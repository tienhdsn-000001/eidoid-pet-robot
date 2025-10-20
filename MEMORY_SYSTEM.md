# Memory System Documentation

## Overview

The Eidoid Pet Robot now features a sophisticated memory system that enables Jarvis and Alexa personas to:
- Remember conversations and build context over time
- Learn facts about users and their preferences
- Develop unique personalities based on interactions
- Build rapport and familiarity with users
- Store short-term and long-term memories separately

## Architecture

The memory system consists of three main components:

### 1. Memory Manager (`memory_manager.py`)
The core memory system that handles:
- **Short-term memory**: Recent conversation context (last 12 turns)
- **Long-term memory**: Persistent facts, preferences, and experiences
- **Personality traits**: Evolving characteristics based on interactions
- **User relationship**: Familiarity level and rapport indicators

Each persona has its own isolated memory stored in the `.memory/` directory.

### 2. Memory Intelligence (`memory_intelligence.py`)
Intelligent conversation analysis that extracts:
- **User facts**: Name, location, occupation, likes/dislikes, goals
- **Emotional tone**: Positive/negative sentiment detection
- **Conversation topics**: Technology, weather, entertainment, work, etc.
- **Interaction quality**: Engagement level, question detection, topic analysis

### 3. Memory Viewer (`memory_viewer.py`)
A command-line utility to inspect and manage persona memories.

## Features

### Long-Term Memory Storage

Each persona stores:
- **User Facts**: Information learned about the user
  - Name, location, occupation
  - Likes and dislikes
  - Goals and interests
  - Confidence levels and reinforcement counts

- **Preferences**: User preferences by category
  - Music, topics, interaction style, etc.
  
- **Conversation Topics**: Frequency of discussed topics
  - Technology, work, entertainment, health, etc.

- **Important Memories**: Emotionally significant moments
  - Stored with emotional weight (0.0-1.0)
  - Timestamp of occurrence

- **Personality Traits**: Developing characteristics
  - Enthusiasm, warmth, humor, formality
  - Detail orientation, curiosity
  - Values range from 0.0 to 1.0

- **User Relationship**: Rapport and familiarity
  - Familiarity level (0-100)
  - Interaction history with timestamps
  - Rapport indicators (positive/negative)

### Personality Development

Personas automatically adjust their personality traits based on:
- **User engagement**: High engagement → increased enthusiasm
- **Detail requests**: Frequent "explain" → increased detail orientation
- **Positive emotions**: Consistent positivity → increased warmth

Traits evolve gradually using weighted averaging to maintain stability.

### Intelligent Fact Extraction

The system automatically detects and stores facts like:
- "My name is John" → Stores: "User's name is John"
- "I live in Seattle" → Stores: "User lives in Seattle"
- "I work as a developer" → Stores: "User works as/at developer"
- "I like pizza" → Stores: "User likes pizza"
- "My favorite movie is Inception" → Stores: "User's favorite movie is Inception"

### Emotional Intelligence

The system detects emotional tone in user messages:
- Positive emotions: happy, excited, love, thank you, etc.
- Negative emotions: sad, frustrated, angry, annoying, etc.
- Emotional intensity based on word frequency and punctuation

Rapport indicators are tracked to guide relationship building.

### Memory Integration with Gemini

Memories are included in the system prompt sent to Gemini Live API:
1. **Long-term context**: Facts, preferences, personality traits
2. **Short-term context**: Recent conversation (last 6 turns)

Format example:
```
=== LONG-TERM MEMORY ===
Interaction count: 15
Relationship: Well-known

Known facts about user:
  - User's name is Sarah
  - User lives in Portland
  - User works as/at software engineer

User preferences:
  topics: technology, AI, robotics

Frequent topics: technology, work, learning

Developed personality traits:
  - strongly enthusiasm
  - moderately warmth
  - slightly detail_orientation

=== RECENT CONVERSATION ===
User: How's the weather?
Assistant: It's sunny and 72°F in Portland today!
...
```

## Usage

### Running the Robot

The memory system is integrated automatically. Just run the robot as normal:

```bash
python main.py
```

Memories are:
- Loaded when a persona activates
- Updated throughout conversations
- Saved when sessions end or personas switch

