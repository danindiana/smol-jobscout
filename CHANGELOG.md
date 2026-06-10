# Changelog

All notable changes to this project are documented here.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Per-step structured logging and Prometheus tool-call metrics, wired into the agent via
  smolagents `step_callbacks` (`obs.make_step_callback`).
- Tier-1 tests for `scripts/eval.py` and `scripts/ingest_crawler.py`.
- `.dockerignore`, `.editorconfig`, `CONTRIBUTING.md`, `CHANGELOG.md`, and a `py.typed` marker.
- `make diagrams` target; Graphviz diagrams (architecture, how-it-works, lessons-learned, howto,
  future-directions) as `.dot` sources rendered to `.svg`/`.png`.

## [0.1.0] - 2026-06-10

### Added
- Local-first smolagents `CodeAgent` answering NL questions over a job-posting corpus via Ollama
  (LiteLLM `ollama_chat/` backend), with import-guarded web tools.
- Deterministic data layer (`load_jobs`, `search_jobs`, `to_brief`) for JSONL and SQLite corpora.
- `query_jobs` / `get_job` tools; CLI (`jobscout`) and optional Gradio UI.
- Pydantic-validated config (`config.yaml` + `.env`); `num_ctx` guard.
- Tier-1 unit tests + Tier-2 integration smoke test; `scripts/eval.py` harness.
- systemd unit + Dockerfile; GitHub Actions CI (lint + Tier-1); verbose README with badges.

[Unreleased]: https://github.com/danindiana/smol-jobscout/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/danindiana/smol-jobscout/releases/tag/v0.1.0
