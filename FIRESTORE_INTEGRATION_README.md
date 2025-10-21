# Firestore Integration for Classroom Assistant

This document explains how to set up and use the Google Cloud Firestore integration for persistent chat memory in the Classroom Assistant.

## Overview

The Firestore integration provides persistent, long-term memory for conversations across sessions. This allows the assistant to remember past interactions, user preferences, and maintain context between different conversation sessions.

## Setup Instructions

### 1. Google Cloud Console Setup

Follow the complete setup guide in `firestore_guide.md` to:
- Create a Google Cloud project
- Enable Firestore
- Create a service account
- Download the service account key JSON file

### 2. Environment Configuration

Set the following environment variables:

```bash
# Required: Path to your service account key JSON file
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your/service-account-key.json"

# Required: Your Google API key for Gemini
export GOOGLE_API_KEY="your-gemini-api-key"
```

### 3. Project Configuration

Update the `config.py` file with your Google Cloud project details:

```python
# Replace with your actual Google Cloud Project ID
FIRESTORE_PROJECT_ID = "your-actual-project-id"
CHAT_COLLECTION_NAME = "classroom-chat-history"
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

## How It Works

### Architecture

The Firestore integration works alongside the existing memory system:

1. **Session Initialization**: Each session gets a unique UUID that identifies the conversation
2. **Message Storage**: All user and assistant messages are automatically saved to Firestore
3. **Context Loading**: At the start of each session, recent conversation history is loaded from Firestore
4. **Persistent Memory**: The assistant can access conversation history across different sessions

### Key Components

- `firestore_memory.py`: Core Firestore integration module
- `FirestoreMemoryManager`: Manages Firestore connections and memory operations
- `ConversationBufferMemory`: LangChain memory object that uses Firestore as backend
- Session management in `main.py` and `state.py`

### Data Flow

```
User Input → State Management → Firestore Storage
     ↓
Gemini Live API → Response → Firestore Storage
     ↓
Session End → Memory Persistence
```

## Usage

### Starting a New Session

The system automatically:
1. Generates a unique session ID
2. Initializes Firestore connection
3. Loads recent conversation history
4. Begins the conversation with context

### Memory Persistence

- **Automatic**: Messages are saved to Firestore as they occur
- **Cross-Session**: Previous conversations are available in new sessions
- **Contextual**: The assistant uses recent history for better responses

### Session Management

Each session is identified by a unique UUID printed at startup:
```
[MAIN] Starting new session with ID: 12345678-1234-1234-1234-123456789abc
```

## Testing

Run the test script to verify your setup:

```bash
python test_firestore_integration.py
```

This will test:
- Environment variable configuration
- Firestore connection
- Message storage and retrieval
- Session management

## Troubleshooting

### Common Issues

1. **Authentication Error**
   - Verify `GOOGLE_APPLICATION_CREDENTIALS` points to valid JSON file
   - Check that the service account has Firestore permissions

2. **Project ID Error**
   - Ensure `FIRESTORE_PROJECT_ID` in `config.py` matches your Google Cloud project

3. **Collection Access Error**
   - Verify Firestore security rules allow read/write access
   - Check that the collection name is correct

### Debug Mode

Enable debug logging by adding print statements in the code or using Python's logging module.

## Security Notes

⚠️ **Important**: The current implementation uses open security rules for prototyping. For production use:

1. Implement proper Firestore security rules
2. Use more restrictive access controls
3. Consider user authentication and authorization
4. Implement data encryption if needed

## File Structure

```
├── firestore_memory.py          # Core Firestore integration
├── config.py                    # Configuration (updated with Firestore settings)
├── main.py                      # Main entry point (updated with session management)
├── state.py                     # State management (updated with Firestore integration)
├── session_manager.py           # Session handling (updated with history loading)
├── test_firestore_integration.py # Test script
├── requirements.txt             # Dependencies (updated with Firestore packages)
└── FIRESTORE_INTEGRATION_README.md # This file
```

## Next Steps

1. Update `FIRESTORE_PROJECT_ID` in `config.py` with your actual project ID
2. Set up your service account key and environment variables
3. Run the test script to verify everything works
4. Start using the assistant with persistent memory!

The integration is designed to work seamlessly with the existing codebase while adding powerful persistent memory capabilities.