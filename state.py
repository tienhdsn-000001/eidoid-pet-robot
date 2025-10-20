# state.py
# Manages the robot's current state (sleeping, waking, listening)
# and conversation history.

import time
from collections import deque
from config import CONVO_MAX_TURNS
from memory_manager import memory_manager

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

# Memory management - get current persona's memory
def get_current_memory():
    """Get the memory for the currently active persona."""
    return memory_manager.get_persona_memory(active_persona_key)

# =========================
# State Management Functions
# =========================
def set_state(new_state):
    global current_state
    current_state = new_state

def set_persona(persona_key, voice_name):
    global active_persona_key, active_voice_name
    # Save current persona's memory before switching
    if active_persona_key:
        current_mem = memory_manager.get_persona_memory(active_persona_key)
        current_mem.save_memory()
    
    active_persona_key = persona_key
    active_voice_name = voice_name
    
    # Record interaction for new persona
    new_mem = memory_manager.get_persona_memory(persona_key)
    new_mem.record_interaction()

def set_session_state(hint=None, is_concierge_waiting=False, custom_instructions=None):
    global startup_hint, concierge_waiting_for_description, session_custom_instructions
    startup_hint = hint
    concierge_waiting_for_description = is_concierge_waiting
    session_custom_instructions = custom_instructions

def reset_session_state():
    """Clears all temporary session data and records the session end time."""
    global conversation_buffer, session_custom_instructions, concierge_waiting_for_description, startup_hint, last_session_end
    
    # Save current persona's memory before resetting
    if active_persona_key:
        current_mem = memory_manager.get_persona_memory(active_persona_key)
        current_mem.save_memory()
        # Clear only short-term memory, keep long-term
        current_mem.clear_short_term()
    
    conversation_buffer.clear()
    session_custom_instructions = None
    concierge_waiting_for_description = False
    startup_hint = None
    # BUG FIX: Update the timestamp when a session ends for the cooldown logic.
    last_session_end = time.monotonic()

def add_user_utt(text: str):
    if text:
        conversation_buffer.append(("user", text.strip()))
        # Also add to persona's memory
        if active_persona_key:
            mem = memory_manager.get_persona_memory(active_persona_key)
            mem.add_conversation_turn("user", text.strip())

def add_assistant_utt(text: str):
    if text:
        conversation_buffer.append(("assistant", text.strip()))
        # Also add to persona's memory
        if active_persona_key:
            mem = memory_manager.get_persona_memory(active_persona_key)
            mem.add_conversation_turn("assistant", text.strip())

def render_memory_recency():
    """
    Render both short-term and long-term memory for the current persona.
    This is used in the system prompt to give the AI context.
    """
    if not active_persona_key:
        return "Recent context: (empty)"
    
    mem = memory_manager.get_persona_memory(active_persona_key)
    
    # Get short-term context from memory manager
    short_term = mem.get_short_term_context(max_turns=6)
    
    # Get long-term context
    long_term = mem.get_long_term_context()
    
    result = []
    
    if long_term:
        result.append("=== LONG-TERM MEMORY ===")
        result.append(long_term)
        result.append("")
    
    if short_term:
        result.append("=== RECENT CONVERSATION ===")
        result.append(short_term)
    elif not long_term:
        result.append("Recent context: (empty)")
    
    return "\n".join(result)

