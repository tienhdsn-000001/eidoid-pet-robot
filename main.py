# main.py
# Main entry point for the Eidoid Pet Robot.

import asyncio
import time
import os
import sys

# Import project modules
import state
from wake_word import run_wake_word_listener
from session_manager import gemini_live_session
# --- DEPRECATED: Motor functions are temporarily disabled ---
# from services import serial_mgr
# --- NEW: Import the LED controller ---
from led_controller import led_controller


def main():
    """The main application loop."""
    try:
        # --- NEW: Turn LEDs off at startup just in case ---
        led_controller.turn_off()
        while True:
            if state.current_state == state.RobotState.SLEEPING:
                # This function blocks until a wake word is detected.
                # It will modify the global state when it exits.
                run_wake_word_listener()

            elif state.current_state == state.RobotState.WAKING:
                # The state was changed by the wake word listener.
                # Now, we run the main Gemini Live session.
                asyncio.run(gemini_live_session())

                # --- MODIFIED: Added more explicit logging and re-ordered state reset ---
                # This is the requested fix to ensure a clean return to the sleep loop.
                print("[MAIN] Session ended. Resetting state...")
                # It's slightly cleaner to reset session-specific data first...
                state.reset_session_state()
                # ...and then set the main robot state back to sleeping.
                state.set_state(state.RobotState.SLEEPING)
                # --- NEW: Turn off LEDs when going to sleep ---
                led_controller.turn_off()
                print("[MAIN] State set to SLEEPING. Returning to wake-word listening.")


            # A small sleep to prevent a tight loop if something unexpected happens.
            time.sleep(0.05)

    except KeyboardInterrupt:
        print("\n[EXIT] KeyboardInterrupt detected. Shutting down.")
    finally:
        # Ensure any hardware connections are cleanly closed.
        # --- DEPRECATED: Motor functions are temporarily disabled ---
        # serial_mgr.close()
        # --- NEW: Ensure LEDs are off on exit ---
        led_controller.turn_off()
        # Save all memories before exit
        state.cleanup_memories()
        print("[MAIN] Cleanup complete. Exiting.")

if __name__ == "__main__":
    # Ensure the API key is set before starting.
    if not os.getenv("GOOGLE_API_KEY"):
        print("[ERROR] GOOGLE_API_KEY environment variable not set.")
        sys.exit(1)
    
    # Start the robot.
    main()

