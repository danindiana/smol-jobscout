"""Structured logging + optional Prometheus metrics."""

from __future__ import annotations

import logging

from rich.logging import RichHandler

_PROM = None  # holds the metrics namespace once initialized


def setup_logging(level: str = "INFO") -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=True, show_path=False)],
    )


def log_step(logger: logging.Logger, step_idx: int, tool: str | None,
             tool_args: str | None, duration_ms: float) -> None:
    """One structured log line per agent step."""
    args = (tool_args or "")[:120]
    logger.info("step=%d tool=%s args=%s duration_ms=%.1f",
                step_idx, tool or "-", args, duration_ms)


# Tool names we attribute in metrics when they appear in a CodeAgent's code action.
_KNOWN_TOOLS = ("query_jobs", "get_job", "summarize_url", "web_search",
                "visit_webpage", "final_answer")


def make_step_callback(logger: logging.Logger):
    """Build a smolagents step callback: one log line + metrics per ActionStep.

    smolagents invokes callbacks as ``callback(memory_step, agent=...)``.
    """
    def _cb(memory_step, agent=None):  # noqa: ANN001
        # Only ActionSteps carry tool/code activity; ignore planning/final wrappers.
        code = getattr(memory_step, "code_action", None)
        tool_calls = getattr(memory_step, "tool_calls", None)
        if code is None and not tool_calls:
            return

        idx = int(getattr(memory_step, "step_number", -1) or -1)
        timing = getattr(memory_step, "timing", None)
        duration_ms = float(getattr(timing, "duration", 0.0) or 0.0) * 1000.0

        # Determine which tools fired this step.
        fired: list[str] = []
        if tool_calls:
            for tc in tool_calls:
                name = getattr(tc, "name", None)
                if name:
                    fired.append(name)
        if code:
            fired += [t for t in _KNOWN_TOOLS if t in code]

        label = ",".join(dict.fromkeys(fired)) or ("python" if code else "-")
        args = code if code else str(tool_calls)
        log_step(logger, idx, label, args, duration_ms)

        m = metrics()
        if m:
            m.steps.inc()
            for name in dict.fromkeys(fired):
                if name != "final_answer":
                    m.tool_calls.labels(tool=name).inc()

    return _cb


class _Metrics:
    def __init__(self) -> None:
        from prometheus_client import Counter, Histogram

        self.runs = Counter("jobscout_runs_total", "Total agent runs")
        self.steps = Counter("jobscout_steps", "Total agent steps")
        self.tool_calls = Counter("jobscout_tool_calls_total", "Tool calls", ["tool"])
        self.errors = Counter("jobscout_run_errors_total", "Run errors")
        self.latency = Histogram("jobscout_run_latency_seconds", "Run latency (s)")


def init_metrics(port: int | None):
    """Start a Prometheus exporter if a port is configured; return the metrics handle or None."""
    global _PROM
    if port is None:
        return None
    from prometheus_client import start_http_server

    start_http_server(port)
    _PROM = _Metrics()
    return _PROM


def metrics():
    return _PROM
