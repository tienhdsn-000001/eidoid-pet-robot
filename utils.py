# utils.py
# Contains common helper functions used across multiple modules.

import re
import sys
from pathlib import Path
from config import SHUTDOWN_EXACT

def normalize_text(s: str) -> str:
    """Normalizes text for keyword matching."""
    s = s.lower()
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def says_shutdown(s: str) -> bool:
    """Checks if a string contains the shutdown phrase."""
    if not s:
        return False
    n = normalize_text(s)
    return SHUTDOWN_EXACT in n

def canonical_model_key(s: str) -> str:
    """Normalize a model name/path into a canonical-ish key."""
    stem = Path(s).stem.lower()
    stem = stem.replace(" ", "_").replace("-", "_")
    return stem

def pretty_model_name(s: str) -> str:
    """Cleans up a model path/name for display."""
    base = Path(s).stem
    base = re.sub(r"_v\d+(\.\d+)*$", "", base)  # drop version suffix like _v0.1
    base = base.replace("_", " ").replace("-", " ")
    return base.title()

