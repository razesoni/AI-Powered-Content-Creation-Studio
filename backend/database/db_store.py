import asyncio
from datetime import datetime
from pathlib import Path
from typing import TypeVar
from uuid import UUID, uuid4

from email_validator import EmailNotValidError, validate_email
from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.ai.llm.content_generation import (
    generate_drafts,
    generate_ideas,
    generate_images,
    generate_outlines,
)
from backend.database.db_schema import (
    AIGeneration,
    ContentIdea,
    Draft,
    Image,
    Outline,
    Project,
    User,
)
from core.config import get_settings
from core.security import hash_password, verify_password
from server.schema.user_schema import LoginUser, RegisterUser

settings = get_settings()
engine = create_async_engine(settings.database_url)
SessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


async def register_user(user: RegisterUser, db):
    try:
        valid = validate_email(str(user.email))
        email = valid.email.lower()
    except EmailNotValidError as exc:
        raise ValueError("Invalid Email") from exc
    result = await db.execute(select(User).where(func.lower(User.email) == email))
    user_registered = result.scalar_one_or_none()
    if user_registered:
        raise ValueError("User already registered")
    new_user = User(
        full_name=user.full_name.strip(),
        email=email,
        password_hash=hash_password(user.password),
    )
    db.add(new_user)
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise ValueError("Error registering user") from exc
    await db.refresh(new_user)
    return new_user


async def login_user(user: LoginUser, db):
    email = str(user.email).strip().lower()
    result = await db.execute(select(User).where(func.lower(User.email) == email))
    user_db = result.scalar_one_or_none()
    if user_db is None:
        raise ValueError("User not found")
    if not verify_password(user.password, user_db.password_hash):
        raise ValueError("Invalid password")
    return user_db


async def create_project(project, user_id, db):
    new_project = Project(
        user_id=user_id,
        title=project.title.strip(),
        description=project.description.strip() if project.description else "",
        platform=project.platform.strip(),
        content_type=project.content_type.strip(),
        target_audience=project.target_audience.strip(),
        tone=project.tone.strip(),
    )
    db.add(new_project)
    await db.commit()
    await db.refresh(new_project)
    return new_project


async def get_user_projects(user_id, db):
    result = await db.execute(
        select(Project).where(Project.user_id == user_id).order_by(Project.updated_at.desc())
    )
    return result.scalars().all()


async def delete_user_project(project_id, user_id, db):
    project = await db.scalar(
        select(Project).where(Project.id == project_id, Project.user_id == user_id)
    )
    if project is None:
        return False
    await db.delete(project)
    await db.commit()
    return True


class IdempotencyKeyReuseError(ValueError):
    """Raised when a key is reused for a different generation request."""


class DraftVersionConflictError(ValueError):
    """Raised when a draft has changed since the client last loaded it."""


T = TypeVar("T")


async def _existing_generation_result(
    db, *, user_id: UUID, project_id: UUID, generation_type: str, idempotency_key: UUID, model
) -> list[T] | None:
    """Return the original resources for a completed request, if any."""
    generation = await db.scalar(
        select(AIGeneration).where(
            AIGeneration.user_id == user_id,
            AIGeneration.idempotency_key == idempotency_key,
        )
    )
    if generation is None:
        return None
    if generation.project_id != project_id or generation.generation_type != generation_type:
        raise IdempotencyKeyReuseError(
            "Idempotency key was already used for another generation request"
        )
    if generation.status != "succeeded" or not generation.result_ids:
        raise IdempotencyKeyReuseError("A generation with this idempotency key did not complete")

    ids = generation.result_ids
    rows = (await db.execute(select(model).where(model.id.in_(ids)))).scalars().all()
    by_id = {str(row.id): row for row in rows}
    cached = [by_id[str(resource_id)] for resource_id in ids if str(resource_id) in by_id]
    if len(cached) != len(ids):
        raise IdempotencyKeyReuseError("The original generation result is no longer available")
    return cached


def _generation_metadata(generated):
    """Normalize local fallback responses and provider responses for audit logging."""
    if hasattr(generated, "data"):
        return generated.data, generated
    return generated, None


