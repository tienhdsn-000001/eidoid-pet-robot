#!/usr/bin/env python3
"""
Test script for Firestore integration.
This script tests the basic functionality of the Firestore memory system.
"""

import os
import sys
import uuid
from firestore_memory import initialize_firestore_memory, get_firestore_memory

def test_firestore_integration():
    """Test the Firestore memory integration."""
    print("=== Testing Firestore Integration ===")
    
    # Check environment variables
    if not os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
        print("❌ GOOGLE_APPLICATION_CREDENTIALS not set")
        return False
    
    if not os.getenv("GOOGLE_API_KEY"):
        print("❌ GOOGLE_API_KEY not set")
        return False
    
    print("✅ Environment variables set")
    
    try:
        # Initialize Firestore memory
        session_id = str(uuid.uuid4())
        print(f"📝 Initializing session: {session_id}")
        
        memory_manager = initialize_firestore_memory(session_id)
        print("✅ Firestore memory initialized")
        
        # Test adding messages
        print("📤 Testing message storage...")
        memory_manager.conversation_memory.chat_memory.add_user_message("Hello, this is a test message from the user.")
        memory_manager.conversation_memory.chat_memory.add_ai_message("Hello! This is a test response from the assistant.")
        
        print("✅ Messages added to Firestore")
        
        # Test retrieving messages
        print("📥 Testing message retrieval...")
        messages = memory_manager.get_recent_messages(count=5)
        print(f"✅ Retrieved {len(messages)} messages")
        
        for i, msg in enumerate(messages):
            print(f"  Message {i+1}: {msg.content[:50]}...")
        
        # Test session ID
        print(f"🆔 Session ID: {memory_manager.get_session_id()}")
        
        print("✅ All tests passed! Firestore integration is working.")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_firestore_integration()
    sys.exit(0 if success else 1)