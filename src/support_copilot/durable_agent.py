"""Trusted local runner: SQLite checkpoints and authoritative Postgres approvals."""

from contextlib import contextmanager
from pathlib import Path
from uuid import uuid4

from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.types import Command
from psycopg.conninfo import make_conninfo

from support_copilot.agent_graph import build_graph
from support_copilot.agent_loop import Limits
from support_copilot.approvals import ApprovalDenied, ApprovalStore
from support_copilot.database import connect
from support_copilot.policy import PolicyContext
from support_copilot.tracing import TraceRecorder


class Workflow:
    def __init__(self, settings, actor, run_id):
        self.settings, self.actor, self.run_id = settings, actor, run_id

    def request(self, state):
        with connect(self.settings) as conn:
            return ApprovalStore(conn).request(
                self.actor,
                self.run_id,
                state["intake"]["order_id"],
                state["intake"]["amount_cents"],
            )

    def decision(self):
        with connect(self.settings) as conn:
            return ApprovalStore(conn).get(self.actor, self.run_id)

    def execute(self):
        with connect(self.settings) as conn:
            return ApprovalStore(conn).execute(self.actor, self.run_id)


class DurableAgent:
    def __init__(
        self,
        settings,
        model,
        tools,
        checkpoint: Path,
        tracer=None,
        *,
        checkpoint_backend="sqlite",
        executor=None,
    ):
        self.settings, self.model, self.tools = settings, model, tools
        self.checkpoint = checkpoint
        self.tracer = tracer or TraceRecorder()
        if checkpoint_backend not in {"sqlite", "postgres"}:
            raise ValueError("Unknown checkpoint backend")
        self.checkpoint_backend, self.executor = checkpoint_backend, executor

    @contextmanager
    def saver(self):
        if self.checkpoint_backend == "postgres":
            dsn = make_conninfo(self.settings.database_url, connect_timeout=5)
            with PostgresSaver.from_conn_string(dsn) as saver:
                yield saver
        else:
            self.checkpoint.parent.mkdir(parents=True, exist_ok=True)
            with SqliteSaver.from_conn_string(str(self.checkpoint)) as saver:
                yield saver

    def start(self, ticket_id):
        run_id = str(uuid4())
        with connect(self.settings) as conn:
            ticket = ApprovalStore(conn).create_run(self.tools.principal, run_id, ticket_id)
        initial = {
            "ticket": ticket["text"],
            "tenant_id": self.tools.principal.tenant_id,
            "kb_chunks": [],
            "order": None,
            "steps": 0,
            "tool_calls": 0,
            "events": [],
            "reply": "",
            "citations": [],
            "selected_order": None,
            "approval": None,
            "refund_executed": False,
        }
        return self._invoke(run_id, initial)

    def resume(self, run_id):
        # Only a stored operator decision wakes a paused approval. There is no
        # public resume-value/approved flag and no model-controlled run identity.
        with connect(self.settings) as conn:
            store = ApprovalStore(conn)
            store.owned_run(self.tools.principal, run_id)
            decision = store.get(self.tools.principal, run_id)
            if decision["decision"] == "pending":
                raise ApprovalDenied("Human decision is still pending")
        return self._invoke(run_id, None, resume=True)

    def status(self, run_id):
        with connect(self.settings) as conn:
            store = ApprovalStore(conn)
            store.owned_run(self.tools.principal, run_id)
            pending = conn.execute(
                "SELECT decision FROM refund_approvals WHERE tenant_id=%s AND run_id=%s",
                (self.tools.principal.tenant_id, run_id),
            ).fetchone()
        with self.saver() as saver:
            snapshot = saver.get_tuple(
                {"configurable": {"thread_id": self.tools.principal.tenant_id + ":" + run_id}}
            )
        if not snapshot:
            return {"run_id": run_id, "status": "starting", "refund_executed": False}
        state = dict(snapshot.checkpoint["channel_values"])
        if not state.get("status") and pending:
            state["__interrupt__"] = True
        return self.summary(run_id, state)

    def _invoke(self, run_id, initial, resume=False):
        # Serialize same-run resumes across processes without relying on RAM locks.
        with connect(self.settings) as lock_conn:
            locked = lock_conn.execute(
                "SELECT pg_try_advisory_xact_lock(hashtextextended(%s,0)) AS locked",
                (self.tools.principal.tenant_id + ":" + run_id,),
            ).fetchone()["locked"]
            if not locked:
                raise ApprovalDenied("Run is busy")
            return self._invoke_locked(run_id, initial, resume)

    def _invoke_locked(self, run_id, initial, resume=False):
        with connect(self.settings) as conn:
            store = ApprovalStore(conn)
            actor = store.active(self.tools.principal, {"agent:run"})
            run = store.owned_run(actor, run_id)
        workflow = Workflow(self.settings, actor, run_id)
        if self.executor is not None:
            workflow.execute = lambda: self.executor(run_id)
        context = PolicyContext(
            tenant_id=actor.tenant_id, customer_id=run["customer_id"], scopes=actor.scopes
        )
        # Single trusted local operator process at a time. Postgres row locks and
        # unique ledger constraints still protect execution against duplicate retries.
        with self.saver() as saver:
            graph = build_graph(
                self.model,
                self.tools,
                context,
                Limits(max_steps=12),
                checkpointer=saver,
                workflow=workflow,
                tracer=self.tracer,
            )
            config = {
                "configurable": {"thread_id": actor.tenant_id + ":" + run_id},
                "recursion_limit": 20,
            }
            if resume:
                snapshot = graph.get_state(config)
                if not snapshot.values or snapshot.values.get("tenant_id") != actor.tenant_id:
                    raise ApprovalDenied("Checkpoint not found")
                if not snapshot.next:
                    return self.summary(run_id, snapshot.values)
                initial = Command(resume="stored_decision") if snapshot.interrupts else None
            state = self.tracer.call("support-agent-run", lambda: graph.invoke(initial, config))
        self.tracer.flush()
        result = self.summary(run_id, state)
        if self.tracer.trace_url:
            result["trace_url"] = self.tracer.trace_url
        return result

    @staticmethod
    def summary(run_id, state):
        paused = bool(state.get("__interrupt__"))
        return {
            "run_id": run_id,
            "status": "needs_approval" if paused else state.get("status", "incomplete"),
            "reason": "durable_interrupt" if paused else state.get("reason"),
            "refund_executed": state.get("refund_executed", False),
            "reply": state.get("reply", ""),
            "events": state.get("events", []),
            "approval_durable": paused or bool((state.get("approval") or {}).get("durable")),
            "diagnostic": state.get("diagnostic", {}),
        }


def setup_postgres_checkpoints(settings):
    with PostgresSaver.from_conn_string(
        make_conninfo(settings.database_url, connect_timeout=5)
    ) as saver:
        saver.setup()
