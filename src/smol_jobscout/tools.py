"""@tool functions exposed to the CodeAgent.

The docstrings and type hints are NOT optional: the model reads them to decide
when and how to call each tool. Keep them explicit.
"""

from __future__ import annotations

from smolagents import tool

from .config import get_settings
from .data import load_jobs, search_jobs, to_brief

_JOBS = None


def _jobs():
    global _JOBS
    if _JOBS is None:
        s = get_settings()
        _JOBS = load_jobs(s.data.resolved_path(), s.data.format, s.data.sqlite_table)
    return _JOBS


def reset_jobs_cache() -> None:
    """Drop the in-process corpus cache (used by tests that swap config)."""
    global _JOBS
    _JOBS = None


@tool
def query_jobs(keyword: str = "", remote_only: bool = False, limit: int = 10) -> str:
    """Search the local job-posting corpus and return compact briefs.

    Args:
        keyword: Case-insensitive term to match in title, company, tags, or description
            (e.g. "parquet", "python", "data engineer"). Empty string matches all.
        remote_only: If true, return only postings flagged remote.
        limit: Maximum number of postings to return (1-25).

    Returns a text block whose first line states the match count as "count=N";
    read that number directly rather than counting lines or string length.
    """
    hits = search_jobs(_jobs(), query=keyword or None, remote=remote_only or None, limit=limit)
    if not hits:
        return "No matching postings found. (count=0)"
    # Lead with an explicit count so the agent never has to infer it from len(string).
    header = f"Found {len(hits)} matching posting(s) (count={len(hits)}):"
    body = "\n\n".join(f"[{j.id}] {to_brief(j)}" for j in hits)
    return f"{header}\n\n{body}"


@tool
def get_job(job_id: str) -> str:
    """Return the full text of a single posting by its id (as shown in query_jobs output).

    Args:
        job_id: The bracketed id from query_jobs output, e.g. "a1b2c3d4e5f6".
    """
    for j in _jobs():
        if j.id == job_id:
            return f"{j.title} @ {j.company}\n{j.url}\n\n{j.text}"
    return f"No posting with id {job_id}."


def build_web_tools() -> list:
    """Return smolagents' built-in web tools, import-guarded across versions."""
    tools: list = []
    try:
        from smolagents import WebSearchTool

        tools.append(WebSearchTool())
    except ImportError:
        try:
            from smolagents import DuckDuckGoSearchTool  # older name

            tools.append(DuckDuckGoSearchTool())
        except ImportError:
            pass
    try:
        from smolagents import VisitWebpageTool

        tools.append(VisitWebpageTool())
    except ImportError:
        pass
    return tools
