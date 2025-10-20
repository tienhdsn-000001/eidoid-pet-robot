from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    # General
    db_path: str = os.environ.get("MEMORY_DB_PATH", "/workspace/data/memory.db")
    log_level: str = os.environ.get("LOG_LEVEL", "INFO")
    # Memory sizing (Raspberry Pi 5 friendly)
    max_items_per_persona: int = int(os.environ.get("MAX_ITEMS_PER_PERSONA", "2000"))
    max_total_tokens_per_persona: int = int(os.environ.get("MAX_TOKENS_PER_PERSONA", "200000"))
    # Gemini
    gemini_api_key: Optional[str] = os.environ.get("GEMINI_API_KEY")
    gemini_model: str = os.environ.get("GEMINI_MODEL", "gemini-1.5-pro")
    gemini_api_base: str = os.environ.get(
        "GEMINI_API_BASE", "https://generativelanguage.googleapis.com"
    )
    request_timeout_seconds: float = float(os.environ.get("REQUEST_TIMEOUT_SECONDS", "30"))


settings = Settings()
