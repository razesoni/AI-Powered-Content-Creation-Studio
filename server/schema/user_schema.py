from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class RegisterUser(BaseModel):
    full_name: Annotated[str, Field(min_length=2, max_length=120)]
    email: EmailStr
    password: Annotated[str, Field(min_length=8, max_length=128)]


class LoginUser(BaseModel):
    email: EmailStr
    password: Annotated[str, Field(min_length=8, max_length=128)]


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class NewProject(BaseModel):
    title: Annotated[str, Field(min_length=1, max_length=160)]
    description: Annotated[str, Field(max_length=2000)] = ""
    platform: Literal["Instagram", "YouTube", "LinkedIn", "TikTok", "Blog"]
    content_type: Literal["Post", "Article", "Video script", "Short video"]
    target_audience: Annotated[str, Field(min_length=1, max_length=500)]
    tone: Annotated[str, Field(min_length=1, max_length=120)]


class GenerateIdeas(BaseModel):
    concept: str | None = None
    topic: str | None = None
    no_of_ideas: int | None = Field(default=3, ge=1, le=10)
    count: int | None = Field(default=3, ge=1, le=10)
    tone: str = "Engaging"
    extra_direction: str | None = None
    instructions: str | None = None
    idempotency_key: UUID

    @property
    def effective_concept(self) -> str:
        return self.concept or self.topic or "Content Strategy"

    @property
    def effective_count(self) -> int:
        return self.no_of_ideas or self.count or 3

    @property
    def effective_direction(self) -> str | None:
        return self.extra_direction or self.instructions


class GenerateOutline(BaseModel):
    idea_id: UUID
    instructions: str | None = None
    idempotency_key: UUID


class GenerateDraft(BaseModel):
    outline_id: UUID
    format: Literal["markdown", "html", "json"] = "markdown"
    instructions: str | None = None
    idempotency_key: UUID


class UpdateDraft(BaseModel):
    title: Annotated[str, Field(min_length=1, max_length=200)]
    content: Annotated[str, Field(max_length=100_000)]
    version: Annotated[int, Field(ge=1)]


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    full_name: str
    email: EmailStr


class ProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    title: str
    description: str
    platform: str
    content_type: str
    target_audience: str
    tone: str
    created_at: datetime
    updated_at: datetime


class IdeaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    title: str
    concept_summary: str
    hook: str
    platform: str
    is_selected: bool
    created_at: datetime


class OutlineResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    idea_id: UUID
    title: str
    outline_data: dict
    version: int
    created_at: datetime
    updated_at: datetime


class DraftResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    outline_id: UUID
    title: str
    content: str
    format: str
    version: int
    created_at: datetime
    updated_at: datetime


class GenerateImage(BaseModel):
    draft_id: UUID
    idempotency_key: UUID
    style: Literal["Photorealistic", "Editorial", "Collage", "Illustration", "3D", "Anime"]
    image_count: int = Field(default=1, ge=1, le=4)
    aspect_ratio: Literal["1:1", "4:5", "16:9", "9:16"] = "1:1"
    prompt: Annotated[str | None, Field(max_length=1000)] = None


class ImageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    draft_id: UUID
    project_id: UUID
    style: str
    image_count: int
    aspect_ratio: str
    prompt: str
    url: str
    created_at: datetime
