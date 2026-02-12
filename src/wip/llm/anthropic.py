"""Anthropic (Claude) provider."""

from __future__ import annotations

from wip.llm.base import LLMProvider, LLMResponse, LLMError, LLMAuthError, LLMRateLimitError

DEFAULT_MODEL = "claude-sonnet-4-5-20250929"


class AnthropicProvider(LLMProvider):
    """Anthropic Claude provider.

    Requires: `pip install anthropic`
    API key env var: ANTHROPIC_API_KEY
    """

    name = "anthropic"

    def __init__(self, api_key: str, model: str = "") -> None:
        super().__init__(api_key, model or DEFAULT_MODEL)
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                from anthropic import Anthropic
            except ImportError:
                raise LLMError(
                    "anthropic package not installed. Run: pip install anthropic"
                )
            self._client = Anthropic(api_key=self.api_key)
        return self._client

    def complete(self, system: str, user: str) -> LLMResponse:
        import anthropic

        client = self._get_client()
        try:
            message = client.messages.create(
                model=self.model,
                max_tokens=1024,
                system=system,
                messages=[{"role": "user", "content": user}],
            )
        except anthropic.AuthenticationError as e:
            raise LLMAuthError(f"Invalid Anthropic API key: {e}") from e
        except anthropic.RateLimitError as e:
            raise LLMRateLimitError(f"Anthropic rate limit exceeded: {e}") from e
        except anthropic.APIError as e:
            raise LLMError(f"Anthropic API error: {e}") from e

        return LLMResponse(
            text=message.content[0].text,
            input_tokens=message.usage.input_tokens,
            output_tokens=message.usage.output_tokens,
            model=self.model,
        )

    def stream(self, system: str, user: str):
        import anthropic

        client = self._get_client()
        try:
            with client.messages.stream(
                model=self.model,
                max_tokens=1024,
                system=system,
                messages=[{"role": "user", "content": user}],
            ) as stream:
                for text in stream.text_stream:
                    yield text
        except anthropic.AuthenticationError as e:
            raise LLMAuthError(f"Invalid Anthropic API key: {e}") from e
        except anthropic.RateLimitError as e:
            raise LLMRateLimitError(f"Anthropic rate limit exceeded: {e}") from e
        except anthropic.APIError as e:
            raise LLMError(f"Anthropic API error: {e}") from e
