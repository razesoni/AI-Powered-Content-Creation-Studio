from pydantic import BaseModel, Field


class ContentIdea(BaseModel):
    title: str = Field(min_length=3, max_length=160)
    concept_summary: str = Field(min_length=10, max_length=1000)
    hook: str = Field(min_length=3, max_length=300)
    platform: str = Field(min_length=2, max_length=50)


class IdeaBatch(BaseModel):
    ideas: list[ContentIdea] = Field(min_length=1, max_length=10)


class OutlineSection(BaseModel):
    heading: str = Field(min_length=2, max_length=160)
    purpose: str = Field(min_length=3, max_length=500)
    key_points: list[str] = Field(min_length=1, max_length=12)


class GeneratedOutline(BaseModel):
    title: str
    sections: list[OutlineSection] = Field(min_length=1, max_length=20)
    call_to_action: str | None = None


class GeneratedDraft(BaseModel):
    title: str
    content_markdown: str = Field(min_length=20, max_length=50000)

