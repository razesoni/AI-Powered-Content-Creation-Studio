from dataclasses import dataclass
from typing import Protocol, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


@dataclass(frozen=True)
class GenerationResult:
    data: BaseModel
    provider: str
    model: str
    input_tokens: int | None = None
    output_tokens: int | None = None


class AIProvider(Protocol):
    async def generate(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_model: type[T],
        request_id: str,
    ) -> GenerationResult: ...

