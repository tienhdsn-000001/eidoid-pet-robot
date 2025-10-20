"""
Test script for the Persona Memory System
Run this to verify the system works without voice input
"""

import os
import time
import config  # Load environment variables
from gemini_persona import PersonaSystem
import json


def test_persona_system():
    """Test the persona system without voice interface"""
    
    print("Testing Eidoid Pet Robot Persona System...")
    print("-" * 50)
    
    # Initialize system
    system = PersonaSystem()
    
    # Test Alexa persona
    print("\n1. Testing Alexa Persona:")
    system.activate_persona("Alexa")
    
    test_inputs = [
        "Hello! How are you today?",
        "My name is Sarah and I love gardening",
        "What do you think about artificial intelligence?",
        "I'm feeling a bit tired today",
        "Tell me a joke"
    ]
    
    for user_input in test_inputs:
        print(f"\nUser: {user_input}")
        response = system.process_input(user_input)
        print(f"Alexa: {response['response']}")
        print(f"Emotion: {response.get('emotion', 'neutral')}")
        time.sleep(0.5)  # Small delay between interactions
    
    # Test Jarvis persona
    print("\n\n2. Testing Jarvis Persona:")
    system.activate_persona("Jarvis")
    
    test_inputs = [
        "Hello Jarvis, how are your systems today?",
        "Analyze the efficiency of solar panels",
        "What's your assessment of quantum computing?",
        "I need help with a complex problem",
        "Tell me something interesting about science"
    ]
    
    for user_input in test_inputs:
        print(f"\nUser: {user_input}")
        response = system.process_input(user_input)
        print(f"Jarvis: {response['response']}")
        print(f"Emotion: {response.get('emotion', 'neutral')}")
        time.sleep(0.5)
    
    # Test memory recall
    print("\n\n3. Testing Memory Recall:")
    system.activate_persona("Alexa")
    
    print("\nUser: Do you remember my name?")
    response = system.process_input("Do you remember my name?")
    print(f"Alexa: {response['response']}")
    
    # Simulate sleep exits to trigger evolution
    print("\n\n4. Testing Persona Evolution:")
    print("Simulating 7 sleep exits to trigger evolution...")
    
    for i in range(7):
        print(f"Sleep exit {i+1}")
        system.on_sleep_exit()
        time.sleep(0.1)
    
    # Check evolved traits
    print("\n5. Checking Evolved Personalities:")
    stats = system.get_system_stats()
    
    for persona_name, persona_stats in stats["personas"].items():
        print(f"\n{persona_name} Statistics:")
        print(f"  Total interactions: {persona_stats['total_interactions']}")
        print(f"  Short-term memories: {persona_stats['short_term_count']}")
        print(f"  Long-term memories: {persona_stats['long_term_count']}")
        
        traits = persona_stats.get("personality_traits", {})
        if traits:
            print(f"  Evolved traits:")
            print(f"    Dominant emotion: {traits.get('dominant_emotion', 'neutral')}")
            print(f"    Interests: {traits.get('interests', [])}")
            print(f"    Evolution count: {traits.get('evolution_count', 0)}")
    
    # Test with evolved persona
    print("\n\n6. Testing Evolved Persona Response:")
    system.activate_persona("Alexa")
    
    print("\nUser: Tell me about yourself")
    response = system.process_input("Tell me about yourself")
    print(f"Alexa: {response['response']}")
    
    # Save memories
    print("\n\n7. Saving All Memories:")
    system.save_all_memories()
    print("Memories saved successfully!")
    
    print("\n" + "-" * 50)
    print("Test completed successfully!")
    
    # Display memory file locations
    print("\nMemory files saved to:")
    print("  - persona_memories/alexa_memory.pkl")
    print("  - persona_memories/alexa_traits.json")
    print("  - persona_memories/jarvis_memory.pkl")
    print("  - persona_memories/jarvis_traits.json")


if __name__ == "__main__":
    # Check for API key
    if not os.getenv("GEMINI_API_KEY"):
        print("ERROR: GEMINI_API_KEY not set!")
        print("Please set your Gemini API key:")
        print("  export GEMINI_API_KEY='your-api-key'")
        print("Or add it to .env file")
        exit(1)
    
    try:
        test_persona_system()
    except Exception as e:
        print(f"\nError during test: {e}")
        import traceback
        traceback.print_exc()