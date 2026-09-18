from app.ai.provider import AIProvider
from app.core.config import Settings


class AIProviderFactory:
    """Provider imports stay local so optional SDK startup failures are isolated."""

    @staticmethod
    def create(settings: Settings) -> AIProvider:
        if settings.ai_provider == "openai":
            from app.ai.openai_provider import OpenAIProvider

            return OpenAIProvider(settings)
        if settings.ai_provider == "gemini":
            from app.ai.gemini_provider import GeminiProvider

            return GeminiProvider(settings)
        raise ValueError(f"Unsupported AI_PROVIDER: {settings.ai_provider}")

