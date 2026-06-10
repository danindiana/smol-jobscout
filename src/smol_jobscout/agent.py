"""Assemble the CodeAgent.

SECURITY NOTE: CodeAgent executes Python that the LLM writes, in-process, on the
host. With a local model and a tight `additional_authorized_imports` allowlist the
risk is bounded — but NEVER expose this agent to untrusted input over a network
without sandboxing. For any shared/remote deployment, switch `executor_type` to a
sandboxed runner (e.g. Docker/E2B) and keep the import allowlist minimal.
"""

from __future__ import annotations

import logging

from smolagents import CodeAgent

from .config import get_settings
from .model import build_model
from .obs import make_step_callback
from .tools import build_web_tools, get_job, query_jobs

log = logging.getLogger("smol_jobscout.agent")


def build_agent():
    s = get_settings()
    model = build_model(s)
    tools = [query_jobs, get_job]
    if s.agent.enable_web_tools:
        web = build_web_tools()
        if web:
            tools += web
        else:
            log.warning("web tools requested but unavailable in this smolagents build; "
                        "continuing local-only")
    return CodeAgent(
        tools=tools,
        model=model,
        add_base_tools=False,                # we add only what we need
        additional_authorized_imports=s.agent.additional_authorized_imports,
        max_steps=s.agent.max_steps,
        verbosity_level=s.agent.verbosity_level,
        planning_interval=s.agent.planning_interval,
        executor_type="local",               # SEE SECURITY NOTE above
        step_callbacks=[make_step_callback(log)],  # one log line + metrics per step
    )
