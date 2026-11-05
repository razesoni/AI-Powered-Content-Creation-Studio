from functools import lru_cache

from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Keep CORS_ORIGINS as a comma-separated string until `parse_origins` runs.
    # Pydantic otherwise expects list settings to be JSON before field validation.
    model_config = SettingsConfigDict(
        env_file=".env", extra="ignore", case_sensitive=False, enable_decoding=False
    )

    app_env: str = "development"
    # The persistence layer uses SQLAlchemy's async engine, so the default
    # SQLite URL must select its async driver as well.
    database_url: str = "sqlite+aiosqlite:///./content_studio.db"
    jwt_secret: str = Field(
        default="replace-with-at-least-32-random-characters",
        validation_alias=AliasChoices("JWT_SECRET"),
    )
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 60
    jwt_issuer: str = "content-studio-api"
    jwt_audience: str = "content-studio-web"
    # Origins are scheme + host (+ optional port), never a URL path or trailing slash.
    # Browsers send `Origin: https://razecontentstudio.netlify.app`, which must
    # match this value exactly for FastAPI's CORS middleware to allow it.
    cors_origins: list[str] = ["https://razecontentstudio.netlify.app", "http://localhost:3000"]
    ai_provider: str = "gemini"
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-3.6-flash"
    ai_timeout_seconds: int = 30
    cloudflare_account_id: str | None = None
    cloudflare_api_token: str | None = None
    image_storage_dir: str = "data/images/generated"
    image_public_path: str = "/generated-images"

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_origins(cls, value: object) -> object:
        if isinstance(value, str):
            return [item.strip().rstrip("/") for item in value.split(",") if item.strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
