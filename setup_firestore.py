#!/usr/bin/env python3
"""
Setup script for Firestore integration.
This script helps users configure the Firestore integration for the Classroom Assistant.
"""

import os
import sys
import json
from pathlib import Path

def check_environment():
    """Check if required environment variables are set."""
    print("=== Checking Environment Variables ===")
    
    google_api_key = os.getenv("GOOGLE_API_KEY")
    firestore_creds = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    
    if not google_api_key:
        print("❌ GOOGLE_API_KEY not set")
        return False
    else:
        print("✅ GOOGLE_API_KEY is set")
    
    if not firestore_creds:
        print("❌ GOOGLE_APPLICATION_CREDENTIALS not set")
        return False
    else:
        print(f"✅ GOOGLE_APPLICATION_CREDENTIALS is set to: {firestore_creds}")
        
        # Check if the credentials file exists
        if not os.path.exists(firestore_creds):
            print(f"❌ Credentials file not found: {firestore_creds}")
            return False
        else:
            print("✅ Credentials file exists")
    
    return True

def check_config():
    """Check if config.py has been updated with project ID."""
    print("\n=== Checking Configuration ===")
    
    try:
        from config import FIRESTORE_PROJECT_ID, CHAT_COLLECTION_NAME
        
        if FIRESTORE_PROJECT_ID == "your-gcp-project-id":
            print("❌ FIRESTORE_PROJECT_ID not updated in config.py")
            print("   Please update FIRESTORE_PROJECT_ID with your actual Google Cloud project ID")
            return False
        else:
            print(f"✅ FIRESTORE_PROJECT_ID is set to: {FIRESTORE_PROJECT_ID}")
        
        print(f"✅ CHAT_COLLECTION_NAME is set to: {CHAT_COLLECTION_NAME}")
        return True
        
    except ImportError as e:
        print(f"❌ Error importing config: {e}")
        return False

def test_firestore_connection():
    """Test the Firestore connection."""
    print("\n=== Testing Firestore Connection ===")
    
    try:
        from firestore_memory import initialize_firestore_memory
        import uuid
        
        # Test with a temporary session
        test_session_id = f"test-{uuid.uuid4()}"
        print(f"Testing with session ID: {test_session_id}")
        
        memory_manager = initialize_firestore_memory(test_session_id)
        print("✅ Firestore connection successful")
        
        # Test basic operations
        memory_manager.conversation_memory.chat_memory.add_user_message("Test message")
        messages = memory_manager.get_recent_messages(count=1)
        print(f"✅ Message storage and retrieval working ({len(messages)} messages)")
        
        return True
        
    except Exception as e:
        print(f"❌ Firestore connection failed: {e}")
        return False

def main():
    """Main setup function."""
    print("Classroom Assistant - Firestore Integration Setup")
    print("=" * 50)
    
    # Check environment
    if not check_environment():
        print("\n❌ Environment setup incomplete. Please fix the issues above.")
        return False
    
    # Check configuration
    if not check_config():
        print("\n❌ Configuration incomplete. Please update config.py.")
        return False
    
    # Test connection
    if not test_firestore_connection():
        print("\n❌ Firestore connection failed. Please check your setup.")
        return False
    
    print("\n✅ All checks passed! Firestore integration is ready to use.")
    print("\nNext steps:")
    print("1. Run the main application: python main.py")
    print("2. Test the integration: python test_firestore_integration.py")
    print("3. Check the FIRESTORE_INTEGRATION_README.md for detailed usage information")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)