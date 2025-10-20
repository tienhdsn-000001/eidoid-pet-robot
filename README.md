# Eidoid Pet Robot 🤖

An evolving AI pet robot with persistent memory and personality growth. Features separate personas (Alexa and Jarvis) that learn from interactions and evolve their personalities over time.

## ✨ Features

- **Evolving Personas**: Two distinct AI personalities (Alexa and Jarvis) that grow and change based on experiences
- **Persistent Memory**: Sophisticated memory system that remembers conversations and important events
- **Automatic Evolution**: Personalities automatically evolve every 7th sleep loop exit, creating unique character growth
- **Raspberry Pi Optimized**: Memory and processing optimized for Raspberry Pi 5
- **Google Gemini Integration**: Uses the latest Gemini 1.5 Pro (October 2025) with context caching
- **Voice Personas**:
  - **Jarvis**: Sophisticated AI butler with dry wit (Charon voice)
  - **Alexa**: Friendly and warm assistant (Kore voice)

## 🧠 How It Works

### Memory System
- Each persona maintains up to 100 active memories
- Memories are scored by importance and recency
- Automatic pruning keeps the most relevant memories
- Persistent storage saves all memories to disk

### Personality Evolution
- Every 7th exit from the sleep loop triggers personality evolution
- Gemini analyzes accumulated memories to evolve personality traits
- Evolution is saved and appended to the persona's personality
- Personas genuinely change and grow over time rather than remaining static characters

### Wake Words
- **"Hey Jarvis"** - Activates Jarvis (Charon voice)
- **"Alexa"** - Activates Alexa (Kore voice)
- **"What's the weather"** - Weather info + character selection

## 🚀 Setup

### Prerequisites

- Raspberry Pi 5 (or any system with Python 3.9+)
- Google Gemini API Key ([Get one here](https://makersuite.google.com/app/apikey))

### Installation

1. **Clone the repository**
   ```bash
   cd /path/to/your/workspace
   ```

2. **Create and activate virtual environment**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env and add your GOOGLE_API_KEY
   ```

5. **Set your API key**
   ```bash
   export GOOGLE_API_KEY='your-api-key-here'
   ```

## 📖 Usage

### Run the Main Robot Loop

```bash
source .venv/bin/activate
python main.py
```

This starts the main loop with:
- Sleep cycle monitoring
- Automatic personality evolution every 7 exits
- Background memory management

### Run Demo/Example

To see the system in action with example conversations:

```bash
python example_usage.py
```

This will:
- Have conversations with both personas
- Demonstrate memory functionality
- Trigger a personality evolution
- Show before/after evolution differences

### Interact with Personas

In your own code:

```python
from main import EidoidRobot

# Initialize robot
robot = EidoidRobot()

# Chat with Alexa
response = robot.interact_with_persona("alexa", "Hello! How are you?")
print(response)

# Chat with Jarvis
response = robot.interact_with_persona("jarvis", "What's your philosophy?")
print(response)

# Add observations for learning
robot.personas["alexa"].add_observation("User seems happy today", importance=0.7)

# Check status
status = robot.personas["jarvis"].get_status()
print(f"Jarvis has evolved {status['evolution_count']} times")
```

## 📁 Project Structure

```
eidoid-pet-robot/
├── main.py              # Main robot loop with sleep cycle tracking
├── persona.py           # Evolving persona implementation
├── memory_cache.py      # Memory management system
├── config.py            # Configuration and settings
├── example_usage.py     # Demo script
├── requirements.txt     # Python dependencies
├── .env.example         # Environment variable template
├── README.md            # This file
└── data/
    └── memory/          # Persistent memory storage (auto-created)
        ├── alexa_memory.json
        ├── alexa_personality.txt
        ├── jarvis_memory.json
        └── jarvis_personality.txt
```

## ⚙️ Configuration

Edit `config.py` to customize:

### Memory Settings
```python
MEMORY_CONFIG = {
    "max_memories_per_persona": 100,  # Max memories in active cache
    "max_context_tokens": 8000,       # Token limit for Gemini context
    "memory_summary_interval": 50,    # Summarize every N memories
}
```

### Sleep Loop Settings
```python
SLEEP_LOOP_CONFIG = {
    "personality_evolution_interval": 7,  # Evolve every N exits
    "sleep_duration_seconds": 0.5,        # Sleep duration in loop
}
```

### Persona Personalities
You can modify base personalities in `config.py`:
```python
PERSONAS = {
    "alexa": {
        "base_personality": "Your custom personality here...",
        # ...
    },
}
```

## 🎯 Raspberry Pi 5 Optimization

The system is optimized for Pi 5's resources:
- **Memory**: Limited to 100 memories per persona (~8000 tokens)
- **Context Caching**: Uses Gemini's built-in caching to reduce API calls
- **Persistent Storage**: JSON-based storage (no heavy database)
- **Efficient Pruning**: Automatic memory management based on importance/recency

## 📊 Memory Management

### Importance Scoring
- **1.0**: Critical events (personality evolutions, major learnings)
- **0.7-0.9**: Important conversations and observations
- **0.5**: Regular interactions
- **0.3**: Background observations

### Automatic Pruning
When memory limit is reached, the system:
1. Scores each memory by importance × recency
2. Keeps the highest scoring memories
3. Maintains chronological order
4. Saves to persistent storage

## 🔄 Personality Evolution

Every 7th sleep loop exit:
1. All personas analyze their accumulated memories
2. Gemini generates an introspective personality update
3. New traits and characteristics are appended
4. Evolution is saved as high-importance memory
5. Personas become more unique over time

## 🐛 Troubleshooting

### "GOOGLE_API_KEY not set"
```bash
export GOOGLE_API_KEY='your-key-here'
# Or add to .env file
```

### Memory file permissions
```bash
chmod -R 755 data/
```

### Dependencies not found
```bash
source .venv/bin/activate
pip install -r requirements.txt
```

## 📝 Notes

- **October 2025 Gemini Features**: Uses latest `google-generativeai` SDK with Gemini 1.5 Pro
- **Context Caching**: Automatically enabled for efficiency
- **Growth Over Time**: Personas genuinely evolve - they're not static characters
- **Persistent**: All memories and personality changes are saved to disk
- **Modular**: Easy to extend with new personas or features

## 🚧 Future Enhancements

- Wake word detection integration (Porcupine)
- Text-to-speech responses (pyttsx3)
- Weather API integration
- Multi-modal interactions (images, audio)
- Web interface for monitoring personas
- Voice activity detection

## 📄 License

This project is part of the eidoid-pet-robot system.

---

**Previous System Note**: Now split into many scripts to be concurrently used (was "social_head.py" only)