async def save_generated_ideas(idea_des, project_id, user_id, db, idempotency_key: UUID):
    project = await db.scalar(
        select(Project).where(Project.id == project_id, Project.user_id == user_id)
    )
    if project is None:
        return None

    cached = await _existing_generation_result(
        db,
        user_id=user_id,
        project_id=project_id,
        generation_type="idea",
        idempotency_key=idempotency_key,
        model=ContentIdea,
    )
    if cached is not None:
        return cached

    generated = await generate_ideas(
        concept=idea_des.effective_concept,
        no_of_ideas=idea_des.effective_count,
        tone=idea_des.tone,
        extra_direction=idea_des.effective_direction,
        platform=project.platform,
        target_audience=project.target_audience,
    )

    new_ideas = []
    data, metadata = _generation_metadata(generated)
    for idea in data.ideas:
        new_idea = ContentIdea(
            project_id=project_id,
            title=idea.idea_title,
            concept_summary=idea.concept_summary,
            hook=idea.hook,
            platform=project.platform,
        )
        db.add(new_idea)
        new_ideas.append(new_idea)

    # Allocate database UUIDs before storing them as the replayable response.
    await db.flush()
    await log_ai_interaction(
        db=db,
        user_id=user_id,
        project_id=project_id,
        generation_type="idea",
        provider=getattr(metadata, "provider", "local-fallback"),
        model=getattr(metadata, "model", "local-fallback"),
        input_tokens=getattr(metadata, "input_tokens", None),
        output_tokens=getattr(metadata, "output_tokens", None),
        latency_ms=getattr(metadata, "latency_ms", None),
        status="succeeded",
        idempotency_key=idempotency_key,
        created_at=getattr(metadata, "created_at", None),
        completed_at=getattr(metadata, "completed_at", None),
        error_code=getattr(metadata, "error_code", None),
        prompt_version="1",
        request_id=getattr(metadata, "request_id", None),
        result_ids=[str(idea.id) for idea in new_ideas],
    )
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        return await _existing_generation_result(
            db,
            user_id=user_id,
            project_id=project_id,
            generation_type="idea",
            idempotency_key=idempotency_key,
            model=ContentIdea,
        )
    for idea in new_ideas:
        await db.refresh(idea)
    return new_ideas


async def save_generated_outlines(idea_id, project_id, user_id, db, idempotency_key: UUID):
    idea = await db.scalar(
        select(ContentIdea).where(ContentIdea.id == idea_id, ContentIdea.project_id == project_id)
    )
    if idea is None:
        return None
    project = await db.scalar(
        select(Project).where(Project.id == project_id, Project.user_id == user_id)
    )
    if project is None:
        return None
    cached = await _existing_generation_result(
        db,
        user_id=user_id,
        project_id=project_id,
        generation_type="outline",
        idempotency_key=idempotency_key,
        model=Outline,
    )
    if cached is not None:
        return cached[0]
    generated = await generate_outlines(
        idea_title=idea.title,
        concept_summary=idea.concept_summary,
        platform=idea.platform,
        hook=idea.hook,
    )
    data, metadata = _generation_metadata(generated)
    new_outline = Outline(
        project_id=project_id,
        idea_id=idea_id,
        title=data.title,
        outline_data=data.outline_data.model_dump(),
        version=1,
    )
    db.add(new_outline)
    await db.flush()
    await log_ai_interaction(
        db=db,
        user_id=user_id,
        project_id=project_id,
        generation_type="outline",
        provider=getattr(metadata, "provider", "local-fallback"),
        model=getattr(metadata, "model", "local-fallback"),
        input_tokens=getattr(metadata, "input_tokens", None),
        output_tokens=getattr(metadata, "output_tokens", None),
        latency_ms=getattr(metadata, "latency_ms", None),
        status="succeeded",
        idempotency_key=idempotency_key,
        created_at=getattr(metadata, "created_at", None),
        completed_at=getattr(metadata, "completed_at", None),
        error_code=getattr(metadata, "error_code", None),
        prompt_version="1",
        request_id=getattr(metadata, "request_id", None),
        result_ids=[str(new_outline.id)],
    )
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        cached = await _existing_generation_result(
            db,
            user_id=user_id,
            project_id=project_id,
            generation_type="outline",
            idempotency_key=idempotency_key,
            model=Outline,
        )
        return cached[0]
    await db.refresh(new_outline)
    return new_outline


