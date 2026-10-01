from pydantic import BaseModel


class IdeaResponse(BaseModel):
    idea_title: str
    concept_summary: str
    hook: str


class GenerateIdeasResponse(BaseModel):
    ideas: list[IdeaResponse]


class OutlineSection(BaseModel):
    heading: str
    purpose: str
    key_points: list[str]


class OutlineData(BaseModel):
    sections: list[OutlineSection]
    call_to_action: str | None = None


class GenerateOutlineResponse(BaseModel):
    title: str
    outline_data: OutlineData


class GenerateDraftResponse(BaseModel):
    title: str
    content_markdown: str


class GenerateImageResponse(BaseModel):
    image_url: str
    width: int
    height: int
    model: str
    seed: int | None = None
