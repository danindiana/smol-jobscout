import logging

import pytest

from smol_jobscout.config import Settings, load_settings


def test_valid_config_loads():
    s = load_settings()
    assert isinstance(s, Settings)
    assert s.model.backend == "ollama"
    assert s.model.num_ctx >= 4096
    assert s.data.resolved_path().exists()


def test_low_num_ctx_warns(caplog):
    with caplog.at_level(logging.WARNING, logger="smol_jobscout.config"):
        Settings(model={"num_ctx": 2048})
    assert any("num_ctx" in r.message for r in caplog.records)


def test_missing_data_path_raises(tmp_path):
    cfg = tmp_path / "config.yaml"
    cfg.write_text(
        "data:\n  path: /nonexistent/does-not-exist.jsonl\n  format: jsonl\n"
    )
    with pytest.raises(FileNotFoundError):
        load_settings(cfg)
