"""Tier-2 integration smoke test. Needs a running Ollama + a pulled model.

Skips (does not fail) when Ollama is unreachable or the configured model is absent.
"""

import urllib.request

import pytest

from smol_jobscout.config import get_settings

pytestmark = pytest.mark.integration


def _ollama_has_model(api_base: str, model_id: str) -> bool:
    try:
        with urllib.request.urlopen(f"{api_base}/api/tags", timeout=3) as resp:
            import json

            tags = json.loads(resp.read())
    except Exception:
        return False
    names = {m.get("name", "") for m in tags.get("models", [])}
    # match exact tag or base name (ollama appends :latest etc.)
    return any(model_id == n or n.startswith(model_id) for n in names)


@pytest.fixture(scope="module")
def agent():
    s = get_settings()
    if not _ollama_has_model(s.model.api_base, s.model.model_id):
        pytest.skip(f"Ollama unreachable or model {s.model.model_id} not pulled")
    from smol_jobscout.agent import build_agent

    return build_agent()


def test_agent_uses_tools_and_answers(agent):
    # Well-formed prompt: a vague "use the tools" phrasing makes small models loop to
    # max_steps without finalizing (see docs/LESSONS_LEARNED.md). Be explicit.
    answer = agent.run(
        "Using the local job postings, call query_jobs once with limit=25 and tell me "
        "how many postings mention Python. Answer with just the number."
    )
    # final_answer preserves the agent's type (here an int 10), so don't assume str.
    assert answer is not None
    assert str(answer).strip()

    steps = getattr(agent.memory, "steps", []) or []
    assert len(steps) <= get_settings().agent.max_steps + 2

    # At least one tool/code action referenced a corpus tool. CodeAgent emits the
    # call inside `code_action`; also scan tool_calls for ToolCallingAgent-style runs.
    blobs = []
    for st in steps:
        blobs.append(str(getattr(st, "code_action", "") or ""))
        blobs.append(str(getattr(st, "tool_calls", "") or ""))
    text = " ".join(blobs).lower()
    assert "query_jobs" in text or "get_job" in text
