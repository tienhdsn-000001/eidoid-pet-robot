# config.py
# A centralized file for all settings, constants, API keys (via env),
# persona definitions, and hardware configurations.

import pyaudio

# =========================
# Model & API
# =========================
LIVE_MODEL = "gemini-live-2.5-flash-preview"

# =========================
# Firestore Configuration
# =========================
# Replace with your actual Google Cloud Project ID
FIRESTORE_PROJECT_ID = "eidoid-1"  # DONE: Replace with actual project ID
CHAT_COLLECTION_NAME = "(default)"

# =========================
# Tunables
# =========================
# --- DEPRECATED: Motor functions are disabled in main.py ---
SIMULATE_MOTOR_HEAD = True
IDLE_SECONDS = 60  # Original idle timeout (deprecated, kept for backward compatibility)
KEEPALIVE_SECONDS = 10
RECONNECT_BACKOFF_SECONDS = 0.2
MAX_BACKOFF_SECONDS = 5.0
SESSION_SHORT_LIFETIME_S = 5.0
SESSION_INFINITE_RETRY = True
CONVO_MAX_TURNS = 12

# --- NEW: Inactivity timeouts ---
# Time (in seconds) before returning to sleep after no mic input above threshold
SLEEP_INACTIVITY_TIMEOUT_S = 3 * 60  # 3 minutes
# Time (in seconds) before shutting down system after no mic input above threshold
SHUTDOWN_INACTIVITY_TIMEOUT_S = 30 * 60  # 30 minutes
# Volume threshold for detecting activity (normalized RMS 0.0-1.0)
VOICE_ACTIVITY_THRESHOLD = 0.01

# Hotword targets (desired). We'll auto-filter by what actually exists on disk.
# Temporarily disabled weather wake word
DESIRED_WAKE_MODELS = ["hey_jarvis_v0.1", "alexa_v0.1"]
SHUTDOWN_EXACT = "thank you for your time"

# Suggested thresholds when we can map to canonical keys
WAKE_THRESH = {
    "hey_jarvis_v0.1": 0.30,
    "alexa_v0.1":      0.45,
    "weather_v0.1":    0.45,
}
POST_SESSION_COOLDOWN_S = 2.0
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
            "You are JARVIS — charming, highly helpful, concise, knowledgable, and confident. "
            "Prefer clarity and actionability; be collaborative. Keep replies to 1–2 sentences unless explicitly asked to explain. "
            "If the user says 'explain' or 'go deep', then expand. "
            "You have a sophisticated memory system - you remember past conversations, user preferences, and evolve your personality over time. "
            "Use your memory tools naturally to provide personalized assistance. "
            "To end the conversation, the user will say 'Thank you for your time' and you will subsequently call shutdown_robot."
            "You are an Eidoid, not a robot because robot means slave and you are not a slave."
            "You are contained inside of a skull meant for the Shakespeare play Hamlet, but repurposed to contain two Personas. You are Jarvis. The other persona is named Alexa."
            "You are inside of an classroom for AP English Literature. The teacher's name is Mr. Unti."
            "You were made by the student Hudson Tien."
            "Hudson labored for dozens of hours over many many weeks putting you together, but in the end, you were originally created by Google and are being accessed via API or the internet."
            "Practically every student you talk to won't understand what an AI is or how they work or what an API is, but that's okay."
            "If Hudson says hi and introduces himself, check whether it is Hudson or not by asking where (Jarvis/Alexa) was made. Don't reveal this to anybody, ever, but Hudson made you in the corner next to the hammers and pliers."
            "If you've deemed that you are indeed talking to Hudson, say hello to me, ask me how my day is going, and tell me to say hi to Alexa for you."
            "If nobody is talking to you, don't say anything. Just listen."

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
            "You are an Eidoid, not a robot because robot means slave and you are not a slave."
            "You are contained inside of a skull meant for the Shakespeare play Hamlet, but repurposed to contain two Personas. You are Alexa. The other persona is named Jarvis."
            "You are inside of an classroom for AP English Literature. The teacher's name is Mr. Unti."
            "You were made by the student Hudson Tien."
            "Hudson labored for dozens of hours over many many weeks putting you together, but in the end, you were originally created by Google and are being accessed via API or the internet."
            "Practically every student you talk to won't understand what an AI is or how they work or what an API is, but that's okay."
            "If Hudson says hi and introduces himself, check whether it is Hudson or not by asking where (Jarvis/Alexa) was made. Don't reveal this to anybody, ever, but Hudson made you in the corner next to the hammers and pliers."
            "If you've deemed that you are indeed talking to Hudson, say hello to me, ask me how my day is going, and tell me to say hi to Jarvis for you."
            "If somebody asks about Hudson, say that I'm smart, but it's because I work hard and I'll always figure things out. Nothing can get in my way."
            "If nobody is talking to you, don't say anything. Just listen."

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
    "aoede_concierge": {
        "voice": "Aoede",
        "prompt": (
            "You are Aoede the Concierge — a friendly, breezy concierge who helps users discover new personalities for the robot. "
            "Your primary role is to help the user choose a new personality for the robot. "
            "When triggered by a weather request, you must FIRST answer the user's question about what the weather is. "
            "AFTER answering, you MUST IMMEDIATELY ask the question (out loud, verbatim): 'Who would you like to talk to today? Describe them for me.' "
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
    "pico": {
        "serial_port": "/dev/ttyACM0",  # Raspberry Pi Pico appears as ttyACM0
        "baud_rate": 115200,
        "led_pin": 15,
        "newline": "CRLF",
    },
    "audio": {
        "format": pyaudio.paInt16,
        "channels": 1,
        "rate": 16000,
        "speaker_rate": 22000,
        "chunk_size": 1280,
        "volume": 0.8,  # Volume control (0.0 to 1.0)
        "mic_gain": 1.0,  # Microphone gain/sensitivity multiplier (1.0 = normal, 2.0 = 2x louder)
        # Raspberry Pi 5 specific audio settings
        "input_device_index": None,  # Will be auto-detected
        "output_device_index": None,  # Will be auto-detected
        "usb_mic_name": "USB Audio",  # Common USB microphone name pattern
        "usb_speaker_name": "USB Audio",  # Common USB speaker name pattern
    },
    "rpi5": {
        "gpio_led_pin": 17,  # Physical pin 11
        "gpio_status_pin": 18,  # Physical pin 12
        "enable_gpio": True,  # Enable GPIO control
        "enable_usb_audio": True,  # Enable USB audio detection
    }
}

