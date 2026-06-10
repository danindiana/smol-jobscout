"""Load + validate config.yaml, overlaid with environment / .env.

Exposes a typed pydantic ``Settings`` object via ``load_settings()`` (explicit path)
or ``get_settings()`` (cached singleton used by tools/agent at runtime).
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Literal

import yaml
from dotenv import load_dotenv
from pydantic import BaseModel, Field, field_validator

log = logging.getLogger("smol_jobscout.config")

# Repo root = two levels up from this file's package dir (src/smol_jobscout/ -> repo/)
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = REPO_ROOT / "config.yaml"


class ModelSettings(BaseModel):
    backend: Literal["ollama", "transformers", "inference_api"] = "ollama"
    model_id: str = "qwen2.5-coder:14b"
    api_base: str = "http://localhost:11434"
    num_ctx: int = 8192
    temperature: float = 0.2
    max_tokens: int = 4096

    @field_validator("num_ctx")
    @classmethod
    def _warn_small_ctx(cls, v: int) -> int:
        # The #1 silent-failure cause for Ollama agents (default is 2048).
        if v < 4096:
            log.warning(
                "num_ctx=%d is below 4096; agent runs may fail silently. "
                "Recommend >= 8192 for the Ollama path.",
                v,
            )
        return v


class AgentSettings(BaseModel):
    max_steps: int = 8
    verbosity_level: int = 1
    planning_interval: int | None = 3
    additional_authorized_imports: list[str] = Field(
        default_factory=lambda: ["json", "re", "statistics", "datetime"]
    )
    enable_web_tools: bool = True


class DataSettings(BaseModel):
    path: str = "data/sample_jobs.jsonl"
    format: Literal["jsonl", "sqlite"] = "jsonl"
    sqlite_table: str = "jobs"

    def resolved_path(self) -> Path:
        p = Path(self.path)
        return p if p.is_absolute() else (REPO_ROOT / p)


class ObsSettings(BaseModel):
    log_level: str = "INFO"
    metrics_port: int | None = None


class Settings(BaseModel):
    model: ModelSettings = Field(default_factory=ModelSettings)
    agent: AgentSettings = Field(default_factory=AgentSettings)
    data: DataSettings = Field(default_factory=DataSettings)
    obs: ObsSettings = Field(default_factory=ObsSettings)


def load_settings(config_path: str | os.PathLike[str] | None = None) -> Settings:
    """Load config.yaml, overlay environment variables, validate, and fail fast."""
    load_dotenv(REPO_ROOT / ".env", override=False)

    path = Path(config_path) if config_path else DEFAULT_CONFIG_PATH
    raw: dict = {}
    if path.exists():
        raw = yaml.safe_load(path.read_text()) or {}
    else:
        log.warning("config file %s not found; using built-in defaults", path)

    # Environment overlay (only OLLAMA_API_BASE is wired by default).
    api_base = os.getenv("OLLAMA_API_BASE")
    if api_base:
        raw.setdefault("model", {})["api_base"] = api_base

    settings = Settings(**raw)

    # Fail fast if the configured corpus is missing.
    data_path = settings.data.resolved_path()
    if not data_path.exists():
        raise FileNotFoundError(
            f"data.path does not exist: {data_path}. "
            "Point config.yaml:data.path at a JSONL/SQLite corpus, or use the bundled "
            "data/sample_jobs.jsonl."
        )
    return settings


_SETTINGS: Settings | None = None


def get_settings() -> Settings:
    """Cached settings singleton for runtime callers (tools, agent)."""
    global _SETTINGS
    if _SETTINGS is None:
        _SETTINGS = load_settings()
    return _SETTINGS


def set_settings(settings: Settings) -> None:
    """Override the cached singleton (used by the CLI when flags override config)."""
    global _SETTINGS
    _SETTINGS = settings
