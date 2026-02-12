"""Provider registry — maps provider names to classes and resolves config."""

from __future__ import annotations

import os

from wip.llm.base import LLMProvider, LLMError

# Provider name -> (class import path, default env var for API key)
PROVIDERS: dict[str, tuple[str, str]] = {
    "anthropic": ("wip.llm.anthropic.AnthropicProvider", "ANTHROPIC_API_KEY"),
    "openai": ("wip.llm.openai.OpenAIProvider", "OPENAI_API_KEY"),
    "gemini": ("wip.llm.gemini.GeminiProvider", "GEMINI_API_KEY"),
}


def list_providers() -> list[str]:
    """Return available provider names."""
    return list(PROVIDERS.keys())


def get_provider(
    provider_name: str,
    api_key: str = "",
    model: str = "",
) -> LLMProvider:
    """Instantiate a provider by name.

    API key resolution order:
      1. Explicit `api_key` argument
      2. Environment variable (provider-specific, e.g. ANTHROPIC_API_KEY)
      3. WIP_LLM_API_KEY (generic fallback env var)

    Raises:
        LLMError: If provider is unknown or no API key found.
    """
    if provider_name not in PROVIDERS:
        available = ", ".join(PROVIDERS.keys())
        raise LLMError(f"Unknown provider '{provider_name}'. Available: {available}")

    class_path, env_var = PROVIDERS[provider_name]

    # Resolve API key
    resolved_key = (
        api_key
        or os.environ.get(env_var, "")
        or os.environ.get("WIP_LLM_API_KEY", "")
    )
    if not resolved_key:
        raise LLMError(
            f"No API key found for '{provider_name}'. "
            f"Set {env_var} environment variable or configure via `wip config init`."
        )

    # Lazy import the provider class
    cls = _import_class(class_path)
    return cls(api_key=resolved_key, model=model)


def _import_class(dotted_path: str) -> type:
    """Import a class from a dotted module path like 'wip.llm.anthropic.AnthropicProvider'."""
    module_path, class_name = dotted_path.rsplit(".", 1)
    import importlib
    module = importlib.import_module(module_path)
    return getattr(module, class_name)
