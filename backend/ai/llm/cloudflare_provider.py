import base64
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import uuid4

import httpx

from core.config import get_settings


class CloudflareImageGenerationError(RuntimeError):
    pass


@dataclass(frozen=True)
class GeneratedImage:
    content: bytes
    content_type: str
    provider: str
    model: str
    request_id: str
    created_at: datetime
    completed_at: datetime
    latency_ms: int


class CloudflareImageProvider:
    model = "@cf/black-forest-labs/flux-1-schnell"

    def __init__(self) -> None:
        settings = get_settings()
        self.account_id = settings.cloudflare_account_id
        self.api_token = settings.cloudflare_api_token
        if not self.account_id or not self.api_token:
            raise CloudflareImageGenerationError(
                "CLOUDFLARE_ACCOUNT_ID and CLOUDFLARE_API_TOKEN are required"
            )

    async def generate(self, *, prompt: str) -> GeneratedImage:
        endpoint = (
            f"https://api.cloudflare.com/client/v4/accounts/{self.account_id}/ai/run/{self.model}"
        )
        payload = {"prompt": prompt, "steps": 4}
        created_at = datetime.now(UTC)
        started_at = time.perf_counter()

        async with httpx.AsyncClient(timeout=90) as client:
            response = await client.post(
                endpoint,
                headers={
                    "Authorization": f"Bearer {self.api_token}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )

        if not response.is_success:
            raise CloudflareImageGenerationError(
                f"Cloudflare image generation failed: {response.status_code} {response.text}"
            )

        try:
            payload = response.json()
            encoded = payload["result"]["image"]
            image_bytes = base64.b64decode(encoded, validate=True)
        except (KeyError, TypeError, ValueError) as exc:
            raise CloudflareImageGenerationError(
                "Cloudflare returned an unexpected image response"
            ) from exc

        completed_at = datetime.now(UTC)
        return GeneratedImage(
            content=image_bytes,
            content_type="image/jpeg",
            provider="cloudflare",
            model=self.model,
            request_id=response.headers.get("cf-ray", str(uuid4())),
            created_at=created_at,
            completed_at=completed_at,
            latency_ms=int((time.perf_counter() - started_at) * 1000),
        )
