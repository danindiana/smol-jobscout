import smol_jobscout.tools as tools_mod
from smol_jobscout.config import load_settings, set_settings


def _setup():
    # Bind tools to the bundled sample corpus.
    set_settings(load_settings())
    tools_mod.reset_jobs_cache()


def _call(tool, **kwargs):
    # smolagents @tool wraps the function; the original is callable via forward/__call__.
    fn = getattr(tool, "forward", tool)
    return fn(**kwargs)


def test_query_jobs_returns_briefs_with_ids():
    _setup()
    out = _call(tools_mod.query_jobs, keyword="parquet", limit=5)
    assert "[" in out and "]" in out  # bracketed ids present
    assert "parquet" in out.lower()


def test_query_jobs_reports_count():
    _setup()
    out = _call(tools_mod.query_jobs, keyword="python", limit=25)
    # First line carries an explicit count the agent can read directly.
    assert "count=" in out.splitlines()[0]
    n_ids = sum(1 for ln in out.splitlines() if ln.startswith("["))
    assert f"count={n_ids}" in out.splitlines()[0]


def test_query_jobs_remote_only():
    _setup()
    out = _call(tools_mod.query_jobs, keyword="", remote_only=True, limit=25)
    assert "remote" in out.lower()


def test_query_jobs_empty_result_sentinel():
    _setup()
    out = _call(tools_mod.query_jobs, keyword="cobol-mainframe-zzz", limit=5)
    assert out == "No matching postings found. (count=0)"


def test_get_job_roundtrip():
    _setup()
    jobs = tools_mod._jobs()
    jid = jobs[0].id
    out = _call(tools_mod.get_job, job_id=jid)
    assert jobs[0].title in out
    assert jobs[0].url in out


def test_get_job_missing():
    _setup()
    out = _call(tools_mod.get_job, job_id="deadbeef0000")
    assert out == "No posting with id deadbeef0000."
