"""Optional Gradio chat UI (extras: .[ui]).

SECURITY: this launches a code-executing agent. Do NOT bind to a public interface
without auth + a sandboxed executor (see agent.py security note).
"""

from __future__ import annotations

from smolagents import GradioUI

from .agent import build_agent
from .config import get_settings
from .obs import setup_logging


def main() -> None:
    s = get_settings()
    setup_logging(s.obs.log_level)
    GradioUI(build_agent()).launch(server_name="0.0.0.0", server_port=7860)


if __name__ == "__main__":
    main()
