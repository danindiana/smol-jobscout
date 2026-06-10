#!/usr/bin/env python3
"""Tiny eval harness over fixed (question -> expected-substring) pairs.

Runs against the live Ollama model, prints pass/fail + wall-clock latency per
question, and writes a Markdown table to docs/eval_results.md. This is the
artifact that produces real numbers for LESSONS_LEARNED.md.

Usage:
    python scripts/eval.py                 # uses config.yaml model
    python scripts/eval.py --model qwen2.5-coder:7b
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from smol_jobscout.config import load_settings, set_settings  # noqa: E402

# (question, expected lowercase substring in the final answer)
CASES: list[tuple[str, str]] = [
    ("Using the local job postings, how many mention Python? Call query_jobs with "
     "limit=25 and answer with just the count.", "10"),
    ("Using only the local job postings (the query_jobs tool), name one company "
     "hiring for a Rust role.", "ferroline"),
    ("List remote postings that mention Parquet. Give company names.", "parquet"),
    ("What salary range is listed for the Senior Data Engineer at Parqion?", "160"),
]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--model", help="override model_id")
    ap.add_argument("--output", default="docs/eval_results.md")
    args = ap.parse_args()

    s = load_settings()
    if args.model:
        s.model.model_id = args.model
    set_settings(s)

    from smol_jobscout.agent import build_agent

    rows = []
    passed = 0
    for q, expect in CASES:
        agent = build_agent()  # fresh agent per case (clean memory)
        t0 = time.perf_counter()
        ok = False
        answer = ""
        try:
            answer = str(agent.run(q))
            ok = expect.lower() in answer.lower()
        except Exception as e:  # noqa: BLE001
            answer = f"ERROR: {e}"
        dt = time.perf_counter() - t0
        passed += int(ok)
        rows.append((q, expect, ok, dt, answer.replace("\n", " ")[:80]))
        print(f"[{'PASS' if ok else 'FAIL'}] {dt:5.1f}s  {q}", file=sys.stderr)

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        f"# Eval results — `{s.model.model_id}`",
        "",
        f"**{passed}/{len(CASES)} passed.**",
        "",
        "| Question | Expect | Pass | Latency (s) | Answer (truncated) |",
        "|---|---|---|---|---|",
    ]
    for q, expect, ok, dt, ans in rows:
        q_e = q.replace("|", "\\|")
        ans_e = ans.replace("|", "\\|")
        lines.append(f"| {q_e} | `{expect}` | {'✅' if ok else '❌'} | {dt:.1f} | {ans_e} |")
    out.write_text("\n".join(lines) + "\n")
    print(f"\nwrote {out}  ({passed}/{len(CASES)} passed)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
