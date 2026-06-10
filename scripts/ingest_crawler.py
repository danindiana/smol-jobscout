#!/usr/bin/env python3
"""Convert the user's real crawler output into the canonical jobs corpus.

No real crawler sample was provided at build time, so this script documents and
implements the EXPECTED input shape. Adjust ``map_record`` to your crawler.

Expected crawler input (JSON array OR JSONL), per record — any subset of:
    {
      "title": str, "company": str, "location": str,
      "remote": bool|str, "url": str, "posted_at": str (ISO date),
      "salary": str|null,
      "text"|"description": str   # full posting body
    }

Output: JSONL of canonical records (one JSON object per line), ready for
``config.yaml:data.path``. Missing fields are tolerated by data.load_jobs.

Usage:
    python scripts/ingest_crawler.py --input crawler_dump.json --output data/jobs.jsonl
    CRAWLER_INPUT_PATH=... python scripts/ingest_crawler.py --output data/jobs.jsonl
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

# Make the package importable when run from the repo root without install.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from smol_jobscout.data import _normalize  # noqa: E402


def _load_any(path: Path) -> list[dict]:
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        return []
    if text[0] == "[":  # JSON array
        return json.loads(text)
    return [json.loads(line) for line in text.splitlines() if line.strip()]  # JSONL


def map_record(raw: dict) -> dict:
    """Map one crawler record to the canonical schema. Edit for your crawler's keys."""
    job = _normalize(raw)
    return job.model_dump()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input", default=os.getenv("CRAWLER_INPUT_PATH"),
                    help="crawler dump (.json or .jsonl); or set CRAWLER_INPUT_PATH")
    ap.add_argument("--output", default="data/jobs.jsonl")
    args = ap.parse_args()

    if not args.input:
        ap.error("no --input and CRAWLER_INPUT_PATH unset")
    src = Path(args.input)
    if not src.exists():
        ap.error(f"input not found: {src}")

    records = _load_any(src)
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as fh:
        for raw in records:
            fh.write(json.dumps(map_record(raw), ensure_ascii=False) + "\n")
    print(f"wrote {len(records)} records -> {out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
