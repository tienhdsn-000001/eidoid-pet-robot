"""
Configuration for Eidoid Pet Robot with Evolving Persona Memory
Optimized for Raspberry Pi 5
"""

import os
from pathlib import Path

# Base directories
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
MEMORY_DIR = DATA_DIR / "memory"

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
MEMORY_DIR.mkdir(exist_ok=True)

# Gemini API Configuration
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "")
GEMINI_MODEL = "gemini-1.5-pro-002"  # Latest model as of October 2025

# Memory Configuration (Optimized for Raspberry Pi 5)
# Pi 5 has 4-8GB RAM, so we'll be conservative
MEMORY_CONFIG = {
    "max_memories_per_persona": 100,  # Maximum memories to keep in active cache
    "max_context_tokens": 8000,  # Gemini 1.5 Pro supports up to 2M, but we limit for Pi
    "memory_summary_interval": 50,  # Summarize every N memories
    "cache_ttl_minutes": 60,  # Cache time-to-live
    "persistent_storage": True,  # Save memory to disk
}

# Persona Configuration
PERSONAS = {
    "alexa": {
        "name": "Alexa",
        "voice": "Kore",
        "wake_word": "alexa",
        "base_personality": (
            "You are Alexa, a helpful and friendly AI assistant. "
            "You are warm, approachable, and enjoy casual conversation. "
            "You remember past interactions and grow from them."
        ),
        "memory_file": MEMORY_DIR / "alexa_memory.json",
        "personality_file": MEMORY_DIR / "alexa_personality.txt",
    },
    "jarvis": {
        "name": "Jarvis",
        "voice": "Charon",
        "wake_word": "hey jarvis",
        "base_personality": (
            "You are Jarvis, a sophisticated and witty AI butler. "
            "You are professional yet personable, with a touch of dry humor. "
            "You remember past interactions and evolve your personality accordingly."
        ),
        "memory_file": MEMORY_DIR / "jarvis_memory.json",
        "personality_file": MEMORY_DIR / "jarvis_personality.txt",
    }
}

# Sleep Loop Configuration
SLEEP_LOOP_CONFIG = {
    "personality_evolution_interval": 7,  # Evolve personality every 7th exit
    "sleep_duration_seconds": 0.5,  # How long to sleep in the loop
    "max_loop_iterations": 1000,  # Max iterations before forced evolution
}

# Gemini Context Caching Configuration (October 2025 feature)
CACHE_CONFIG = {
    "use_context_caching": True,  # Use Gemini's built-in context caching
    "cache_ttl": 3600,  # 1 hour cache TTL
    "min_tokens_for_cache": 32768,  # Minimum tokens to enable caching
}

# Logging
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
LOG_FILE = DATA_DIR / "eidoid.log"
