# firestore_memory.py
# Firestore integration for persistent chat memory using LangChain

import os
import uuid
from typing import Optional
from langchain_google_firestore import FirestoreChatMessageHistory
from langchain.memory import ConversationBufferMemory
from langchain.schema import BaseMessage
from config import FIRESTORE_PROJECT_ID, CHAT_COLLECTION_NAME

class FirestoreMemoryManager:
    """Manages persistent chat memory using Google Cloud Firestore."""
    
    def __init__(self, session_id: Optional[str] = None):
        """
        Initialize Firestore memory manager.
        
        Args:
            session_id: Unique session identifier. If None, generates a new one.
        """
        # Generate unique session ID if not provided
        self.session_id = session_id or str(uuid.uuid4())
        
        # Verify authentication environment variable is set
        if not os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
            raise ValueError(
                "GOOGLE_APPLICATION_CREDENTIALS environment variable not set. "
                "Please set it to the path of your service account key JSON file."
            )
        
        print(f"[FIRESTORE] Initializing memory for session: {self.session_id}")
        
        try:
            # Initialize Firestore chat history
            self.firestore_history = FirestoreChatMessageHistory(
                session_id=self.session_id,
                collection=CHAT_COLLECTION_NAME
            )
            
            # Initialize LangChain conversation memory with Firestore backend
            self.conversation_memory = ConversationBufferMemory(
                chat_memory=self.firestore_history,
                memory_key="chat_history",
                return_messages=True
            )
            
            print(f"[FIRESTORE] Memory initialized successfully. Collection: {CHAT_COLLECTION_NAME}")
            
        except Exception as e:
            print(f"[FIRESTORE] Error initializing Firestore memory: {e}")
            print(f"[FIRESTORE] Project ID: {FIRESTORE_PROJECT_ID}")
            print(f"[FIRESTORE] Collection: {CHAT_COLLECTION_NAME}")
            print(f"[FIRESTORE] Session ID: {self.session_id}")
            raise
    
    def get_memory(self) -> ConversationBufferMemory:
        """Get the conversation memory object for use with LangChain chains."""
        return self.conversation_memory
    
    def get_session_id(self) -> str:
        """Get the current session ID."""
        return self.session_id
    
    def clear_memory(self):
        """Clear all messages from the current session."""
        self.firestore_history.clear()
        print(f"[FIRESTORE] Memory cleared for session: {self.session_id}")
    
    def get_message_count(self) -> int:
        """Get the number of messages in the current session."""
        return len(self.firestore_history.messages)
    
    def get_recent_messages(self, count: int = 10) -> list[BaseMessage]:
        """Get the most recent messages from the session."""
        messages = self.firestore_history.messages
        return messages[-count:] if messages else []
    
    def get_conversation_context(self, max_messages: int = 10) -> str:
        """
        Get formatted conversation context for use in system prompts.
        
        Args:
            max_messages: Maximum number of recent messages to include
            
        Returns:
            Formatted string with conversation history
        """
        try:
            messages = self.get_recent_messages(max_messages)
            if not messages:
                return "No previous conversation history available."
            
            context_parts = ["Previous conversation context:"]
            for msg in messages:
                if hasattr(msg, 'type') and hasattr(msg, 'content'):
                    role = "User" if msg.type == "human" else "Assistant"
                    context_parts.append(f"{role}: {msg.content}")
                elif hasattr(msg, 'content'):
                    # Fallback for different message formats
                    context_parts.append(f"Message: {msg.content}")
            
            return "\n".join(context_parts)
            
        except Exception as e:
            print(f"[FIRESTORE] Error getting conversation context: {e}")
            return "Error loading conversation context."

# Global memory manager instance
_firestore_memory_manager: Optional[FirestoreMemoryManager] = None

def initialize_firestore_memory(session_id: Optional[str] = None, persona_key: Optional[str] = None) -> FirestoreMemoryManager:
    """
    Initialize or get the global Firestore memory manager.
    
    Args:
        session_id: Unique session identifier. If None, generates a new one.
        persona_key: Persona key to create persona-specific session IDs
    
    Returns:
        FirestoreMemoryManager instance
    """
    global _firestore_memory_manager
    
    # Create persona-specific session ID if persona_key is provided
    if persona_key and session_id:
        persona_session_id = f"{session_id}-{persona_key}"
    elif persona_key:
        persona_session_id = f"eidoid-{persona_key}-session"
    else:
        persona_session_id = session_id or "eidoid-main-session"
    
    if _firestore_memory_manager is None or session_id is not None:
        _firestore_memory_manager = FirestoreMemoryManager(persona_session_id)
    
    return _firestore_memory_manager

def get_firestore_memory() -> Optional[FirestoreMemoryManager]:
    """Get the current Firestore memory manager instance."""
    return _firestore_memory_manager

def cleanup_firestore_memory():
    """Cleanup the global Firestore memory manager."""
    global _firestore_memory_manager
    _firestore_memory_manager = None