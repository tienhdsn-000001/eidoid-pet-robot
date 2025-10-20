# Eidoid Pet Robot

An evolving AI pet robot with persistent memory and personality development, powered by Google Gemini API (October 2025).

## Features

- **Dual Personas**: Alexa (friendly, helpful) and Jarvis (sophisticated, analytical)
- **Evolving Memory**: Each persona maintains short-term and long-term memory
- **Personality Evolution**: Personas evolve based on interactions every 7th sleep cycle
- **Voice Activation**: Wake words trigger specific personas
- **Optimized for Raspberry Pi 5**: Memory-efficient implementation

## Quick Start

1. **Setup the environment**:
   ```bash
   ./setup.sh
   source .venv/bin/activate
   ```

2. **Configure API key**:
   Edit `.env` file and add your Gemini API key:
   ```
   GEMINI_API_KEY=your-actual-api-key
   ```

3. **Run the robot**:
   ```bash
   python social_head.py
   ```

## Voice Commands

- **"Alexa"** - Activates Alexa persona (friendly, conversational)
- **"Hey Jarvis"** or **"Jarvis"** - Activates Jarvis persona (sophisticated, analytical)
- **"What's the weather"** - Special command for weather + character prompt

## Architecture

### Memory System
- **Short-term memory**: Last 100 interactions (quick access)
- **Long-term memory**: Up to 1000 significant memories per persona
- **Personality traits**: Evolve based on interaction patterns
- **Persistence**: Memories saved to disk for continuity

### Persona Evolution
- Occurs every 7th exit from sleep mode
- Analyzes recent interactions for:
  - Dominant emotions
  - Common topics of interest
  - Interaction patterns
- Updates personality traits accordingly

### Technical Details
- **Gemini 1.5 Flash**: Optimized for Raspberry Pi performance
- **Memory-aware generation**: Uses context from past interactions
- **Efficient storage**: Pickle format for memories, JSON for traits
- **Thread-safe**: Concurrent access to memory caches

## File Structure
```
eidoid-pet-robot/
├── social_head.py       # Main robot controller
├── gemini_persona.py    # Gemini API integration
├── persona_memory.py    # Memory cache system
├── requirements.txt     # Python dependencies
├── setup.sh            # Setup script
├── .env                # API keys (create from template)
└── persona_memories/   # Stored memories directory
    ├── alexa_memory.pkl
    ├── alexa_traits.json
    ├── jarvis_memory.pkl
    └── jarvis_traits.json
```

## Configuration

Edit `robot_config.json` to customize:
```json
{
  "sleep_timeout": 30,      // Seconds before sleep mode
  "evolution_interval": 7,   // Sleep exits before evolution
  "voice_enabled": true,
  "save_interval": 300      // Memory save interval (seconds)
}
```

## Memory Management

The system is optimized for Raspberry Pi 5 with:
- Fixed-size memory buffers (deque)
- Selective long-term memory promotion
- Efficient context window management
- Periodic memory persistence

## Troubleshooting

1. **No audio input**: Install system audio packages:
   ```bash
   sudo apt-get install python3-pyaudio portaudio19-dev
   ```

2. **TTS not working**: Install espeak:
   ```bash
   sudo apt-get install espeak ffmpeg libespeak1
   ```

3. **Memory errors**: Check available disk space for persona memories

## Development

To extend the system:
1. Add new personas in `gemini_persona.py`
2. Customize memory criteria in `persona_memory.py`
3. Add new wake words in `social_head.py`

## Notes

- Personas become more personalized over time
- Memory persists between sessions
- Designed for continuous operation on Raspberry Pi 5
- Uses Gemini 1.5 Flash for optimal performance/cost ratio
