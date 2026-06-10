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
