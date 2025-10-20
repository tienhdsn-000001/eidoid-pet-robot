# Eidoid - Streamlined Alexa & Jarvis Edition

A streamlined voice assistant featuring Alexa and Jarvis personas with persistent memory and personality development.

## Features

- **Wake Words**: Say "Hey Jarvis" or "Alexa" to activate
- **Two Distinct Personas**:
  - **Jarvis**: Professional, confident, and helpful (Charon voice)
  - **Alexa**: Friendly, upbeat, and supportive (Aoede voice)
- **Memory System**: Both personas remember conversations and develop unique personalities
- **Web Search**: Real-time information retrieval
- **LED Feedback**: Visual status indication
- **Shutdown Phrase**: Say "Thank you for your time" to end conversations

## Setup

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set Gemini API Key**:
   ```bash
   export GOOGLE_API_KEY=your_api_key_here
   ```

3. **Configure Audio Devices**:
   - Run `python3 list_audio_devices.py` to find your device indices
   - Update `MIC_DEVICE_INDEX` and `SPEAKER_DEVICE_INDEX` in:
     - `wake_word.py` (line 64)
     - `session_manager.py` (lines 32-33)

4. **Run the Assistant**:
   ```bash
   python3 main.py
   ```

## Usage

1. Say "Hey Jarvis" or "Alexa" to wake the assistant
2. The LED will turn on to indicate it's listening
3. Have a conversation - the assistant will remember you!
4. Say "Thank you for your time" to end the session
5. The LED will turn off and return to sleep mode

## LED Indicators

- **Off**: Sleeping, waiting for wake word
- **On (solid)**: Listening to you
- **Pulsing**: Assistant is speaking
- **Quick flash**: Processing (e.g., web search)
- **Double flash**: System ready
- **Triple flash**: Error occurred

## Memory Features

Both personas will:
- Remember your name and preferences
- Recall past conversations
- Develop personality traits based on interactions
- Store important information you share

Memory files are saved in `persona_memories/` directory.

## File Structure

- `main.py` - Main entry point
- `wake_word.py` - Wake word detection
- `session_manager.py` - Gemini Live API session management
- `state.py` - State management
- `config.py` - Configuration (personas, voices, timeouts)
- `services.py` - Web search and memory tools
- `memory_system.py` - Memory and personality system
- `memory_tools.py` - Gemini tool declarations for memory
- `led_controller.py` - LED status feedback
- `utils.py` - Utility functions

## Troubleshooting

- **No wake word detection**: Check microphone permissions and device index
- **No audio output**: Verify speaker device index
- **API errors**: Ensure GOOGLE_API_KEY is set correctly
- **Memory not persisting**: Check write permissions for `persona_memories/` directory

## Notes

- This streamlined version focuses on simplicity and reliability
- Motor controls and persona creation features have been removed
- Only Alexa and Jarvis personas are available
- Memory system provides long-term continuity across sessions