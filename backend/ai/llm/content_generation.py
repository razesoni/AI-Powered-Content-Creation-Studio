from backend.ai.llm.cloudflare_provider import (
    CloudflareImageGenerationError,
    CloudflareImageProvider,
)
from backend.ai.llm.gemini_provider import GeminiProvider
from backend.ai.llm.generation_schema import (
    GenerateDraftResponse,
    GenerateIdeasResponse,
    GenerateOutlineResponse,
    IdeaResponse,
    OutlineData,
    OutlineSection,
)
from backend.ai.prompts.draft_prompt import DRAFT_SYSTEM_PROMPT, DRAFT_USER_PROMPT
from backend.ai.prompts.ideas_prompt import IDEAS_SYSTEM_PROMPT, IDEAS_USER_PROMPT
from backend.ai.prompts.outline_prompt import OUTLINE_SUMMARY_PROMPT, OUTLINE_USER_PROMPT
from core.config import get_settings


class IdeaGenerationError(RuntimeError):
    """Raised when the configured AI provider cannot generate ideas."""


class OutlineGenerationError(RuntimeError):
    """Raised when the configured AI provider cannot generate an outline."""


class DraftGenerationError(RuntimeError):
    """Raised when the configured AI provider cannot generate a draft."""


class ImageGenerationError(RuntimeError):
    """Raised when the configured AI provider cannot generate an image."""


def fallback_ideas(
    concept: str, no_of_ideas: int, tone: str, target_audience: str
) -> GenerateIdeasResponse:
    return GenerateIdeasResponse(
        ideas=[
            IdeaResponse(
                idea_title=f"{concept.title()}: practical angle #{index}",
                concept_summary=(
                    f"A {tone.lower()} content idea about {concept} for {target_audience}."
                ),
                hook=f"A simpler way to think about {concept}: start with this.",
            )
            for index in range(1, no_of_ideas + 1)
        ]
    )


def fallback_outline(idea_title: str, concept_summary: str, hook: str) -> GenerateOutlineResponse:
    return GenerateOutlineResponse(
        title=idea_title,
        outline_data=OutlineData(
            sections=[
                OutlineSection(
                    heading="Hook",
                    purpose="Capture attention and establish why the topic matters.",
                    key_points=[hook, "Name the audience problem or opportunity."],
                ),
                OutlineSection(
                    heading="Core insight",
                    purpose="Explain the main idea in clear, useful language.",
                    key_points=[concept_summary, "Make the takeaway concrete."],
                ),
                OutlineSection(
                    heading="Put it into practice",
                    purpose="Give the audience a simple action they can take.",
                    key_points=["Provide practical steps.", "Include a realistic example."],
                ),
            ],
            call_to_action="What is one step you will try first?",
        ),
    )


def fallback_draft(title: str, outline_data: dict) -> GenerateDraftResponse:
    sections = outline_data.get("sections", [])
    section_markdown = "\n\n".join(
        "\n".join(
            [f"## {section['heading']}", section["purpose"]]
            + [f"- {point}" for point in section.get("key_points", [])]
        )
        for section in sections
    )
    call_to_action = outline_data.get("call_to_action")
    content = f"# {title}\n\n{section_markdown}"
    if call_to_action:
        content += f"\n\n{call_to_action}"
    return GenerateDraftResponse(title=title, content_markdown=content)


async def generate_ideas(
    concept: str,
    no_of_ideas: int,
    tone: str,
    extra_direction: str | None,
    platform: str,
    target_audience: str,
) -> GenerateIdeasResponse:
    settings = get_settings()
    if not settings.gemini_api_key:
        return fallback_ideas(concept, no_of_ideas, tone, target_audience)
    try:
        result = await GeminiProvider(settings).generate(
            system_prompt=IDEAS_SYSTEM_PROMPT.format(
                project_description=concept,
                no_of_ideas=no_of_ideas,
                tone=tone,
                platform=platform,
                target_audience=target_audience,
            ),
            user_prompt=IDEAS_USER_PROMPT.format(
                concept=concept,
                no_of_ideas=no_of_ideas,
                tone=tone,
                extra_direction=extra_direction or "None",
            ),
            response_model=GenerateIdeasResponse,
        )
    except Exception as exc:
        raise IdeaGenerationError(
            "Gemini could not generate ideas. Check GEMINI_API_KEY and GEMINI_MODEL."
        ) from exc
    return result


async def generate_outlines(
    *, idea_title: str, concept_summary: str, platform: str, hook: str
) -> GenerateOutlineResponse:
    settings = get_settings()
    if not settings.gemini_api_key:
        return fallback_outline(idea_title, concept_summary, hook)
    try:
        result = await GeminiProvider(settings).generate(
            system_prompt=OUTLINE_SUMMARY_PROMPT.format(),
            user_prompt=OUTLINE_USER_PROMPT.format(
                idea_title=idea_title,
                concept_summary=concept_summary,
                platform=platform,
                hook=hook,
            ),
            response_model=GenerateOutlineResponse,
        )
    except Exception as exc:
        raise OutlineGenerationError(
            "Gemini could not generate an outline. Check GEMINI_API_KEY and GEMINI_MODEL."
        ) from exc
    return result


async def generate_drafts(
    *,
    title: str,
    outline_data: dict,
    platform: str,
    content_type: str,
    target_audience: str,
    tone: str,
    instructions: str | None = None,
) -> GenerateDraftResponse:
    settings = get_settings()
    if not settings.gemini_api_key:
        return fallback_draft(title, outline_data)
    try:
        result = await GeminiProvider(settings).generate(
            system_prompt=DRAFT_SYSTEM_PROMPT.format(),
            user_prompt=DRAFT_USER_PROMPT.format(
                platform=platform,
                content_type=content_type,
                target_audience=target_audience,
                tone=tone,
                title=title,
                outline_data=outline_data,
                instructions=instructions or "None",
            ),
            response_model=GenerateDraftResponse,
        )
    except Exception as exc:
        raise DraftGenerationError(
            "Gemini could not generate a draft. Check GEMINI_API_KEY and GEMINI_MODEL."
        ) from exc
    return result


async def generate_images(
    title: str,
    content: str,
    style: str,
    image_count: int,
    aspect_ratio: str,
    prompt: str | None,
):
    content_excerpt = content[:2500]
    image_prompt = (
        f'Create a {style} visual for a social media post titled "{title}". '
        f"Compose it for a {aspect_ratio} aspect ratio. "
        f"Post context: {content_excerpt}. "
        f"Creative direction: {prompt or 'Create an eye-catching, polished visual with no text.'}"
    )
    try:
        provider = CloudflareImageProvider()
        return [
            await provider.generate(prompt=image_prompt) for _ in range(image_count)
        ], image_prompt
    except CloudflareImageGenerationError as exc:
        raise ImageGenerationError(str(exc)) from exc
