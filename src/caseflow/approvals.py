"""Tenant-bound authority ledger and transactional, idempotent fictional refunds."""

import hashlib
import json
from uuid import UUID

from caseflow.auth import Principal
from caseflow.mock_backend import MockStore
from caseflow.policy import ActionProposal, PolicyContext, PolicyOrder, policy_check


class ApprovalDenied(RuntimeError):
    pass


def order_value(tenant, raw):
    return PolicyOrder(
        tenant_id=tenant, **{k: raw[k] for k in PolicyOrder.model_fields if k != "tenant_id"}
    )


def digest(order):
    return hashlib.sha256(json.dumps(order.model_dump(), sort_keys=True).encode()).hexdigest()


class ApprovalStore:
    def __init__(self, conn):
        self.conn = conn

    def active(self, actor: Principal, required):
        row = self.conn.execute(
            """SELECT tenant_id, scopes FROM api_tokens WHERE token_hash=%s
               AND revoked_at IS NULL AND (expires_at IS NULL OR expires_at>now())""",
            (actor.token_hash,),
        ).fetchone()
        if (
            not row
            or row["tenant_id"] != actor.tenant_id
            or not set(required) <= set(row["scopes"])
        ):
            raise ApprovalDenied("Insufficient authority")
        return Principal(row["tenant_id"], frozenset(row["scopes"]), actor.token_hash)

    def create_run(self, actor, run_id, ticket_id):
        actor = self.active(actor, {"agent:run", "tickets:read"})
        if str(UUID(run_id)) != run_id:
            raise ValueError("Use a canonical UUID run id")
        ticket = self.conn.execute(
            "SELECT customer_id, text FROM tickets WHERE tenant_id=%s AND id=%s AND status='open'",
            (actor.tenant_id, ticket_id),
        ).fetchone()
        if not ticket:
            raise ApprovalDenied("Record not found")
        self.conn.execute(
            """INSERT INTO agent_runs (tenant_id,id,ticket_id,customer_id,requester_hash)
               VALUES (%s,%s,%s,%s,%s)""",
            (actor.tenant_id, run_id, ticket_id, ticket["customer_id"], actor.token_hash),
        )
        return ticket

    def owned_run(self, actor, run_id):
        actor = self.active(actor, {"agent:run"})
        row = self.conn.execute(
            "SELECT * FROM agent_runs WHERE tenant_id=%s AND id=%s AND requester_hash=%s",
            (actor.tenant_id, run_id, actor.token_hash),
        ).fetchone()
        if not row:
            raise ApprovalDenied("Record not found")
        return row

    def request(self, actor, run_id, order_id, amount):
        actor = self.active(actor, {"agent:run", "refunds:propose"})
        run = self.owned_run(actor, run_id)
        raw = MockStore(self.conn).get_order(actor.tenant_id, order_id)
        order = order_value(actor.tenant_id, raw) if raw else None
        decision = policy_check(
            ActionProposal(action="refund", order_id=order_id, amount_cents=amount),
            PolicyContext(
                tenant_id=actor.tenant_id, customer_id=run["customer_id"], scopes=actor.scopes
            ),
            order,
        )
        if decision.outcome != "needs_approval":
            raise ApprovalDenied("Refund policy denied")
        fingerprint = digest(order)
        self.conn.execute(
            """INSERT INTO refund_approvals (tenant_id,run_id,order_id,amount_cents,order_digest)
               VALUES (%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING""",
            (actor.tenant_id, run_id, order_id, amount, fingerprint),
        )
        row = self.get(actor, run_id)
        if (row["order_id"], row["amount_cents"], row["order_digest"]) != (
            order_id,
            amount,
            fingerprint,
        ):
            raise ApprovalDenied("Approval proposal changed")
        return row

    def get(self, actor, run_id):
        self.owned_run(actor, run_id)
        row = self.conn.execute(
            "SELECT * FROM refund_approvals WHERE tenant_id=%s AND run_id=%s",
            (actor.tenant_id, run_id),
        ).fetchone()
        if not row:
            raise ApprovalDenied("Approval not found")
        return row

    def pending(self, actor):
        self.active(actor, {"refund:approve"})
        return self.conn.execute(
            """SELECT run_id, order_id, amount_cents, created_at FROM refund_approvals
               WHERE tenant_id=%s AND decision='pending' ORDER BY created_at LIMIT 100""",
            (actor.tenant_id,),
        ).fetchall()

    def decide(self, actor, run_id, approve: bool):
        self.active(actor, {"refund:approve"})
        if type(approve) is not bool:
            raise ValueError("Decision must be boolean")
        row = self.conn.execute(
            """SELECT a.decision,r.requester_hash FROM refund_approvals a JOIN agent_runs r
               ON (a.tenant_id,a.run_id)=(r.tenant_id,r.id)
               WHERE a.tenant_id=%s AND a.run_id=%s FOR UPDATE OF a""",
            (actor.tenant_id, run_id),
        ).fetchone()
        if not row or row["requester_hash"] == actor.token_hash or row["decision"] != "pending":
            raise ApprovalDenied("Approval cannot be decided")
        self.conn.execute(
            """UPDATE refund_approvals SET decision=%s,decided_by=%s,decided_at=now()
               WHERE tenant_id=%s AND run_id=%s""",
            ("approved" if approve else "rejected", actor.token_hash, actor.tenant_id, run_id),
        )

    def execute(self, actor, run_id):
        actor = self.active(actor, {"agent:run", "refunds:propose", "refunds:execute"})
        run = self.owned_run(actor, run_id)
        approval = self.conn.execute(
            "SELECT * FROM refund_approvals WHERE tenant_id=%s AND run_id=%s FOR UPDATE",
            (actor.tenant_id, run_id),
        ).fetchone()
        if (
            not approval
            or approval["decision"] != "approved"
            or approval["decided_by"] == actor.token_hash
        ):
            raise ApprovalDenied("Human approval required")
        self.active(
            Principal(actor.tenant_id, frozenset(), approval["decided_by"]), {"refund:approve"}
        )
        existing = self.conn.execute(
            "SELECT order_id,amount_cents FROM refunds WHERE tenant_id=%s AND run_id=%s",
            (actor.tenant_id, run_id),
        ).fetchone()
        if existing:
            return existing
        raw = self.conn.execute(
            "SELECT * FROM orders WHERE tenant_id=%s AND id=%s FOR UPDATE",
            (actor.tenant_id, approval["order_id"]),
        ).fetchone()
        order = order_value(actor.tenant_id, raw) if raw else None
        proposal = ActionProposal(
            action="refund", order_id=approval["order_id"], amount_cents=approval["amount_cents"]
        )
        context = PolicyContext(
            tenant_id=actor.tenant_id, customer_id=run["customer_id"], scopes=actor.scopes
        )
        if (
            policy_check(proposal, context, order).outcome != "needs_approval"
            or digest(order) != approval["order_digest"]
        ):
            raise ApprovalDenied("Order or policy changed after approval")
        self.conn.execute(
            """INSERT INTO refunds (tenant_id,run_id,order_id,amount_cents,approved_by)
               VALUES (%s,%s,%s,%s,%s)""",
            (actor.tenant_id, run_id, order.id, proposal.amount_cents, approval["decided_by"]),
        )
        self.conn.execute(
            "UPDATE orders SET status='refunded' WHERE tenant_id=%s AND id=%s",
            (actor.tenant_id, order.id),
        )
        return {"order_id": order.id, "amount_cents": proposal.amount_cents}
