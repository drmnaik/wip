"""OpenAI (GPT) provider."""

from __future__ import annotations

from wip.llm.base import LLMProvider, LLMResponse, LLMError, LLMAuthError, LLMRateLimitError

DEFAULT_MODEL = "gpt-4o"


class OpenAIProvider(LLMProvider):
    """OpenAI GPT provider.

    Requires: `pip install openai`
    API key env var: OPENAI_API_KEY
    Docs: https://platform.openai.com/docs/api-reference/chat
    """

    name = "openai"

    def __init__(self, api_key: str, model: str = "") -> None:
        super().__init__(api_key, model or DEFAULT_MODEL)
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                from openai import OpenAI
            except ImportError:
                raise LLMError(
                    "openai package not installed. Run: pip install openai"
                )
            self._client = OpenAI(api_key=self.api_key)
        return self._client

    def complete(self, system: str, user: str) -> LLMResponse:
        import openai

        client = self._get_client()
        try:
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            )
        except openai.AuthenticationError as e:
            raise LLMAuthError(f"Invalid OpenAI API key: {e}") from e
        except openai.RateLimitError as e:
            raise LLMRateLimitError(f"OpenAI rate limit exceeded: {e}") from e
        except openai.APIError as e:
            raise LLMError(f"OpenAI API error: {e}") from e

        choice = response.choices[0]
        return LLMResponse(
            text=choice.message.content,
            input_tokens=response.usage.prompt_tokens,
            output_tokens=response.usage.completion_tokens,
            model=self.model,
        )

    def stream(self, system: str, user: str):
        import openai

        client = self._get_client()
        try:
            stream = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                stream=True,
            )
            for chunk in stream:
                delta = chunk.choices[0].delta.content
                if delta:
                    yield delta
        except openai.AuthenticationError as e:
            raise LLMAuthError(f"Invalid OpenAI API key: {e}") from e
        except openai.RateLimitError as e:
            raise LLMRateLimitError(f"OpenAI rate limit exceeded: {e}") from e
        except openai.APIError as e:
            raise LLMError(f"OpenAI API error: {e}") from e
