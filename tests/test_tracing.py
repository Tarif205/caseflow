from contextlib import contextmanager

import pytest

from caseflow.tracing import TraceRecorder


class Client:
    def __init__(self):
        self.outputs = []

    @contextmanager
    def start_as_current_observation(self, **kwargs):
        # No raw inputs are passed to Langfuse.
        assert set(kwargs) == {"name", "as_type"}
        yield self

    def update(self, **kwargs):
        self.outputs.append(kwargs)

    def get_trace_url(self):
        return "https://example.test/trace"


def test_only_safe_status_and_reason_are_exported():
    client = Client()
    result = TraceRecorder(client).call(
        "node",
        lambda: {
            "status": "escalate",
            "reason": "model_unavailable",
            "ticket": "private",
            "reply": "private",
        },
    )
    assert result["ticket"] == "private"
    assert client.outputs[0]["output"] == {"status": "escalate", "reason": "model_unavailable"}
    assert client.outputs[0]["level"] == "ERROR"


def test_raw_exception_is_not_captured_by_sdk():
    client = Client()

    def broken():
        raise RuntimeError("SECRET")

    with pytest.raises(RuntimeError, match="SECRET"):
        TraceRecorder(client).call("node", broken)
    assert "SECRET" not in str(client.outputs)


def test_telemetry_failure_never_replays_or_prevents_operation():
    class BrokenClient:
        def start_as_current_observation(self, **kwargs):
            raise RuntimeError("offline")

    calls = []
    result = TraceRecorder(BrokenClient()).call("node", lambda: calls.append(1) or {"status": "ok"})
    assert result == {"status": "ok"} and calls == [1]
