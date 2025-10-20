from __future__ import annotations

import logging
import os

from .config import settings


def setup_logging() -> None:
    level = getattr(logging, settings.log_level.upper(), logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )

    # Reduce noisy loggers if present
    for noisy in ("httpx", "urllib3", "asyncio", "tenacity"):  # type: ignore[assignment]
        logging.getLogger(noisy).setLevel(max(level, logging.WARNING))
