from __future__ import annotations

from model_adapter.base import ModelAdapter
from model_adapter.mock import MockModelAdapter
from model_adapter.ollama import OllamaModelAdapter


def build_model_adapter(
    *,
    provider: str,
    ollama_base_url: str,
    ollama_model: str,
    ollama_timeout_seconds: float,
) -> ModelAdapter:
    normalized = provider.strip().lower()
    if normalized == "mock":
        return MockModelAdapter()
    if normalized == "ollama":
        return OllamaModelAdapter(
            base_url=ollama_base_url,
            model=ollama_model,
            timeout_seconds=ollama_timeout_seconds,
        )
    raise ValueError(f"Unsupported model provider: {provider}")
