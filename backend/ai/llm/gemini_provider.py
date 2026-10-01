import time
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TypeVar
from uuid import UUID, uuid4

from google import genai
from google.genai import types
from pydantic import BaseModel

from core.config import Settings

T = TypeVar("T", bound=BaseModel)


@dataclass(frozen=True)
class GenerationResult:
    data: BaseModel
    provider: str
    model: str
    created_at: datetime
    completed_at: datetime
    latency_ms: int
    status: str
    request_id: UUID
    input_tokens: int | None = None
    output_tokens: int | None = None
    error_code: str | None = None


class GeminiProvider:
    def __init__(self, settings: Settings):
        if not settings.gemini_api_key or not settings.gemini_model:
            raise ValueError("GEMINI_API_KEY and GEMINI_MODEL are required")
        self.client = genai.Client(api_key=settings.gemini_api_key)
        self.model = settings.gemini_model

    async def generate(
        self, *, system_prompt: str, user_prompt: str, response_model: type[T]
    ) -> GenerationResult:
        started_at = time.perf_counter()
        created_at = datetime.now(UTC)
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
        completed_at = datetime.now(UTC)
        latency_ms = int((time.perf_counter() - started_at) * 1000)
        status = "succeeded"
        request_id = uuid4()

        if parsed is None:
            raise RuntimeError("Provider returned no parsed output")
        usage = response.usage_metadata
        return GenerationResult(
            error_code=response.prompt_feedback,
            created_at=created_at,
            completed_at=completed_at,
            latency_ms=latency_ms,
            status=status,
            request_id=request_id,
            data=parsed,
            provider="gemini",
            model=self.model,
            input_tokens=getattr(usage, "prompt_token_count", None),
            output_tokens=getattr(usage, "candidates_token_count", None),
        )
