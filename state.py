# state.py
# Manages the robot's current state (sleeping, waking, listening)
# and conversation history.

import time
from collections import deque
from config import CONVO_MAX_TURNS
from memory_system import get_memory_manager, cleanup_all_memories

# =========================
# State Definitions
# =========================
class RobotState:
    SLEEPING = 1
    WAKING   = 2
    LISTENING= 3

# =========================
# Global State Variables
# =========================
current_state = RobotState.SLEEPING
active_persona_key = "aoede_concierge"
active_voice_name = "Aoede"
last_session_end = 0.0 # <-- BUG FIX: Added the missing variable

# Session-specific state
conversation_buffer = deque(maxlen=CONVO_MAX_TURNS)
session_custom_instructions = None
concierge_waiting_for_description = False
startup_hint = None

# Memory manager reference
current_memory_manager = None

# =========================
# State Management Functions
# =========================
def set_state(new_state):
    global current_state
    current_state = new_state

def set_persona(persona_key, voice_name):
    global active_persona_key, active_voice_name, current_memory_manager
    active_persona_key = persona_key
    active_voice_name = voice_name
    # Initialize memory manager for the persona
    current_memory_manager = get_memory_manager(persona_key)

def set_session_state(hint=None, is_concierge_waiting=False, custom_instructions=None):
    global startup_hint, concierge_waiting_for_description, session_custom_instructions
    startup_hint = hint
    concierge_waiting_for_description = is_concierge_waiting
    session_custom_instructions = custom_instructions

def reset_session_state():
    """Clears all temporary session data and records the session end time."""
    global conversation_buffer, session_custom_instructions, concierge_waiting_for_description, startup_hint, last_session_end
    conversation_buffer.clear()
    session_custom_instructions = None
    concierge_waiting_for_description = False
    startup_hint = None
    # BUG FIX: Update the timestamp when a session ends for the cooldown logic.
    last_session_end = time.monotonic()
    
    # Save memories when session ends
    if current_memory_manager:
        current_memory_manager.save_memories()

def cleanup_memories():
    """Save all memories and perform cleanup."""
    cleanup_all_memories()

def add_user_utt(text: str):
    if text: 
        conversation_buffer.append(("user", text.strip()))
        # Add to memory system
        if current_memory_manager:
            current_memory_manager.add_short_term_memory("user", text.strip())

def add_assistant_utt(text: str):
    if text: 
        conversation_buffer.append(("assistant", text.strip()))
        # Add to memory system
        if current_memory_manager:
            current_memory_manager.add_short_term_memory("assistant", text.strip())

def render_memory_recency():
    # Use advanced memory system if available
    if current_memory_manager:
        return current_memory_manager.generate_context_prompt()
    
    # Fallback to simple buffer
    if not conversation_buffer: return "Recent context: (empty)"
    lines=[]
    for role, t in conversation_buffer:
        who="User" if role=="user" else "Assistant"
        t=(t[:300]+"…") if len(t)>300 else t
        lines.append(f"{who}: {t}")
    return "Recent context:\n" + "\n".join(lines)

