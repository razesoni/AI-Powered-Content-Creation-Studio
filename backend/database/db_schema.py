import uuid

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    full_name = Column(String(120), nullable=False)
    email = Column(String(254), nullable=False)
    password_hash = Column(Text, nullable=False)
    role = Column(String(30), nullable=False, server_default="creator")
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.current_timestamp()
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )

    projects = relationship("Project", back_populates="user", cascade="all, delete-orphan")
    ai_generations = relationship(
        "AIGeneration", back_populates="user", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint("char_length(trim(full_name)) >= 2", name="users_full_name_check"),
        CheckConstraint("role IN ('creator', 'admin')", name="users_role_check"),
        # Case-insensitive unique index on email
        Index(
            "users_email_unique_ci",
            func.lower(email),
            unique=True,
            postgresql_where=None,
        ),
    )


class Project(Base):
    __tablename__ = "projects"

    id = Column(
        "project_id",
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    title = Column(String(160), nullable=False)
    description = Column(String(2000), nullable=False, server_default="")
    platform = Column(String(50), nullable=False)
    content_type = Column(String(50), nullable=False)
    target_audience = Column(String(500), nullable=False)
    tone = Column(String(120), nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.current_timestamp(),
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )

    # Relationships
    user = relationship("User", back_populates="projects")
    content_ideas = relationship(
        "ContentIdea", back_populates="project", cascade="all, delete-orphan"
    )
    outlines = relationship("Outline", back_populates="project", cascade="all, delete-orphan")
    drafts = relationship("Draft", back_populates="project", cascade="all, delete-orphan")
    images = relationship("Image", back_populates="project", cascade="all, delete-orphan")
    ai_generations = relationship("AIGeneration", back_populates="project")

    __table_args__ = (
        CheckConstraint("char_length(trim(title)) >= 1", name="projects_title_check"),
        CheckConstraint(
            "platform IN ('Instagram', 'YouTube', 'LinkedIn', 'TikTok', 'Blog')",
            name="projects_platform_check",
        ),
        CheckConstraint(
            "content_type IN ('Post', 'Article', 'Video script', 'Short video')",
            name="projects_content_type_check",
        ),
        Index("projects_user_updated_idx", user_id, updated_at.desc()),
    )


class ContentIdea(Base):
    __tablename__ = "content_ideas"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    project_id = Column(
        UUID(as_uuid=True), ForeignKey("projects.project_id", ondelete="CASCADE"), nullable=False
    )
    title = Column(String(200), nullable=False)
    concept_summary = Column(Text, nullable=False)
    hook = Column(String(500), nullable=False)
    platform = Column(String(50), nullable=False)
    is_selected = Column(Boolean, nullable=False, server_default=text("false"))
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.current_timestamp()
    )

    # Relationships
    project = relationship("Project", back_populates="content_ideas")
    outlines = relationship("Outline", back_populates="idea", cascade="all, delete-orphan")

    __table_args__ = (Index("content_ideas_project_created_idx", project_id, created_at.desc()),)


class Outline(Base):
    __tablename__ = "outlines"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    project_id = Column(
        UUID(as_uuid=True), ForeignKey("projects.project_id", ondelete="CASCADE"), nullable=False
    )
    idea_id = Column(
        UUID(as_uuid=True), ForeignKey("content_ideas.id", ondelete="CASCADE"), nullable=False
    )
    title = Column(String(200), nullable=False)
    outline_data = Column(JSONB, nullable=False)
    version = Column(Integer, nullable=False, server_default="1")
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.current_timestamp()
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )

    # Relationships
    project = relationship("Project", back_populates="outlines")
    idea = relationship("ContentIdea", back_populates="outlines")
    drafts = relationship("Draft", back_populates="outline", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint(
            "jsonb_typeof(outline_data) = 'object'", name="outlines_outline_data_check"
        ),
        CheckConstraint("version >= 1", name="outlines_version_check"),
        Index("outlines_project_created_idx", project_id, created_at.desc()),
        Index("outlines_idea_idx", idea_id),
    )


