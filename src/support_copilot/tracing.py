"""Optional metadata-only spans. Never send prompts, tool results or credentials."""


class TraceRecorder:
    def __init__(self, client=None):
        self.client = client
        self.trace_url = None

    def call(self, name, operation):
        manager = span = None
        if self.client:
            try:
                manager = self.client.start_as_current_observation(name=name, as_type="span")
                span = manager.__enter__()
            except Exception:
                manager = None
        error = None
        try:
            result = operation()
        except BaseException as exc:
            # Never pass raw exceptions to the SDK context manager.
            error = exc
            result = {}
        if span:
            try:
                paused = error is not None and type(error).__name__ == "GraphInterrupt"
                paused = paused or bool(result.get("__interrupt__"))
                status = "paused" if paused else "error" if error else result.get("status", "ok")
                span.update(
                    output={"status": status, "reason": result.get("reason")},
                    level="ERROR" if status == "escalate" or error and not paused else "DEFAULT",
                    status_message=result.get("reason"),
                )
                if name == "support-agent-run":
                    self.trace_url = self.client.get_trace_url()
            except Exception:
                pass
        if manager:
            try:
                manager.__exit__(None, None, None)
            except Exception:
                pass
        if error is not None:
            raise error
        return result

    def flush(self):
        if self.client:
            try:
                self.client.flush()
            except Exception:
                pass
