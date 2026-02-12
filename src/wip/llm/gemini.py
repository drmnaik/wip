"""Google Gemini provider."""

from __future__ import annotations

from wip.llm.base import LLMProvider, LLMResponse, LLMError, LLMAuthError, LLMRateLimitError

DEFAULT_MODEL = "gemini-2.0-flash"


class GeminiProvider(LLMProvider):
    """Google Gemini provider.

    Requires: `pip install google-genai`
    API key env var: GEMINI_API_KEY
    Docs: https://ai.google.dev/gemini-api/docs
    """

    name = "gemini"

    def __init__(self, api_key: str, model: str = "") -> None:
        super().__init__(api_key, model or DEFAULT_MODEL)
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                from google import genai
            except ImportError:
                raise LLMError(
                    "google-genai package not installed. Run: pip install google-genai"
                )
            self._client = genai.Client(api_key=self.api_key)
        return self._client

    def complete(self, system: str, user: str) -> LLMResponse:
        from google.api_core import exceptions as google_exceptions
        from google import genai

        client = self._get_client()
        try:
            response = client.models.generate_content(
                model=self.model,
                config=genai.types.GenerateContentConfig(
                    system_instruction=system,
                ),
                contents=user,
            )
        except google_exceptions.Unauthenticated as e:
            raise LLMAuthError(f"Invalid Gemini API key: {e}") from e
        except google_exceptions.ResourceExhausted as e:
            raise LLMRateLimitError(f"Gemini rate limit exceeded: {e}") from e
        except Exception as e:
            raise LLMError(f"Gemini API error: {e}") from e

        return LLMResponse(
            text=response.text,
            input_tokens=response.usage_metadata.prompt_token_count,
            output_tokens=response.usage_metadata.candidates_token_count,
            model=self.model,
        )

    def stream(self, system: str, user: str):
        from google.api_core import exceptions as google_exceptions
        from google import genai

        client = self._get_client()
        try:
            response = client.models.generate_content_stream(
                model=self.model,
                config=genai.types.GenerateContentConfig(
                    system_instruction=system,
                ),
                contents=user,
            )
            for chunk in response:
                if chunk.text:
                    yield chunk.text
        except google_exceptions.Unauthenticated as e:
            raise LLMAuthError(f"Invalid Gemini API key: {e}") from e
        except google_exceptions.ResourceExhausted as e:
            raise LLMRateLimitError(f"Gemini rate limit exceeded: {e}") from e
        except Exception as e:
            raise LLMError(f"Gemini API error: {e}") from e
