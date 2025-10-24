# Memory Separation for Jarvis and Alexa

## Overview
Jarvis and Alexa have completely separate persistent memories managed through two layers:

### 1. Firestore Conversation History
- **Jarvis**: Session ID `eidoid-jarvis-persistent`
- **Alexa**: Session ID `eidoid-alexa-persistent`
- All conversations are automatically stored in Firestore
- Provides smooth, natural continuity across sessions

### 2. Important Memory System (Personality Evolution)
- **Jarvis**: Stores in `persona_memories/jarvis_memory.json`
- **Alexa**: Stores in `persona_memories/alexa_memory.json`
- Only significant information is stored:
  - User facts (name, age, occupation)
  - User preferences
  - Important experiences
  - Emotional connections
- Used for personality trait evolution

## Implementation Details

### Memory Manager Per Persona
```python
# Each persona gets its own memory manager instance
memory_managers = {
    "jarvis": PersonaMemory("jarvis"),
    "alexa": PersonaMemory("alexa")
}
```

### Firestore Session IDs
```python
# In state.py when persona is set:
session_id = f"eidoid-{persona_key}-persistent"
initialize_firestore_memory(session_id=session_id, persona_key=persona_key)
```

### Memory File Storage
```python
# In memory_system.py:
self.memory_file = os.path.join(MEMORY_DIR, f"{persona_key}_memory.json")
```

## Verified Separations

✅ Each persona has its own Firestore collection/session
✅ Each persona has its own JSON memory file
✅ Personality traits are tracked separately
✅ Memory queries only return memories for the active persona
✅ No memory leakage between personas

## Testing
To verify memory separation works:
1. Talk to Jarvis and share some information
2. Check `persona_memories/jarvis_memory.json` - should contain Jarvis's memories
3. Check Firestore for session `eidoid-jarvis-persistent`
4. Switch to Alexa and verify Alexa doesn't have access to Jarvis's memories
5. Share different information with Alexa
6. Check `persona_memories/alexa_memory.json` - should contain Alexa's memories
7. Verify memories remain separate

