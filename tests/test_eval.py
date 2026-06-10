"""Deterministic checks on the eval harness definition (no model)."""

import importlib.util
from pathlib import Path

EVAL = Path(__file__).resolve().parents[1] / "scripts" / "eval.py"


def _load_eval_module():
    spec = importlib.util.spec_from_file_location("jobscout_eval", EVAL)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_cases_well_formed():
    mod = _load_eval_module()
    assert mod.CASES, "eval CASES must be non-empty"
    for case in mod.CASES:
        assert isinstance(case, tuple) and len(case) == 2
        question, expect = case
        assert isinstance(question, str) and question.strip()
        assert isinstance(expect, str) and expect.strip()
        # expected substring is matched case-insensitively in eval.py
        assert expect == expect.lower(), "expected substrings should be lowercase"
