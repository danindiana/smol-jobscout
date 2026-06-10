from pathlib import Path

from smol_jobscout.data import Job, load_jobs, search_jobs, to_brief

DATA = Path(__file__).resolve().parents[1] / "data" / "sample_jobs.jsonl"


def test_load_normalizes_schema():
    jobs = load_jobs(DATA, "jsonl")
    assert len(jobs) == 15
    for j in jobs:
        assert isinstance(j, Job)
        assert j.id  # stable id assigned
        assert isinstance(j.remote, bool)
        assert isinstance(j.tags, list)


def test_tags_extracted():
    jobs = load_jobs(DATA, "jsonl")
    parqion = next(j for j in jobs if j.company == "Parqion")
    assert "parquet" in parqion.tags
    assert "python" in parqion.tags


def test_search_keyword_filter():
    jobs = load_jobs(DATA, "jsonl")
    hits = search_jobs(jobs, query="parquet")
    assert hits, "expected parquet matches"
    assert all("parquet" in (" ".join(j.tags) + j.text).lower() for j in hits)


def test_search_remote_filter():
    jobs = load_jobs(DATA, "jsonl")
    remote = search_jobs(jobs, remote=True, limit=25)
    assert remote
    assert all(j.remote for j in remote)


def test_search_limit_clamped():
    jobs = load_jobs(DATA, "jsonl")
    assert len(search_jobs(jobs, limit=999)) <= 25
    assert len(search_jobs(jobs, limit=0)) >= 1  # clamped up to 1 minimum behaviour


def test_to_brief_length_bound():
    jobs = load_jobs(DATA, "jsonl")
    long = max(jobs, key=lambda j: len(j.text))
    brief = to_brief(long, max_desc=240)
    # description portion is truncated; brief stays compact relative to full text
    assert "…" in brief or len(long.text) <= 240
