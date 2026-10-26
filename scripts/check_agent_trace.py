"""Send a deliberate fake-model failure, then verify only redacted node metadata."""

import json
import time

from dotenv import load_dotenv
from langfuse import get_client

from support_copilot.agent_graph import build_graph
from support_copilot.agent_loop import Limits
from support_copilot.auth import Principal
from support_copilot.chat import ModelUnavailable
from support_copilot.config import PROJECT_ROOT
from support_copilot.policy import PolicyContext
from support_copilot.tracing import TraceRecorder


class FailedModel:
    def complete_json(self, *args):
        raise ModelUnavailable("deliberate test failure; do not export this raw exception")


class NoTools:
    principal = Principal("trace-test", frozenset({"agent:run"}), "not-a-real-token")


def main():
    load_dotenv(PROJECT_ROOT / ".env", override=False)
    client = get_client()
    if not client.auth_check():
        raise SystemExit("Langfuse authentication failed; credentials withheld")
    recorder = TraceRecorder(client)
    graph = build_graph(
        FailedModel(),
        NoTools(),
        PolicyContext(tenant_id="trace-test", scopes=frozenset({"agent:run"})),
        Limits(),
        tracer=recorder,
    )
    result = recorder.call(
        "support-agent-run",
        lambda: graph.invoke(
            {
                "ticket": "Synthetic failure test; no customer data",
                "tenant_id": "trace-test",
                "steps": 0,
                "tool_calls": 0,
                "events": [],
            }
        ),
    )
    recorder.flush()
    assert result["reason"] == "model_unavailable"
    trace_id = recorder.trace_url.rstrip("/").split("/")[-1]
    observations = []
    for _ in range(5):
        response = client.api.observations.get_many(
            trace_id=trace_id, fields="core,basic,io", limit=100
        )
        observations = response.data
        if any(o.name == "intake" for o in observations):
            break
        time.sleep(3)
    intake = next(o for o in observations if o.name == "intake")
    assert intake.level == "ERROR" and intake.status_message == "model_unavailable"
    for observation in observations:
        assert not observation.input
        output = observation.output
        if isinstance(output, str):
            output = json.loads(output)
        assert set(output or {}) <= {"status", "reason"}
    report = {
        "trace_url": recorder.trace_url,
        "trace_id": trace_id,
        "delivery_verified_by_read_api": True,
        "failed_node": intake.name,
        "safe_reason": intake.status_message,
        "metadata_only": True,
        "kind": "deliberate fake-model failure, not a real provider diagnostic",
        "observations": [{"name": o.name, "level": o.level} for o in observations],
    }
    path = PROJECT_ROOT / "evals/results/day-09-failed-trace.json"
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        raise SystemExit(
            f"Trace verification failed ({type(exc).__name__}); raw details withheld"
        ) from None
