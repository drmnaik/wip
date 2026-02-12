"""Base class and types for LLM providers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class LLMResponse:
    text: str
    input_tokens: int = 0
    output_tokens: int = 0
    model: str = ""


class LLMProvider(ABC):
    """Abstract base for LLM providers.

    Each provider must implement `complete()` and `stream()`.
    The constructor receives the API key and model ID.
    """

    name: str = ""

    def __init__(self, api_key: str, model: str) -> None:
        self.api_key = api_key
        self.model = model

    @abstractmethod
    def complete(self, system: str, user: str) -> LLMResponse:
        """Send a message and return the full response.

        Args:
            system: System prompt providing context and instructions.
            user: The user message / query.

        Returns:
            LLMResponse with the generated text and token usage.

        Raises:
            LLMAuthError: If the API key is invalid.
            LLMRateLimitError: If rate limited.
            LLMError: For any other provider error.
        """
        ...

    @abstractmethod
    def stream(self, system: str, user: str):
        """Send a message and yield response text chunks.

        Args:
            system: System prompt providing context and instructions.
            user: The user message / query.

        Yields:
            str: Chunks of the response text as they arrive.

        Raises:
            LLMAuthError: If the API key is invalid.
            LLMRateLimitError: If rate limited.
            LLMError: For any other provider error.
        """
        ...

    def validate_key(self) -> bool:
        """Quick check that the API key works. Override for provider-specific validation."""
        try:
            self.complete(system="Reply with OK.", user="ping")
            return True
        except Exception:
            return False


# --- Errors ---

class LLMError(Exception):
    """Base error for LLM operations."""


class LLMAuthError(LLMError):
    """Invalid or missing API key."""


class LLMRateLimitError(LLMError):
    """Rate limit exceeded."""
