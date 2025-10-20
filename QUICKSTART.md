# Quick Start Guide 🚀

Get your Eidoid Pet Robot with Evolving Personas running in 5 minutes!

## Prerequisites

- Python 3.9+ (preferably on Raspberry Pi 5)
- Google Gemini API Key ([Get one free here](https://makersuite.google.com/app/apikey))

## Installation (5 Steps)

### 1. Set up virtual environment
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Set your API key
```bash
export GOOGLE_API_KEY='your-actual-api-key-here'
```

Or create a `.env` file:
```bash
cp .env.example .env
# Edit .env and add your key
```

### 4. Validate setup
```bash
python validate_setup.py
```

You should see ✅ for all checks except API Key (if not exported) and Dependencies (if not installed).

### 5. Run the demo!
```bash
python example_usage.py
```

## What Happens?

1. **Alexa and Jarvis initialize** with their base personalities
2. **Conversations happen** - they remember everything
3. **Sleep loop exits** are counted (demo fast-forwards this)
4. **On the 7th exit** - personalities evolve!
5. **You see the difference** - they've learned and grown

## Key Files

- `main.py` - Main robot loop (use this for production)
- `example_usage.py` - Demo script (use this for testing)
- `validate_setup.py` - Check everything is working
- `config.py` - Tweak settings here

## Customization

### Change evolution frequency
Edit `config.py`:
```python
SLEEP_LOOP_CONFIG = {
    "personality_evolution_interval": 7,  # Change this number
}
```

### Adjust memory size
```python
MEMORY_CONFIG = {
    "max_memories_per_persona": 100,  # More or less memories
}
```

### Modify personalities
```python
PERSONAS = {
    "alexa": {
        "base_personality": "Your custom personality here...",
    }
}
```

## Where's my data?

All memories and personalities are saved in:
```
./data/memory/
├── alexa_memory.json       # All of Alexa's memories
├── alexa_personality.txt   # How Alexa has evolved
├── jarvis_memory.json      # All of Jarvis's memories
└── jarvis_personality.txt  # How Jarvis has evolved
```

## Interacting Programmatically

```python
from main import EidoidRobot

robot = EidoidRobot()

# Chat with Alexa
response = robot.interact_with_persona("alexa", "Hello!")
print(response)

# Check evolution status
status = robot.personas["jarvis"].get_status()
print(f"Jarvis has evolved {status['evolution_count']} times")

# Add a learning experience
robot.personas["alexa"].add_observation(
    "User enjoys science fiction", 
    importance=0.8
)
```

## Troubleshooting

### "No module named 'google'"
```bash
pip install google-generativeai
```

### "GOOGLE_API_KEY not set"
```bash
export GOOGLE_API_KEY='your-key-here'
```

### Dependencies keep failing
```bash
# Upgrade pip first
pip install --upgrade pip
# Then try again
pip install -r requirements.txt
```

## Production Usage

For actual robot deployment:

1. Integrate wake word detection (Porcupine, Snowboy, etc.)
2. Add text-to-speech for responses
3. Run `main.py` instead of `example_usage.py`
4. Set up as systemd service for auto-start

Example systemd service:
```ini
[Unit]
Description=Eidoid Pet Robot
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/eidoid-pet-robot
Environment="GOOGLE_API_KEY=your-key"
ExecStart=/home/pi/eidoid-pet-robot/.venv/bin/python main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

## Next Steps

1. ✅ Run the demo and see personas evolve
2. 📝 Read `IMPLEMENTATION_NOTES.md` for technical details
3. 🎨 Customize personalities in `config.py`
4. 🚀 Integrate with your robot's hardware
5. 🧠 Watch your personas grow and become unique!

## Help & Support

- Check `README.md` for full documentation
- Run `validate_setup.py` to diagnose issues
- Review `IMPLEMENTATION_NOTES.md` for architecture details
- Check logs in `./data/eidoid.log`

---

**Happy Robot Building! 🤖✨**
