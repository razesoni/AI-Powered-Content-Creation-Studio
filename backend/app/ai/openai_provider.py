from openai import AsyncOpenAI

from app.ai.provider import GenerationResult, T
from app.core.config import Settings


class OpenAIProvider:
    def __init__(self, settings: Settings):
        if not settings.openai_api_key or not settings.openai_model:
            raise ValueError("OPENAI_API_KEY and OPENAI_MODEL are required")
        self.client = AsyncOpenAI(api_key=settings.openai_api_key, timeout=settings.ai_timeout_seconds)
        self.model = settings.openai_model

    async def generate(self, *, system_prompt: str, user_prompt: str,
                       response_model: type[T], request_id: str) -> GenerationResult:
        response = await self.client.responses.parse(
            model=self.model,
            instructions=system_prompt,
            input=user_prompt,
            text_format=response_model,
        )
        if response.output_parsed is None:
            raise RuntimeError("Provider returned no parsed output")
        usage = response.usage
        return GenerationResult(
            data=response.output_parsed,
            provider="openai",
            model=self.model,
            input_tokens=getattr(usage, "input_tokens", None),
            output_tokens=getattr(usage, "output_tokens", None),
        )
