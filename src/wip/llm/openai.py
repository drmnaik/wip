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

    def complete(self, system: str, user: str) -> LLMResponse:
        # TODO: Implement using openai SDK
        #
        # Rough shape:
        #   from openai import OpenAI
        #   client = OpenAI(api_key=self.api_key)
        #   response = client.chat.completions.create(
        #       model=self.model,
        #       messages=[
        #           {"role": "system", "content": system},
        #           {"role": "user", "content": user},
        #       ],
        #   )
        #   choice = response.choices[0]
        #   return LLMResponse(
        #       text=choice.message.content,
        #       input_tokens=response.usage.prompt_tokens,
        #       output_tokens=response.usage.completion_tokens,
        #       model=self.model,
        #   )
        #
        # Error mapping:
        #   openai.AuthenticationError -> raise LLMAuthError(...)
        #   openai.RateLimitError      -> raise LLMRateLimitError(...)
        #   openai.APIError            -> raise LLMError(...)
        raise NotImplementedError("OpenAI provider not yet implemented")

    def stream(self, system: str, user: str):
        # TODO: Implement streaming
        #
        # Rough shape:
        #   from openai import OpenAI
        #   client = OpenAI(api_key=self.api_key)
        #   stream = client.chat.completions.create(
        #       model=self.model,
        #       messages=[
        #           {"role": "system", "content": system},
        #           {"role": "user", "content": user},
        #       ],
        #       stream=True,
        #   )
        #   for chunk in stream:
        #       delta = chunk.choices[0].delta.content
        #       if delta:
        #           yield delta
        raise NotImplementedError("OpenAI streaming not yet implemented")
