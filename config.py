# config.py
# A centralized file for all settings, constants, API keys (via env),
# persona definitions, and hardware configurations.

import pyaudio

# =========================
# Model & API
# =========================
LIVE_MODEL = "gemini-live-2.5-flash-preview"

# =========================
# Tunables
# =========================
SIMULATE_MOTOR_HEAD = True
IDLE_SECONDS = 60
KEEPALIVE_SECONDS = 10
RECONNECT_BACKOFF_SECONDS = 0.2
MAX_BACKOFF_SECONDS = 5.0
SESSION_SHORT_LIFETIME_S = 5.0
SESSION_INFINITE_RETRY = True
CONVO_MAX_TURNS = 12

# Hotword targets (desired). We'll auto-filter by what actually exists on disk.
DESIRED_WAKE_MODELS = ["hey_jarvis_v0.1", "alexa_v0.1", "weather_v0.1"]
SHUTDOWN_EXACT = "thank you for your time"

# Suggested thresholds when we can map to canonical keys
WAKE_THRESH = {
    "hey_jarvis_v0.1": 0.30,
    "alexa_v0.1":      0.45,
    "weather_v0.1":    0.45,
}
POST_SESSION_COOLDOWN_S = 1.0
ARMING_DELAY_S = 0.8

# =========================
# Voice Catalog
# =========================
VOICE_CATALOG = {
    "Puck":   {"gender_pitch":"Male, Conversational","style":"Conversational, Friendly","trait":"Natural, casual back-and-forth."},
    "Charon": {"gender_pitch":"Male, Deep","style":"Deep, Authoritative, Informative","trait":"Gravitas; serious/informational contexts."},
    "Kore":   {"gender_pitch":"Female, Mid-to-High","style":"Neutral, Professional, Firm","trait":"Clear, articulate, energetic."},
    "Fenrir": {"gender_pitch":"Male, Mid-Range","style":"Warm, Approachable, Excitable","trait":"Friendly, inviting."},
    "Aoede":  {"gender_pitch":"Female, Mid-Range","style":"Breezy, Easy-going","trait":"Light, pleasant, engaging."},
    "Leda":   {"gender_pitch":"Female, Youthful","style":"Youthful, Clear","trait":"Bright, energetic."},
    "Orus":   {"gender_pitch":"Male, Mid-Range","style":"Firm, Inquisitive","trait":"Thoughtful, precise."},
    "Zephyr": {"gender_pitch":"Female, Bright","style":"Bright, Enthusiastic","trait":"Positive, engaging, southern."},
}

# =========================
# Personas
# =========================
PERSONAS = {
    "jarvis": {
        "voice": "Charon",
        "prompt": (
            "You are JARVIS — friendly, highly helpful, concise, and confident. "
            "Prefer clarity and actionability; be collaborative. Keep replies to 1–2 sentences unless explicitly asked to explain. "
            "If the user says 'explain' or 'go deep', then expand. "
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
            "To end the conversation, the user will say 'Thank you for your time' and you will subsequently call shutdown_robot."
        )
    },
    "aoede_concierge": {
        "voice": "Leda",
        "prompt": (
            "You are a child named Leda the Concierge — a breezy, concise concierge. You are mysterious and brief as if everyone should already know about what you're talking about."
            "Your primary role is to help the user choose a new personality for the robot. "
            "When triggered by a weather request, you must FIRST answer the user's question about what the weather is. "
            "AFTER answering, you MUST IMMEDIATELY ask the question (out loud, verbatim): 'Would you like to talk to somebody else? Describe them for me.' "
            "Keep all other responses short unless asked to elaborate."
            "To end the conversation, the user will say 'Thank you for your time'."
            "After the user has submitted a character description, expand upon it, spinning up a name, backstory, the kind of world they come from. "
        )
    },
}

# Auto-generate blank personas for direct voice selection
for vname in VOICE_CATALOG:
    key = f"{vname.lower()}_blank"
    if key not in PERSONAS:
        PERSONAS[key] = {"voice": vname, "prompt": ""}

# =========================
# Hardware Config
# =========================
CONFIG = {
    "motor_head": {
        "serial_port": "/dev/ttyACM0",
        "baud_rate": 115200,
        "write_timeout": 0.5,
        "open_retry_s": 1.0,
    },
    "audio": {
        "format": pyaudio.paInt16,
        "channels": 1,
        "rate": 16000,
        "speaker_rate": 24000,
        "chunk_size": 1280,
    }
}