async def save_generated_drafts(
    outline_id,
    project_id,
    user_id,
    db,
    draft_format="markdown",
    instructions=None,
    idempotency_key: UUID | None = None,
):
    outline = await db.scalar(
        select(Outline).where(Outline.id == outline_id, Outline.project_id == project_id)
    )
    if outline is None:
        return None
    project = await db.scalar(
        select(Project).where(Project.id == project_id, Project.user_id == user_id)
    )
    if project is None:
        return None
    if idempotency_key is None:
        raise ValueError("idempotency_key is required")
    cached = await _existing_generation_result(
        db,
        user_id=user_id,
        project_id=project_id,
        generation_type="draft",
        idempotency_key=idempotency_key,
        model=Draft,
    )
    if cached is not None:
        return cached[0]
    generated = await generate_drafts(
        title=outline.title,
        outline_data=outline.outline_data,
        platform=project.platform,
        content_type=project.content_type,
        target_audience=project.target_audience,
        tone=project.tone,
        instructions=instructions,
    )
    data, metadata = _generation_metadata(generated)
    new_draft = Draft(
        project_id=project_id,
        outline_id=outline_id,
        title=data.title,
        content=data.content_markdown,
        format=draft_format,
        version=1,
    )
    db.add(new_draft)
    await db.flush()
    await log_ai_interaction(
        db=db,
        user_id=user_id,
        project_id=project_id,
        generation_type="draft",
        provider=getattr(metadata, "provider", "local-fallback"),
        model=getattr(metadata, "model", "local-fallback"),
        input_tokens=getattr(metadata, "input_tokens", None),
        output_tokens=getattr(metadata, "output_tokens", None),
        latency_ms=getattr(metadata, "latency_ms", None),
        status="succeeded",
        idempotency_key=idempotency_key,
        created_at=getattr(metadata, "created_at", None),
        completed_at=getattr(metadata, "completed_at", None),
        error_code=getattr(metadata, "error_code", None),
        prompt_version="1",
        request_id=getattr(metadata, "request_id", None),
        result_ids=[str(new_draft.id)],
    )
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        cached = await _existing_generation_result(
            db,
            user_id=user_id,
            project_id=project_id,
            generation_type="draft",
            idempotency_key=idempotency_key,
            model=Draft,
        )
        return cached[0]
    await db.refresh(new_draft)
    return new_draft


async def get_project_ideas(project_id, user_id, db):
    project = await db.scalar(
        select(Project).where(Project.id == project_id, Project.user_id == user_id)
    )
    if project is None:
        return None
    result = await db.execute(
        select(ContentIdea)
        .where(ContentIdea.project_id == project_id)
        .order_by(ContentIdea.created_at.desc())
    )
    return result.scalars().all()


async def get_project_outlines(project_id, user_id, db):
    project = await db.scalar(
        select(Project).where(Project.id == project_id, Project.user_id == user_id)
    )
    if project is None:
        return None
    result = await db.execute(
        select(Outline).where(Outline.project_id == project_id).order_by(Outline.created_at.desc())
    )
    return result.scalars().all()


async def get_project_drafts(project_id, user_id, db):
    project = await db.scalar(
        select(Project).where(Project.id == project_id, Project.user_id == user_id)
    )
    if project is None:
        return None
    result = await db.execute(
        select(Draft).where(Draft.project_id == project_id).order_by(Draft.updated_at.desc())
    )
    return result.scalars().all()


async def update_user_draft(draft_id, user_id, title, content, version, db):
    """Update an owned draft with optimistic locking to prevent lost edits."""
    owned_draft = await db.scalar(
        select(Draft.id)
        .join(Project, Draft.project_id == Project.id)
        .where(Draft.id == draft_id, Project.user_id == user_id)
    )
    if owned_draft is None:
        return None

    result = await db.execute(
        update(Draft)
        .where(Draft.id == draft_id, Draft.version == version)
        .values(title=title.strip(), content=content, version=Draft.version + 1)
    )
    if result.rowcount != 1:
        await db.rollback()
        raise DraftVersionConflictError("This draft changed elsewhere. Reload it before saving.")

    await db.commit()
    return await db.scalar(select(Draft).where(Draft.id == draft_id))


