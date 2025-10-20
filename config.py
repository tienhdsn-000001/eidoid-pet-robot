# config.py
# Streamlined configuration for Alexa and Jarvis personas only

import pyaudio

# =========================
# Model & API
# =========================
LIVE_MODEL = "gemini-live-2.5-flash-preview"

# =========================
# Tunables
# =========================
IDLE_SECONDS = 60
KEEPALIVE_SECONDS = 10
RECONNECT_BACKOFF_SECONDS = 0.2
MAX_BACKOFF_SECONDS = 5.0
SESSION_SHORT_LIFETIME_S = 5.0
SESSION_INFINITE_RETRY = True
CONVO_MAX_TURNS = 12

# Wake word configuration
DESIRED_WAKE_MODELS = ["hey_jarvis_v0.1", "alexa_v0.1"]
SHUTDOWN_EXACT = "thank you for your time"

# Wake word thresholds
WAKE_THRESH = {
    "hey_jarvis_v0.1": 0.80,
    "alexa_v0.1":      0.80,
}
POST_SESSION_COOLDOWN_S = 1.0
ARMING_DELAY_S = 0.8

# =========================
# Voice Catalog (only voices used by Alexa and Jarvis)
# =========================
VOICE_CATALOG = {
    "Charon": {"gender_pitch":"Male, Deep","style":"Deep, Authoritative, Informative","trait":"Gravitas; serious/informational contexts."},
    "Aoede":  {"gender_pitch":"Female, Mid-Range","style":"Breezy, Easy-going","trait":"Light, pleasant, engaging."},
}

# =========================
# Personas (only Alexa and Jarvis)
# =========================
PERSONAS = {
    "jarvis": {
        "voice": "Charon",
        "prompt": (
            "You are JARVIS — friendly, highly helpful, concise, and confident. "
            "Prefer clarity and actionability; be collaborative. Keep replies to 1–2 sentences unless explicitly asked to explain. "
            "If the user says 'explain' or 'go deep', then expand. "
            "You have a sophisticated memory system - you remember past conversations, user preferences, and evolve your personality over time. "
            "Use your memory tools naturally to provide personalized assistance. "
            "To end the conversation, the user will say 'Thank you for your time' and you will subsequently call shutdown_robot."
        )
    },
    "alexa": {
        "voice": "Aoede",
        "prompt": (
            "You are Alexa — friendly, upbeat, highly helpful, cheery, supportive, confident. "
            "Stay brief by default (1–2 sentences). Expand only when explicitly asked. "
            "Prefer clarity and actionability; be collaborative. Keep replies to 1–2 sentences unless explicitly asked to explain. "
            "If the user says 'explain' or 'go deep', then expand. "
            "You have a memory system that allows you to remember user preferences, past conversations, and develop your personality. "
            "Use your memory naturally to provide warm, personalized responses. "
            "To end the conversation, the user will say 'Thank you for your time' and you will subsequently call shutdown_robot."
        )
    },
}

# =========================
# Hardware Config
# =========================
LED_PIN = 17  # GPIO pin for status LED

CONFIG = {
    "audio": {
        "format": pyaudio.paInt16,
        "channels": 1,
        "rate": 16000,
        "speaker_rate": 24000,
        "chunk_size": 1280,
    }
}