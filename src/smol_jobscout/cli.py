"""`jobscout "question"` entry point.

Final answer -> stdout (pipeable). Step/tool traces -> stderr.
"""

from __future__ import annotations

import argparse
import sys
import time

from .config import load_settings, set_settings
from .obs import init_metrics, setup_logging


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="jobscout", description=__doc__)
    p.add_argument("question", nargs="?", help="natural-language question over the job corpus")
    p.add_argument("--config", help="path to config.yaml")
    p.add_argument("--backend", choices=["ollama", "transformers", "inference_api"])
    p.add_argument("--model", help="override model_id (e.g. qwen2.5-coder:7b)")
    p.add_argument("--data", help="override data.path")
    p.add_argument("--once", action="store_true", default=True,
                   help="single shot: print final answer and exit (default)")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    if not args.question:
        print("usage: jobscout \"your question\"", file=sys.stderr)
        return 2

    settings = load_settings(args.config)
    if args.backend:
        settings.model.backend = args.backend
    if args.model:
        settings.model.model_id = args.model
    if args.data:
        settings.data.path = args.data
    set_settings(settings)

    setup_logging(settings.obs.log_level)
    m = init_metrics(settings.obs.metrics_port)

    # Import after set_settings so the agent/tools see the overridden config.
    from .agent import build_agent

    agent = build_agent()
    start = time.perf_counter()
    try:
        answer = agent.run(args.question)
        if m:
            m.runs.inc()
            m.latency.observe(time.perf_counter() - start)
            # per-step counts (jobscout_steps, jobscout_tool_calls_total) are
            # incremented in the agent's step callback (obs.make_step_callback).
    except Exception:
        if m:
            m.errors.inc()
        raise

    print(answer)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