class Draft(Base):
    __tablename__ = "drafts"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    project_id = Column(
        UUID(as_uuid=True), ForeignKey("projects.project_id", ondelete="CASCADE"), nullable=False
    )
    outline_id = Column(
        UUID(as_uuid=True), ForeignKey("outlines.id", ondelete="CASCADE"), nullable=False
    )
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False, server_default="")
    format = Column(String(30), nullable=False, server_default="markdown")
    version = Column(Integer, nullable=False, server_default="1")
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.current_timestamp()
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )

    # Relationships
    project = relationship("Project", back_populates="drafts")
    outline = relationship("Outline", back_populates="drafts")
    images = relationship("Image", back_populates="draft", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("format IN ('markdown', 'html', 'json')", name="drafts_format_check"),
        CheckConstraint("version >= 1", name="drafts_version_check"),
        Index("drafts_project_updated_idx", project_id, updated_at.desc()),
        Index("drafts_outline_idx", outline_id),
    )


class AIGeneration(Base):
    __tablename__ = "ai_generations"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    project_id = Column(
        UUID(as_uuid=True), ForeignKey("projects.project_id", ondelete="SET NULL"), nullable=True
    )
    generation_type = Column(String(30), nullable=False)
    provider = Column(String(50), nullable=False)
    model = Column(String(120), nullable=False)
    prompt_version = Column(String(50), nullable=True)
    idempotency_key = Column(UUID(as_uuid=True), nullable=False)
    status = Column(String(20), nullable=False, server_default="pending")
    input_tokens = Column(Integer, nullable=True)
    output_tokens = Column(Integer, nullable=True)
    latency_ms = Column(Integer, nullable=True)
    error_code = Column(String(100), nullable=True)
    request_id = Column(UUID(as_uuid=True), nullable=True)
    # IDs of resources created by this request, in response order.  This lets a
    # retry return the original response instead of calling the provider again.
    result_ids = Column(JSONB, nullable=True)
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.current_timestamp()
    )
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User", back_populates="ai_generations")
    project = relationship("Project", back_populates="ai_generations")

    __table_args__ = (
        CheckConstraint(
            "generation_type IN ('idea', 'outline', 'draft', 'image')",
            name="ai_generations_generation_type_check",
        ),
        CheckConstraint(
            "status IN ('pending', 'succeeded', 'failed')",
            name="ai_generations_status_check",
        ),
        CheckConstraint(
            "input_tokens IS NULL OR input_tokens >= 0",
            name="ai_generations_input_tokens_check",
        ),
        CheckConstraint(
            "output_tokens IS NULL OR output_tokens >= 0",
            name="ai_generations_output_tokens_check",
        ),
        CheckConstraint(
            "latency_ms IS NULL OR latency_ms >= 0",
            name="ai_generations_latency_ms_check",
        ),
        UniqueConstraint("user_id", "idempotency_key", name="ai_generations_user_idempotency_key"),
        Index("ai_generations_user_created_idx", user_id, created_at.desc()),
        Index("ai_generations_project_created_idx", project_id, created_at.desc()),
    )


class Image(Base):
    __tablename__ = "images"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    draft_id = Column(
        UUID(as_uuid=True), ForeignKey("drafts.id", ondelete="CASCADE"), nullable=False
    )
    project_id = Column(
        UUID(as_uuid=True), ForeignKey("projects.project_id", ondelete="CASCADE"), nullable=False
    )
    prompt = Column(Text, nullable=False)
    style = Column(String(50), nullable=False)
    image_count = Column(Integer, nullable=False, server_default="1")
    aspect_ratio = Column(String(10), nullable=False)
    url = Column(String(500), nullable=False)
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.current_timestamp()
    )

    # Relationships
    draft = relationship("Draft", back_populates="images")
    project = relationship("Project", back_populates="images")

    __table_args__ = (
        CheckConstraint("image_count BETWEEN 1 AND 4", name="images_count_check"),
        Index("images_draft_id_created_idx", draft_id, created_at.desc()),
        Index("images_project_created_idx", project_id, created_at.desc()),
    )
