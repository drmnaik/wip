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

    def complete(self, system: str, user: str) -> LLMResponse:
        # TODO: Implement using google-genai SDK
        #
        # Rough shape:
        #   from google import genai
        #   client = genai.Client(api_key=self.api_key)
        #   response = client.models.generate_content(
        #       model=self.model,
        #       config=genai.types.GenerateContentConfig(
        #           system_instruction=system,
        #       ),
        #       contents=user,
        #   )
        #   return LLMResponse(
        #       text=response.text,
        #       input_tokens=response.usage_metadata.prompt_token_count,
        #       output_tokens=response.usage_metadata.candidates_token_count,
        #       model=self.model,
        #   )
        #
        # Error mapping:
        #   google.api_core.exceptions.Unauthenticated -> raise LLMAuthError(...)
        #   google.api_core.exceptions.ResourceExhausted -> raise LLMRateLimitError(...)
        #   Exception -> raise LLMError(...)
        raise NotImplementedError("Gemini provider not yet implemented")

    def stream(self, system: str, user: str):
        # TODO: Implement streaming
        #
        # Rough shape:
        #   from google import genai
        #   client = genai.Client(api_key=self.api_key)
        #   response = client.models.generate_content_stream(
        #       model=self.model,
        #       config=genai.types.GenerateContentConfig(
        #           system_instruction=system,
        #       ),
        #       contents=user,
        #   )
        #   for chunk in response:
        #       if chunk.text:
        #           yield chunk.text
        raise NotImplementedError("Gemini streaming not yet implemented")
