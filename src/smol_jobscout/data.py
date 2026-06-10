"""Data layer: normalize crawled postings into a stable schema and query them.

No LLM here — this is the deterministic backbone the agent tools call.
"""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from pathlib import Path

from pydantic import BaseModel, Field

# Best-effort tag vocabulary: languages / tools we try to extract from free text.
_TAG_VOCAB = [
    "python", "rust", "go", "golang", "java", "scala", "c++", "sql", "bash",
    "parquet", "s3", "spark", "kafka", "airflow", "dbt", "snowflake", "postgres",
    "postgresql", "mysql", "duckdb", "pandas", "polars", "kubernetes", "docker",
    "terraform", "aws", "gcp", "azure", "pytorch", "tensorflow", "llm", "etl",
]


class Job(BaseModel):
    id: str
    title: str = ""
    company: str = ""
    location: str = ""
    remote: bool = False
    url: str = ""
    posted_at: str | None = None
    salary: str | None = None
    text: str = ""
    tags: list[str] = Field(default_factory=list)


def _stable_id(url: str, title: str) -> str:
    return hashlib.sha1(f"{url}|{title}".encode()).hexdigest()[:12]


def _extract_tags(text: str, existing: list[str] | None) -> list[str]:
    if existing:
        return sorted({t.lower() for t in existing})
    low = text.lower()
    found = {t for t in _TAG_VOCAB if re.search(rf"\b{re.escape(t)}\b", low)}
    return sorted(found)


def _coerce_remote(raw: dict) -> bool:
    val = raw.get("remote")
    if isinstance(val, bool):
        return val
    if isinstance(val, str):
        return val.strip().lower() in {"true", "yes", "remote", "1"}
    loc = str(raw.get("location", "")).lower()
    return "remote" in loc


def _normalize(raw: dict) -> Job:
    """Build a canonical Job from a tolerant/partial source record."""
    url = str(raw.get("url", "") or "")
    title = str(raw.get("title", "") or "")
    text = str(raw.get("text") or raw.get("description") or "")
    jid = str(raw.get("id") or "") or _stable_id(url, title)
    return Job(
        id=jid,
        title=title,
        company=str(raw.get("company", "") or ""),
        location=str(raw.get("location", "") or ""),
        remote=_coerce_remote(raw),
        url=url,
        posted_at=raw.get("posted_at"),
        salary=raw.get("salary"),
        text=text,
        tags=_extract_tags(text + " " + title, raw.get("tags")),
    )


def load_jobs(path: str | Path, fmt: str = "jsonl", sqlite_table: str = "jobs") -> list[Job]:
    """Read JSONL or a SQLite table into canonical Job records; tolerant of missing fields."""
    path = Path(path)
    if fmt == "jsonl":
        jobs: list[Job] = []
        with path.open(encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                jobs.append(_normalize(json.loads(line)))
        return jobs
    if fmt == "sqlite":
        con = sqlite3.connect(str(path))
        con.row_factory = sqlite3.Row
        try:
            rows = con.execute(f"SELECT * FROM {sqlite_table}").fetchall()  # noqa: S608
        finally:
            con.close()
        return [_normalize(dict(r)) for r in rows]
    raise ValueError(f"unknown data format: {fmt}")


def _matches(job: Job, q: str) -> bool:
    hay = " ".join([job.title, job.company, " ".join(job.tags), job.text]).lower()
    ql = q.lower()
    # Word-boundary match for alphanumeric terms (avoids "rust" matching "trustworthy");
    # fall back to substring for terms with punctuation like "c++".
    if ql.replace(" ", "").isalnum():
        return re.search(rf"\b{re.escape(ql)}\b", hay) is not None
    return ql in hay


def search_jobs(
    jobs: list[Job],
    query: str | None = None,
    remote: bool | None = None,
    must_include: list[str] | None = None,
    limit: int = 20,
) -> list[Job]:
    """Pure-Python keyword/flag filter over the corpus (no LLM)."""
    limit = max(1, min(limit, 25))
    out = jobs
    if remote is not None:
        out = [j for j in out if j.remote == remote]
    if query:
        out = [j for j in out if _matches(j, query)]
    if must_include:
        out = [j for j in out if all(_matches(j, term) for term in must_include)]
    return out[:limit]


def to_brief(job: Job, max_desc: int = 240) -> str:
    """Compact one-paragraph rendering for the model's context. Keep it short for num_ctx."""
    desc = job.text.replace("\n", " ").strip()
    if len(desc) > max_desc:
        desc = desc[:max_desc].rstrip() + "…"
    parts = [
        f"{job.title or '(no title)'} @ {job.company or '(unknown)'}",
        f"location={job.location or 'n/a'}{' [remote]' if job.remote else ''}",
    ]
    if job.salary:
        parts.append(f"salary={job.salary}")
    if job.tags:
        parts.append("tags=" + ",".join(job.tags[:8]))
    parts.append(desc)
    return " | ".join(parts)
