"""Deterministic checks on scripts/ingest_crawler.py (no model)."""

import importlib.util
from pathlib import Path

INGEST = Path(__file__).resolve().parents[1] / "scripts" / "ingest_crawler.py"


def _load_ingest_module():
    spec = importlib.util.spec_from_file_location("jobscout_ingest", INGEST)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_load_any_handles_json_array(tmp_path):
    mod = _load_ingest_module()
    p = tmp_path / "dump.json"
    p.write_text('[{"title": "A"}, {"title": "B"}]')
    recs = mod._load_any(p)
    assert [r["title"] for r in recs] == ["A", "B"]


def test_load_any_handles_jsonl(tmp_path):
    mod = _load_ingest_module()
    p = tmp_path / "dump.jsonl"
    p.write_text('{"title": "A"}\n\n{"title": "B"}\n')
    recs = mod._load_any(p)
    assert len(recs) == 2


def test_map_record_normalizes_and_tolerates_missing_fields():
    mod = _load_ingest_module()
    out = mod.map_record({"title": "Data Engineer", "description": "Python and Parquet on S3"})
    # canonical schema keys present
    for key in ("id", "title", "company", "location", "remote", "url", "tags", "text"):
        assert key in out
    assert out["title"] == "Data Engineer"
    assert out["id"]  # stable id derived even with no url
    assert "python" in out["tags"] and "parquet" in out["tags"]
    assert out["remote"] is False
