# state.py
# Manages the robot's current state and conversation history

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
active_persona_key = "jarvis"  # Default to Jarvis
active_voice_name = "Charon"
last_session_end = 0.0

# Session-specific state
conversation_buffer = deque(maxlen=CONVO_MAX_TURNS)

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

def reset_session_state():
    """Clears all temporary session data and records the session end time."""
    global conversation_buffer, last_session_end
    conversation_buffer.clear()
    last_session_end = time.monotonic()
    
    # Save memories when session ends
    if current_memory_manager:
        current_memory_manager.save_memories()

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

def cleanup_memories():
    """Save all memories and perform cleanup."""
    cleanup_all_memories()