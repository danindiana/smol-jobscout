"""Model factory: ollama (default) | transformers | inference_api.

Only the Ollama-via-LiteLLM path is required to pass smoke tests.
"""

from __future__ import annotations

from .config import Settings


def build_model(s: Settings):
    """Build a smolagents model object from validated Settings."""
    m = s.model
    if m.backend == "ollama":
        from smolagents import LiteLLMModel

        # Ollama is reached through LiteLLM using the `ollama_chat/` prefix
        # (the chat variant handles roles correctly; `ollama/` does not).
        return LiteLLMModel(
            model_id=f"ollama_chat/{m.model_id}",
            api_base=m.api_base,
            api_key="ollama",          # placeholder; Ollama ignores it
            num_ctx=m.num_ctx,         # MUST be raised from the 2048 default
            temperature=m.temperature,
            max_tokens=m.max_tokens,
        )
    if m.backend == "transformers":
        from smolagents import TransformersModel  # requires extras: .[transformers]

        return TransformersModel(
            model_id=m.model_id,       # e.g. "HuggingFaceTB/SmolLM2-1.7B-Instruct"
            device_map="auto",
            max_new_tokens=m.max_tokens,
        )
    if m.backend == "inference_api":
        from smolagents import InferenceClientModel  # HF-hosted; needs HF_TOKEN for limits

        return InferenceClientModel(model_id=m.model_id)
    raise ValueError(f"unknown backend: {m.backend}")
