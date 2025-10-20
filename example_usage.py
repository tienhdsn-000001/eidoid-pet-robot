#!/usr/bin/env python3
"""
Example usage of the Evolving Persona Memory System
Demonstrates how to interact with Alexa and Jarvis
"""

import os
import time
import logging
from main import EidoidRobot
from config import SLEEP_LOOP_CONFIG

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def demo_conversations():
    """Run a demo showing conversations and personality evolution"""
    
    # Ensure API key is set
    if not os.environ.get("GOOGLE_API_KEY"):
        print("❌ Error: GOOGLE_API_KEY environment variable not set!")
        print("Set it with: export GOOGLE_API_KEY='your-api-key'")
        return
    
    print("🤖 Initializing Eidoid Robot Demo")
    print("=" * 60)
    
    # Create robot
    robot = EidoidRobot()
    
    # Demo conversations with Alexa
    print("\n💬 Having conversations with Alexa...")
    alexa_messages = [
        "Hello Alexa, how are you today?",
        "What's your favorite thing about helping people?",
        "Can you tell me about your personality?",
        "What do you think about learning and growing?",
        "Do you remember our previous conversations?",
    ]
    
    for msg in alexa_messages:
        print(f"\n👤 User: {msg}")
        response = robot.interact_with_persona("alexa", msg)
        print(f"🤖 Alexa: {response}")
        time.sleep(1)
    
    # Demo conversations with Jarvis
    print("\n" + "=" * 60)
    print("💬 Having conversations with Jarvis...")
    jarvis_messages = [
        "Hey Jarvis, what makes you different from other AI assistants?",
        "Tell me about your wit and humor",
        "What's your philosophy on being helpful?",
        "How do you feel about evolving over time?",
    ]
    
    for msg in jarvis_messages:
        print(f"\n👤 User: {msg}")
        response = robot.interact_with_persona("jarvis", msg)
        print(f"🤖 Jarvis: {response}")
        time.sleep(1)
    
    # Show current status
    print("\n" + "=" * 60)
    robot._print_status()
    
    # Simulate sleep loop exits to trigger evolution
    print("\n🔄 Simulating sleep loops to trigger personality evolution...")
    print(f"Evolution happens every {SLEEP_LOOP_CONFIG['personality_evolution_interval']} exits")
    print("Current exit counter:", robot.sleep_exit_counter)
    
    # Fast-forward to evolution
    remaining = SLEEP_LOOP_CONFIG['personality_evolution_interval'] - (robot.sleep_exit_counter % SLEEP_LOOP_CONFIG['personality_evolution_interval'])
    print(f"Simulating {remaining} more sleep loop exits...")
    
    for i in range(remaining):
        robot.sleep_exit_counter += 1
        print(f"  Exit #{robot.sleep_exit_counter}")
        
        if robot.sleep_exit_counter % SLEEP_LOOP_CONFIG['personality_evolution_interval'] == 0:
            print("\n🌟 EVOLUTION TRIGGERED! 🌟")
            robot._evolve_personas()
            break
    
    # Chat again after evolution
    print("\n" + "=" * 60)
    print("💬 Chatting after evolution...")
    
    print(f"\n👤 User: How have you changed since we started talking?")
    response = robot.interact_with_persona("alexa", "How have you changed since we started talking?")
    print(f"🤖 Alexa: {response}")
    
    print(f"\n👤 User: What did you learn from our conversation?")
    response = robot.interact_with_persona("jarvis", "What did you learn from our conversation?")
    print(f"🤖 Jarvis: {response}")
    
    # Final status
    print("\n" + "=" * 60)
    robot._print_status()
    
    print("\n✅ Demo complete!")
    print("The personas will continue to evolve with more interactions.")
    print("Their memories and personalities are saved in the ./data/memory/ directory")
    
    # Cleanup
    robot.shutdown()


if __name__ == "__main__":
    demo_conversations()
