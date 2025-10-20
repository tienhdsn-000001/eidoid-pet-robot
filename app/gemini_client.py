from __future__ import annotations

import asyncio
import logging
import os
from typing import Any, Dict, Optional

import httpx
from tenacity import AsyncRetrying, retry_if_exception_type, stop_after_attempt, wait_exponential

from .config import settings

logger = logging.getLogger(__name__)


class GeminiError(Exception):
    pass


class GeminiClient:
    """Thin wrapper around the Gemini REST API (Oct 2025 behavior).

    Notes:
    - Uses REST endpoint compatible with `google.ai.generativelanguage` v1beta
    - Supports text-only generateContent
    - Keeps the interface minimal to avoid heavyweight deps on Pi
    """

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None) -> None:
        self.api_key = api_key or settings.gemini_api_key
        if not self.api_key:
            raise GeminiError("GEMINI_API_KEY is required")
        self.model = model or settings.gemini_model
        self.base = settings.gemini_api_base.rstrip("/")
        self._client = httpx.AsyncClient(timeout=settings.request_timeout_seconds)

    async def aclose(self) -> None:
        await self._client.aclose()

    async def generate(self, system_prompt: str, user_prompt: str) -> str:
        url = f"{self.base}/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        body = {
            "contents": [
                {"role": "user", "parts": [{"text": f"{system_prompt}\n\n{user_prompt}"}]}
            ]
        }
        headers = {"Content-Type": "application/json"}

        async for attempt in AsyncRetrying(
            wait=wait_exponential(multiplier=0.5, min=0.5, max=6),
            stop=stop_after_attempt(4),
            retry=retry_if_exception_type((httpx.HTTPError, asyncio.TimeoutError)),
            reraise=True,
        ):
            with attempt:
                resp = await self._client.post(url, json=body, headers=headers)
                if resp.status_code >= 400:
                    raise GeminiError(f"HTTP {resp.status_code}: {resp.text[:200]}")
                data = resp.json()
                try:
                    return data["candidates"][0]["content"]["parts"][0]["text"]
                except Exception as exc:  # noqa: BLE001
                    raise GeminiError(f"Unexpected response: {data}") from exc