### Viewing Memories

Use the memory viewer utility:

```bash
# List all personas with saved memories
python memory_viewer.py list

# View detailed memory for a persona
python memory_viewer.py view jarvis
python memory_viewer.py view alexa

# Export memory to a backup file
python memory_viewer.py export jarvis jarvis_backup.json

# Clear short-term memory only (keep long-term)
python memory_viewer.py clear jarvis

# Reset ALL memory for a persona (DESTRUCTIVE)
python memory_viewer.py reset jarvis
```

### Memory Directory Structure

```
.memory/
├── jarvis_memory.json
├── alexa_memory.json
└── leda_concierge_memory.json
```

Each file contains:
- User facts
- Preferences
- Conversation topics
- Important memories
- Personality traits
- User relationship data
- Interaction history

## Configuration

Memory settings in `config.py`:

```python
# Memory Configuration
MEMORY_DIR = ".memory"
ENABLE_PERSONALITY_DEVELOPMENT = True
ENABLE_LONG_TERM_MEMORY = True
```

## Persona-Specific Behavior

### Jarvis
- Refined, professional personality with British sensibility
- Focuses on clarity and actionability
- Develops subtle warmth with familiar users
- References past conversations naturally
- Adapts formality based on user preference

### Alexa
- Warm, enthusiastic personality
- Emotionally intelligent and empathetic
- Celebrates interactions: "Great to talk with you again!"
- Remembers what matters to users
- Develops stronger rapport over time

## Privacy & Data

### What's Stored
- Conversation context and topics
- Facts users explicitly share
- Interaction patterns and preferences
- Personality trait adjustments

### What's NOT Stored
- Raw audio data
- Sensitive personal information (unless explicitly shared)
- External API responses (beyond user-initiated sharing)

### Data Location
All memory files are stored locally in the `.memory/` directory as JSON files.

### Clearing Memories
- Short-term memory clears between sessions
- Long-term memory persists across sessions
- Use `memory_viewer.py reset <persona>` to completely erase persona memory

## Technical Details

### Memory Persistence
- Memories save automatically at session end
- Memories save when switching personas
- JSON format for easy inspection and backup

### Memory Limits
- Last 100 user facts retained
- Last 50 important memories retained
- Last 100 emotional responses tracked
- Last 50 rapport indicators kept
- Conversation buffer: 12 turns (configurable)

### Personality Trait Adjustment
- Uses weighted averaging (70% old, 30% new)
- Prevents rapid personality shifts
- Gradual evolution over multiple interactions

### Gemini API Integration
- Compatible with Gemini Live 2.5 Flash Preview (October 2025)
- Memory context included in system instruction
- No changes to tool definitions required
- Transparent to user experience

## Troubleshooting

### Memory Not Persisting
- Check that `.memory/` directory has write permissions
- Verify persona key is correct (check with `list` command)
- Ensure session completes normally (not force-killed)

### Memory File Corrupted
- Delete the corrupted file: `rm .memory/<persona>_memory.json`
- Memory will reinitialize on next interaction

### Personality Not Developing
- Check `ENABLE_PERSONALITY_DEVELOPMENT = True` in `config.py`
- Needs 5+ interactions to trigger adjustments
- Development is gradual by design

### Too Much Memory Stored
- Use `memory_viewer.py clear <persona>` to reset short-term
- Old memories are automatically pruned (see Memory Limits)

## Future Enhancements

Possible improvements:
- [ ] Import/export specific memory categories
- [ ] Memory search and query capabilities
- [ ] Memory visualization dashboard
- [ ] Multi-user memory separation
- [ ] Semantic memory clustering
- [ ] Memory importance scoring
- [ ] Cross-persona shared knowledge base
- [ ] Memory consolidation and summarization

## October 2025 Gemini API Notes

The implementation uses the latest Gemini Live API features:
- **Model**: `gemini-live-2.5-flash-preview`
- **System Instructions**: Enhanced with memory context
- **Live Streaming**: Real-time audio processing maintained
- **Tool Calling**: Compatible with existing tools
- **Context Management**: Memory integrated into system prompt

No breaking changes to existing functionality - memory is a pure enhancement.
