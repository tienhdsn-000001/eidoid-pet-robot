# Quick Start Guide - Eidoid Pet Robot with Memory

## 🚀 5-Minute Setup

### 1. Activate Environment
```bash
source .venv/bin/activate
```

### 2. Set API Key
```bash
export GOOGLE_API_KEY="your-gemini-api-key"
```

### 3. Run the Robot
```bash
python main.py
```

## 🎯 First Interaction

### Activate Jarvis
1. Wait for: `[WAKE_WORD] Listening for: hey jarvis, alexa, weather`
2. Say: **"Hey Jarvis"**
3. Robot wakes up and starts listening

### Have a Conversation
```
You: "Hey Jarvis"
[Robot activates]

You: "My name is Alex and I live in Portland"
Jarvis: "Nice to meet you, Alex. How can I help you today?"

You: "I'm a software developer and I love learning about AI"
Jarvis: "That's great! I'd be happy to discuss AI with you."

You: "What's the weather like?"
Jarvis: [searches web] "In Portland, it's currently 68°F and partly cloudy."

You: "Thank you for your time"
Jarvis: [ends session]
```

### View What Jarvis Remembers
```bash
python memory_viewer.py view jarvis
```

You'll see:
```
============================================================
  Memory for: JARVIS
============================================================

Interaction Count: 1
Familiarity Level: 1/100
Relationship: New acquaintance

============================================================
  Learned Facts About User
============================================================
1. User's name is Alex
   Confidence: 80.0%, Reinforcements: 1
2. User lives in Portland
   Confidence: 80.0%, Reinforcements: 1
3. User works as/at software developer
   Confidence: 80.0%, Reinforcements: 1

============================================================
  User Preferences
============================================================

learning: AI

============================================================
  Conversation Topics
============================================================
  technology: 1 times
  weather: 1 times
```

## 🔄 Second Interaction

Activate Jarvis again:

```
You: "Hey Jarvis"
Jarvis: "Hello again! What can I help you with?"
[Jarvis now remembers you're Alex from Portland]

You: "Remember what I do for work?"
Jarvis: "Yes, you're a software developer. How can I assist with that?"

You: "Can you explain machine learning?"
Jarvis: [provides explanation]
[Jarvis notes you like detailed responses]
```

After this session:
```bash
python memory_viewer.py view jarvis
```

Now shows:
```
Interaction Count: 2
Familiarity Level: 2/100
Relationship: New acquaintance

Developed Personality Traits:
  - slightly detail_orientation
  - slightly enthusiasm
```

## 🎭 Try Alexa

Alexa has a different personality and separate memory:

```
You: "Alexa"
Alexa: "Hi there! How can I brighten your day?"

You: "I'm learning Python programming"
Alexa: "That's awesome! Python is such a great language to learn."

You: "Thank you for your time"
[ends session]
```

View Alexa's memory:
```bash
python memory_viewer.py view alexa
```

Alexa and Jarvis have completely separate memories!

## 📊 Memory Commands

### List All Personas
```bash
python memory_viewer.py list
```

### View Detailed Memory
```bash
python memory_viewer.py view jarvis
python memory_viewer.py view alexa
```

### Export Backup
```bash
python memory_viewer.py export jarvis jarvis_backup.json
```

### Clear Short-Term Memory Only
```bash
python memory_viewer.py clear jarvis
```

### Reset All Memory (CAREFUL!)
```bash
python memory_viewer.py reset jarvis
# Type "yes" to confirm
```

## 🎓 How Personas Learn

### Facts Automatically Extracted
- **"My name is ___"** → Stores your name
- **"I live in ___"** → Stores your location
- **"I work as ___"** → Stores your occupation
- **"I like ___"** → Stores your preferences
- **"My favorite ___ is ___"** → Stores favorites
- **"I'm learning ___"** → Stores learning interests

### Personality Development
After 5+ interactions, personas start adjusting:

**Jarvis develops:**
- More detailed responses if you often ask "explain"
- Warmer tone if interactions are positive
- Higher enthusiasm if you're highly engaged

**Alexa develops:**
- Even more warmth with positive interactions
- Casual tone with familiar users
- Stronger emotional intelligence

### Topics Tracked
- Technology, Weather, Entertainment
- Work, Personal, Health
- Food, Travel, Learning, Hobbies

## 💡 Tips

### Get Better Memory
1. **Be specific**: "I work as a data scientist" vs "I work with data"
2. **State preferences**: "I like jazz music" vs "That's nice music"
3. **Share interests**: "I'm learning Spanish" vs "I study sometimes"

### Develop Personality
1. **Engage deeply**: Ask follow-up questions
2. **Be positive**: Thank the assistant, show appreciation
3. **Return often**: Familiarity builds over multiple sessions

### Check Memory Growth
After each session:
```bash
python memory_viewer.py view jarvis
```

Watch for:
- ✅ New facts learned
- ✅ Topics tracked
- ✅ Familiarity level increasing
- ✅ Personality traits developing

## 🔧 Troubleshooting

### Robot doesn't wake up
- Check: Is `[WAKE_WORD] Listening...` showing?
- Try: Speak louder and clearer
- Check: Microphone device index in `wake_word.py`

### Memory not saving
```bash
# Check if directory exists and has permissions
ls -la .memory/

# Try creating it manually
mkdir .memory
```

### Persona doesn't remember
```bash
# Verify memory file exists
ls .memory/jarvis_memory.json

# View contents
python memory_viewer.py view jarvis

# If empty, memory might not be saving
# Check for errors in terminal output
```

### Want to start fresh
```bash
# Reset specific persona
python memory_viewer.py reset jarvis

# Or delete all memories
rm -rf .memory/
```

## 🎯 Advanced Usage

### Disable Memory (if needed)
Edit `config.py`:
```python
ENABLE_LONG_TERM_MEMORY = False
ENABLE_PERSONALITY_DEVELOPMENT = False
```

### Adjust Memory Limits
Edit `memory_manager.py`:
```python
self.conversation_buffer = deque(maxlen=12)  # Short-term turns
```

### Custom Wake Words
See `config.py` for threshold adjustments:
```python
WAKE_THRESH = {
    "hey_jarvis_v0.1": 0.30,  # Lower = more sensitive
    "alexa_v0.1": 0.45,
}
```

## 📚 Next Steps

1. **Read full documentation**: `MEMORY_SYSTEM.md`
2. **Explore code**: Check out `memory_manager.py`
3. **Run tests**: `python test_memory_system.py`
4. **Customize personas**: Edit `config.py` prompts
5. **View changelog**: `CHANGELOG_MEMORY.md`

## 🎉 Enjoy!

Your robot now has memory and personality! The more you interact, the more it learns and develops its unique character.

Have fun conversations! 🤖✨