async def save_generated_images(
    draft_id, project_id, user_id, db, style, image_count, aspect_ratio, prompt, idempotency_key
):
    draft = await db.scalar(
        select(Draft).where(Draft.id == draft_id, Draft.project_id == project_id)
    )
    if draft is None:
        return None
    project = await db.scalar(
        select(Project).where(Project.id == project_id, Project.user_id == user_id)
    )
    if project is None:
        return None

    cached = await _existing_generation_result(
        db,
        user_id=user_id,
        project_id=project_id,
        generation_type="image",
        idempotency_key=idempotency_key,
        model=Image,
    )
    if cached is not None:
        return cached

    generated, effective_prompt = await generate_images(
        project.title, draft.content, style, image_count, aspect_ratio, prompt
    )
    storage_dir = Path(settings.image_storage_dir).resolve()
    await asyncio.to_thread(storage_dir.mkdir, parents=True, exist_ok=True)
    saved_paths: list[Path] = []
    new_images: list[Image] = []

    try:
        for generated_image in generated:
            extension = ".jpg" if generated_image.content_type == "image/jpeg" else ".png"
            filename = f"{uuid4()}{extension}"
            file_path = storage_dir / filename
            await asyncio.to_thread(file_path.write_bytes, generated_image.content)
            saved_paths.append(file_path)
            new_image = Image(
                draft_id=draft_id,
                project_id=project_id,
                style=style,
                image_count=image_count,
                aspect_ratio=aspect_ratio,
                prompt=effective_prompt,
                url=f"{settings.image_public_path.rstrip('/')}/{filename}",
            )
            db.add(new_image)
            new_images.append(new_image)

        await db.flush()
        first_result = generated[0]
        await log_ai_interaction(
            db=db,
            user_id=user_id,
            project_id=project_id,
            generation_type="image",
            provider=first_result.provider,
            model=first_result.model,
            input_tokens=None,
            output_tokens=None,
            latency_ms=sum(item.latency_ms for item in generated),
            status="succeeded",
            idempotency_key=idempotency_key,
            created_at=first_result.created_at,
            completed_at=generated[-1].completed_at,
            prompt_version="1",
            result_ids=[str(image.id) for image in new_images],
        )
        await db.commit()
    except IntegrityError:
        await db.rollback()
        for file_path in saved_paths:
            await asyncio.to_thread(file_path.unlink, missing_ok=True)
        cached = await _existing_generation_result(
            db,
            user_id=user_id,
            project_id=project_id,
            generation_type="image",
            idempotency_key=idempotency_key,
            model=Image,
        )
        return cached
    except Exception:
        await db.rollback()
        for file_path in saved_paths:
            await asyncio.to_thread(file_path.unlink, missing_ok=True)
        raise

    for new_image in new_images:
        await db.refresh(new_image)
    return new_images


async def get_project_images(project_id, user_id, db):
    project = await db.scalar(
        select(Project).where(Project.id == project_id, Project.user_id == user_id)
    )
    if project is None:
        return None
    result = await db.execute(
        select(Image).where(Image.project_id == project_id).order_by(Image.created_at.desc())
    )
    return result.scalars().all()


async def log_ai_interaction(
    db,
    user_id: UUID,
    project_id: UUID,
    generation_type: str,
    provider: str,
    model: str,
    input_tokens: int,
    output_tokens: int,
    latency_ms: int,
    status: str,
    idempotency_key: UUID,
    created_at: datetime | None,
    completed_at: datetime | None,
    error_code: str | None = None,
    request_id: UUID | None = None,
    prompt_version: str | None = None,
    result_ids: list[str] | None = None,
):
    new_log = AIGeneration(
        user_id=user_id,
        project_id=project_id,
        generation_type=generation_type,
        provider=provider,
        model=model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        latency_ms=latency_ms,
        status=status,
        error_code=error_code,
        request_id=request_id,
        prompt_version=prompt_version,
        idempotency_key=idempotency_key,
        created_at=created_at,
        completed_at=completed_at,
        result_ids=result_ids,
    )
    db.add(new_log)
    return new_log


async def get_db():
    async with SessionLocal() as db:
        yield db
