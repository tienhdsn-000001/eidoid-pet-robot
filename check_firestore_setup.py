#!/usr/bin/env python3
"""
Check Firestore setup and database configuration.
This script verifies that Firestore is properly configured and accessible.
"""

import os
import sys
from google.cloud import firestore

def check_firestore_setup():
    """Check Firestore setup and configuration."""
    print("=== Firestore Setup Check ===")
    
    # Check environment variables
    if not os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
        print("❌ GOOGLE_APPLICATION_CREDENTIALS not set")
        return False
    
    if not os.getenv("GOOGLE_API_KEY"):
        print("❌ GOOGLE_API_KEY not set")
        return False
    
    print("✅ Environment variables set")
    
    # Check service account file
    creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if not os.path.exists(creds_path):
        print(f"❌ Service account file not found: {creds_path}")
        return False
    
    print(f"✅ Service account file found: {creds_path}")
    
    try:
        # Initialize Firestore client
        db = firestore.Client()
        print("✅ Firestore client initialized")
        
        # Test basic operations
        test_collection = "test_collection"
        test_doc = db.collection(test_collection).document("test_doc")
        
        # Write test data
        test_data = {
            "message": "Test message",
            "timestamp": firestore.SERVER_TIMESTAMP,
            "test": True
        }
        test_doc.set(test_data)
        print("✅ Test document written successfully")
        
        # Read test data
        doc = test_doc.get()
        if doc.exists:
            print("✅ Test document read successfully")
            print(f"   Data: {doc.to_dict()}")
        else:
            print("❌ Test document not found after writing")
            return False
        
        # Clean up test data
        test_doc.delete()
        print("✅ Test document deleted successfully")
        
        # Check if the main collection exists or can be created
        main_collection = "(default)"  # From config.py
        main_doc = db.collection(main_collection).document("test_session")
        
        # Try to write to main collection
        main_doc.set({"test": True, "timestamp": firestore.SERVER_TIMESTAMP})
        print(f"✅ Main collection '{main_collection}' is accessible")
        
        # Clean up
        main_doc.delete()
        
        print("\n🎉 Firestore setup is working correctly!")
        print("\nNext steps:")
        print("1. Your Firestore database is properly configured")
        print("2. The service account has the necessary permissions")
        print("3. You can now use the Eidoid robot with persistent memory")
        
        return True
        
    except Exception as e:
        print(f"❌ Firestore error: {e}")
        print("\nTroubleshooting:")
        print("1. Check that your Google Cloud project 'eidoid-1' exists")
        print("2. Ensure Firestore is enabled in your project")
        print("3. Verify the service account has 'Cloud Datastore User' role")
        print("4. Check that billing is enabled for your project")
        return False

if __name__ == "__main__":
    success = check_firestore_setup()
    sys.exit(0 if success else 1)
