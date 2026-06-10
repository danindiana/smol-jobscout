# Contributing to smol-jobscout

Thanks for your interest! This is a small, focused project — contributions that keep it
**local-first, single-purpose, and honestly documented** are very welcome.

## Development setup

```bash
# Python 3.11+ is required. If your system python3 is older, use python3.12 explicitly.
python3.12 -m venv .venv && source .venv/bin/activate
pip install -U pip && pip install -e ".[dev,ui]"
```

## Before you push

```bash
make lint     # ruff check src tests  — must be clean
make test     # Tier-1 unit tests (no model) — must pass
```

CI (`.github/workflows/ci.yml`) runs lint + Tier-1 on every push/PR with **no model**, so keep
Tier-1 tests deterministic and model-free.

## Tiers of tests

- **Tier-1** (`pytest`) — deterministic, no LLM. Data layer, tools, config, scripts. Runs in CI.
- **Tier-2** (`pytest -m integration`) — builds the real `CodeAgent`; needs Ollama serving on
  `:11434` with the configured model pulled. **Skips cleanly** if Ollama is unreachable. Run it
  locally before changing agent/model/tool wiring:

  ```bash
  ollama pull qwen2.5-coder:14b
  pytest -m integration
  ```

## Conventions

- Lint/format with **ruff** (`line-length = 100`, `py311` target).
- Keep tool docstrings explicit — the model reads them (see `docs/LESSONS_LEARNED.md`).
- The data layer (`data.py`) stays **LLM-free**: deterministic filtering only.
- Update `docs/diagrams/*.dot` and run `make diagrams` if you change the architecture.
- Note user-visible changes in `CHANGELOG.md`.

## Security

`CodeAgent` executes LLM-written Python in-process. Keep `additional_authorized_imports` minimal and
never wire this to untrusted/network input without a sandboxed executor. See the README security note.
