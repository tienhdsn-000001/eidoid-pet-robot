# main.py
# Streamlined entry point for Alexa and Jarvis personas

import asyncio
import time
import os
import sys

# Import project modules
import state
from wake_word import run_wake_word_listener
from session_manager import gemini_live_session
from led_controller import led_controller

def main():
    """The main application loop."""
    try:
        # Turn LEDs off at startup
        led_controller.turn_off()
        
        print("[MAIN] Starting Eidoid - Alexa and Jarvis Edition")
        print("[MAIN] Say 'Hey Jarvis' or 'Alexa' to wake me up")
        print("[MAIN] Say 'Thank you for your time' to end a conversation")
        
        while True:
            if state.current_state == state.RobotState.SLEEPING:
                # This function blocks until a wake word is detected
                run_wake_word_listener()

            elif state.current_state == state.RobotState.WAKING:
                # Run the main Gemini Live session
                asyncio.run(gemini_live_session())

                # Reset state after session
                print("[MAIN] Session ended. Resetting state...")
                state.reset_session_state()
                state.set_state(state.RobotState.SLEEPING)
                led_controller.turn_off()
                print("[MAIN] State set to SLEEPING. Returning to wake-word listening.")

            # Small sleep to prevent tight loop
            time.sleep(0.05)

    except KeyboardInterrupt:
        print("\n[EXIT] KeyboardInterrupt detected. Shutting down.")
    finally:
        # Cleanup
        led_controller.turn_off()
        state.cleanup_memories()
        print("[MAIN] Cleanup complete. Exiting.")

if __name__ == "__main__":
    # Ensure the API key is set before starting
    if not os.getenv("GOOGLE_API_KEY"):
        print("[ERROR] GOOGLE_API_KEY environment variable not set.")
        print("[ERROR] Please set it with: export GOOGLE_API_KEY=your_api_key")
        sys.exit(1)
    
    # Start the robot
    main()