# Eidoid Pet Robot

An intelligent voice-activated robot assistant featuring Jarvis and Alexa personas with memory, personality development, and conversational AI powered by Google's Gemini Live API.

## Features

### 🎙️ Voice-Activated Personas
- **"Hey Jarvis"** - Activates Jarvis (Charon voice): Refined, professional AI assistant
- **"Alexa"** - Activates Alexa (Aoede voice): Warm, enthusiastic companion
- **"What's the weather"** - Activates Leda the Concierge for character creation

### 🧠 Memory System (NEW!)
- **Short-term memory**: Remembers recent conversation context
- **Long-term memory**: Stores facts about you, your preferences, and past interactions
- **Personality development**: Personas evolve based on your conversations
- **Intelligent learning**: Automatically extracts facts, emotions, and topics
- **Rapport building**: Develops familiarity and adapts to your communication style

### 🎭 Personality Development
- Jarvis develops subtle warmth and references past conversations
- Alexa celebrates returning users and remembers what matters to you
- Personality traits adjust based on interaction patterns
- Each persona maintains separate, isolated memories

### 🛠️ Technical Features
- Real-time audio streaming with Gemini Live API
- Offline wake word detection with OpenWakeWord
- LED status indicators
- Web search integration (DuckDuckGo + Wikipedia)
- Local memory storage with JSON persistence
- Command-line memory management tools

## Quick Start

### Setup

```bash
# Activate virtual environment
source .venv/bin/activate

# Set up API key
export GOOGLE_API_KEY="your-api-key-here"

# Run the robot
python main.py
```

### First Conversation

1. Say **"Hey Jarvis"** to activate
2. Have a conversation and share some information about yourself
3. Say **"Thank you for your time"** to end the session
4. Reactivate Jarvis - he'll remember your previous conversation!

### View Memory

```bash
# List all personas with saved memories
python memory_viewer.py list

# View detailed memory for a persona
python memory_viewer.py view jarvis
python memory_viewer.py view alexa

# Export a backup
python memory_viewer.py export jarvis jarvis_backup.json
```

## Documentation

- **[MEMORY_SYSTEM.md](MEMORY_SYSTEM.md)** - Comprehensive memory system documentation
- **[CHANGELOG_MEMORY.md](CHANGELOG_MEMORY.md)** - Detailed changelog for memory features

## Project Structure

### Core Files
- `main.py` - Main application entry point
- `session_manager.py` - Gemini Live API session management
- `state.py` - Robot state and conversation management
- `config.py` - Configuration and persona definitions
- `wake_word.py` - Offline wake word detection
- `services.py` - External services (web search, tools)

### Memory System
- `memory_manager.py` - Core memory implementation
- `memory_intelligence.py` - Intelligent conversation analysis
- `memory_viewer.py` - Command-line memory management utility
- `test_memory_system.py` - Memory system test suite

### Hardware Control
- `led_controller.py` - LED status indicators
- `utils.py` - Utility functions

### Memory Storage
- `.memory/` - Directory for persona memory files (auto-created)
  - `jarvis_memory.json`
  - `alexa_memory.json`
  - `[other_persona]_memory.json`

## How Memory Works

### What Gets Remembered
- **Facts**: "My name is Alice" → Stored: "User's name is Alice"
- **Preferences**: "I like jazz music" → Stored in music preferences
- **Topics**: Discussions about technology, work, hobbies, etc.
- **Emotional tone**: Positive/negative interactions for rapport building
- **Interaction patterns**: Response style, detail preference, engagement level

### Personality Development
Personas automatically adjust traits like:
- **Enthusiasm**: Increases with high user engagement
- **Detail orientation**: Adjusts based on "explain" requests
- **Warmth**: Develops with positive interactions
- **Formality**: Adapts to your communication style

### Memory in Conversations
Memories are included in the AI's context:
```
=== LONG-TERM MEMORY ===
Interaction count: 15
Relationship: Well-known

Known facts about user:
  - User's name is Sarah
  - User works as/at software engineer
  
Frequent topics: technology, work, learning

=== RECENT CONVERSATION ===
User: How's the weather?
Assistant: It's sunny and 72°F today!
```

## Testing

Run the memory system test suite:

```bash
python test_memory_system.py
```

All tests should pass with output showing successful:
- PersonaMemory operations
- MemoryIntelligence analysis
- MemoryManager functionality

## Configuration

Edit `config.py` to customize:

```python
# Memory settings
MEMORY_DIR = ".memory"
ENABLE_PERSONALITY_DEVELOPMENT = True
ENABLE_LONG_TERM_MEMORY = True

# Conversation settings
CONVO_MAX_TURNS = 12
IDLE_SECONDS = 60

# Wake word thresholds
WAKE_THRESH = {
    "hey_jarvis_v0.1": 0.30,
    "alexa_v0.1": 0.45,
}
```

## Privacy

- All memory is stored **locally** in `.memory/` directory
- No external services receive your conversation data
- Memory files are human-readable JSON
- Full control over memory with viewer utility
- Easy to reset: `python memory_viewer.py reset <persona>`

## Requirements

### Hardware
- Microphone (built-in or USB)
- Speaker (built-in or USB)
- Optional: LED for status indicator (GPIO 17)

### Software
- Python 3.8+
- Google Gemini API key
- Dependencies: PyAudio, OpenWakeWord, Google GenAI SDK

## Gemini API (October 2025)

Uses the latest **Gemini Live 2.5 Flash Preview** model with:
- Real-time bidirectional audio streaming
- Live transcription
- Function calling (tools)
- System instruction with memory context

## Wake Word Detection

Offline detection using OpenWakeWord:
- "Hey Jarvis" → Activates Jarvis
- "Alexa" → Activates Alexa
- "Weather" → Activates Leda the Concierge

## Troubleshooting

### Memory Not Saving
```bash
# Check permissions
ls -la .memory/

# Verify memory after session
python memory_viewer.py view jarvis
```

### Memory Corrupted
```bash
# Reset persona memory
python memory_viewer.py reset jarvis
```

### Dependencies Missing
```bash
# Reinstall
pip install -r requirements.txt
```

## Development

Previously a monolithic `social_head.py`, now split into:
- Modular architecture with separate concerns
- Testable memory system
- Extensible persona framework
- Clean separation of hardware, AI, and memory layers

## License

See repository for license information.

## Credits

- Built with Google Gemini Live API
- Wake word detection: OpenWakeWord
- Memory system: Custom implementation (October 2025)