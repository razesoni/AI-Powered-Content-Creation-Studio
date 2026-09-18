from google import genai
from google.genai import types

from app.ai.provider import GenerationResult, T
from app.core.config import Settings


class GeminiProvider:
    def __init__(self, settings: Settings):
        if not settings.gemini_api_key or not settings.gemini_model:
            raise ValueError("GEMINI_API_KEY and GEMINI_MODEL are required")
        self.client = genai.Client(api_key=settings.gemini_api_key)
        self.model = settings.gemini_model

    async def generate(self, *, system_prompt: str, user_prompt: str,
                       response_model: type[T], request_id: str) -> GenerationResult:
        response = await self.client.aio.models.generate_content(
            model=self.model,
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                response_mime_type="application/json",
                response_schema=response_model,
            ),
        )
        parsed = response.parsed
        if parsed is None:
            raise RuntimeError("Provider returned no parsed output")
        usage = response.usage_metadata
        return GenerationResult(
            data=parsed,
            provider="gemini",
            model=self.model,
            input_tokens=getattr(usage, "prompt_token_count", None),
            output_tokens=getattr(usage, "candidates_token_count", None),
        )

