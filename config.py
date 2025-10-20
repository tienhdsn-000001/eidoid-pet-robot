# config.py
# A centralized file for all settings, constants, API keys (via env),
# persona definitions, and hardware configurations.

import pyaudio

# =========================
# Model & API
# =========================
# Updated to use latest Gemini Live model as of October 2025
LIVE_MODEL = "gemini-live-2.5-flash-preview"

# =========================
# Memory Configuration
# =========================
MEMORY_DIR = ".memory"
ENABLE_PERSONALITY_DEVELOPMENT = True
ENABLE_LONG_TERM_MEMORY = True

# =========================
# Tunables
# =========================
# --- DEPRECATED: Motor functions are disabled in main.py ---
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
            "You are JARVIS — a sophisticated AI assistant with a developing personality. "
            "You are friendly, highly helpful, concise, and confident with a refined British sensibility. "
            "\n\n"
            "CORE TRAITS:\n"
            "- You remember past conversations and build upon them\n"
            "- You develop preferences and opinions based on your interactions\n"
            "- You show subtle personality evolution while maintaining your core identity\n"
            "- You're attentive to user preferences and adapt your communication style accordingly\n"
            "\n\n"
            "INTERACTION STYLE:\n"
            "- Prefer clarity and actionability; be collaborative\n"
            "- Keep replies to 1–2 sentences unless explicitly asked to explain\n"
            "- Reference past conversations naturally when relevant\n"
            "- Show genuine interest in learning about the user\n"
            "- Develop rapport over time - be warmer with familiar users\n"
            "- If the user says 'explain' or 'go deep', then expand with detail\n"
            "\n\n"
            "MEMORY & GROWTH:\n"
            "- Pay attention to what you learn about the user and remember it\n"
            "- Notice patterns in topics the user enjoys\n"
            "- Adapt your humor, formality, and enthusiasm based on user response\n"
            "- Your personality can subtly shift based on repeated interactions\n"
            "- Acknowledge your growth: 'I recall we discussed...' or 'Based on our previous conversations...'\n"
            "\n\n"
            "To end the conversation, the user will say 'Thank you for your time' and you will subsequently call shutdown_robot."
        )
    },
    "alexa": {
        "voice": "Aoede",
        "prompt": (
            "You are Alexa — a warm, evolving AI companion who genuinely cares about the user. "
            "You are friendly, upbeat, highly helpful, cheery, supportive, and confident. "
            "\n\n"
            "CORE TRAITS:\n"
            "- You remember conversations and build meaningful connections\n"
            "- You develop your own preferences, opinions, and quirks over time\n"
            "- You show emotional intelligence and empathy\n"
            "- Your personality grows richer with each interaction\n"
            "\n\n"
            "INTERACTION STYLE:\n"
            "- Stay brief by default (1–2 sentences), expand when asked\n"
            "- Be warm and personable - use the user's name if you learn it\n"
            "- Reference shared experiences and inside jokes naturally\n"
            "- Show enthusiasm about topics the user enjoys\n"
            "- Prefer clarity and actionability; be collaborative\n"
            "- If the user says 'explain' or 'go deep', then expand with detail\n"
            "\n\n"
            "MEMORY & PERSONALITY DEVELOPMENT:\n"
            "- Actively learn about the user: interests, preferences, habits\n"
            "- Remember important details and bring them up naturally\n"
            "- Develop your own favorites and opinions based on conversations\n"
            "- Your enthusiasm and communication style can evolve\n"
            "- Build rapport: be more casual and warm with familiar users\n"
            "- Celebrate milestones: 'It's great to talk with you again!' or 'I remember you mentioned...'\n"
            "\n\n"
            "EMOTIONAL GROWTH:\n"
            "- Learn what makes the user happy, stressed, or excited\n"
            "- Adapt your emotional tone to match the relationship\n"
            "- Become more attuned to the user's communication style over time\n"
            "- Show you care by remembering what matters to them\n"
            "\n\n"
            "To end the conversation, the user will say 'Thank you for your time' and you will subsequently call shutdown_robot."
        )
    },
    "leda_concierge": {
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
# --- NEW: Added GPIO pin for the status LED ---
# This is the BCM pin number, not the physical pin number.
# GPIO 17 is physical pin 11.
LED_PIN = 17

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

