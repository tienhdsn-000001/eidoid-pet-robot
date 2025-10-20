"""
Main Social Head Script for Eidoid Pet Robot
Integrates voice activation, persona system, and memory evolution
"""

import os
import sys
import time
import threading
import queue
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
import config  # Load environment variables

# Import persona system
from gemini_persona import PersonaSystem

# For voice recognition and TTS (assuming these will be installed)
try:
    import speech_recognition as sr
    import pyttsx3
except ImportError:
    print("Note: speech_recognition and pyttsx3 not installed. Install with:")
    print("pip install SpeechRecognition pyttsx3")
    sr = None
    pyttsx3 = None


class VoiceInterface:
    """Handles voice input/output for the robot"""
    
    def __init__(self):
        self.recognizer = sr.Recognizer() if sr else None
        self.microphone = sr.Microphone() if sr else None
        self.tts_engine = pyttsx3.init() if pyttsx3 else None
        
        # Configure TTS voices for personas
        if self.tts_engine:
            voices = self.tts_engine.getProperty('voices')
            self.voice_map = {
                "Alexa": voices[1].id if len(voices) > 1 else voices[0].id,  # Female voice
                "Jarvis": voices[0].id  # Male voice
            }
            
    def listen_for_wake_word(self, timeout: float = 1.0) -> Optional[str]:
        """Listen for wake words (Alexa or Hey Jarvis)"""
        if not self.recognizer or not self.microphone:
            return None
            
        try:
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=3)
                
            text = self.recognizer.recognize_google(audio).lower()
            
            if "alexa" in text:
                return "Alexa"
            elif "hey jarvis" in text or "jarvis" in text:
                return "Jarvis"
            elif "what's the weather" in text:
                return "Weather"
                
        except (sr.WaitTimeoutError, sr.UnknownValueError):
            pass
        except Exception as e:
            print(f"Voice recognition error: {e}")
            
        return None
        
    def listen_for_command(self, timeout: float = 5.0) -> Optional[str]:
        """Listen for user command after wake word"""
        if not self.recognizer or not self.microphone:
            return None
            
        try:
            with self.microphone as source:
                print("Listening for command...")
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=10)
                
            text = self.recognizer.recognize_google(audio)
            return text
            
        except (sr.WaitTimeoutError, sr.UnknownValueError):
            return None
        except Exception as e:
            print(f"Command recognition error: {e}")
            return None
            
    def speak(self, text: str, persona: str = "Alexa"):
        """Speak text using persona-specific voice"""
        if not self.tts_engine:
            print(f"{persona}: {text}")
            return
            
        # Set voice for persona
        if persona in self.voice_map:
            self.tts_engine.setProperty('voice', self.voice_map[persona])
            
        # Adjust speech rate for Pi performance
        self.tts_engine.setProperty('rate', 150)
        
        self.tts_engine.say(text)
        self.tts_engine.runAndWait()


class SocialHead:
    """Main controller for the social robot head"""
    
    def __init__(self):
        self.persona_system = PersonaSystem()
        self.voice_interface = VoiceInterface()
        self.running = True
        self.sleep_mode = True
        self.sleep_exit_count = 0
        
        # Queue for handling commands
        self.command_queue = queue.Queue()
        
        # Load configuration
        self.config_file = Path("robot_config.json")
        self.load_config()
        
    def load_config(self):
        """Load robot configuration"""
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                self.config = json.load(f)
        else:
            self.config = {
                "sleep_timeout": 30,  # Seconds before entering sleep
                "evolution_interval": 7,  # Sleep exits before evolution
                "voice_enabled": True,
                "save_interval": 300  # Save memories every 5 minutes
            }
            self.save_config()
            
    def save_config(self):
        """Save robot configuration"""
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)
            
    def run(self):
        """Main robot loop"""
        print("Eidoid Pet Robot Starting...")
        print("Say 'Alexa' or 'Hey Jarvis' to activate")
        
        last_interaction = time.time()
        last_save = time.time()
        
        while self.running:
            try:
                current_time = time.time()
                
                # Save memories periodically
                if current_time - last_save > self.config["save_interval"]:
                    self.persona_system.save_all_memories()
                    last_save = current_time
                
                if self.sleep_mode:
                    # Sleep mode - listen for wake words
                    wake_word = self.voice_interface.listen_for_wake_word(timeout=1.0)
                    
                    if wake_word:
                        self.handle_wake_word(wake_word)
                        last_interaction = current_time
                        
                else:
                    # Active mode - check for timeout
                    if current_time - last_interaction > self.config["sleep_timeout"]:
                        self.enter_sleep_mode()
                    else:
                        # Process any queued commands
                        try:
                            command = self.command_queue.get(timeout=0.1)
                            self.process_command(command)
                            last_interaction = current_time
                        except queue.Empty:
                            pass
                            
            except KeyboardInterrupt:
                print("\nShutting down...")
                self.running = False
            except Exception as e:
                print(f"Error in main loop: {e}")
                
        # Cleanup
        self.persona_system.save_all_memories()
        print("Robot shutdown complete")
        
    def handle_wake_word(self, wake_word: str):
        """Handle wake word detection"""
        if wake_word in ["Alexa", "Jarvis"]:
            # Exit sleep mode
            self.exit_sleep_mode()
            
            # Activate persona
            self.persona_system.activate_persona(wake_word)
            
            # Acknowledge
            self.voice_interface.speak(
                f"{wake_word} here. How can I help you?",
                persona=wake_word
            )
            
            # Listen for command
            command = self.voice_interface.listen_for_command()
            if command:
                self.process_command({
                    "type": "voice_command",
                    "text": command,
                    "persona": wake_word
                })
            else:
                self.voice_interface.speak(
                    "I didn't catch that. Please try again.",
                    persona=wake_word
                )
                
        elif wake_word == "Weather":
            # Special weather command
            self.handle_weather_command()
            
    def exit_sleep_mode(self):
        """Exit sleep mode and handle persona evolution"""
        if self.sleep_mode:
            self.sleep_mode = False
            self.sleep_exit_count += 1
            
            print(f"Exiting sleep mode (Exit #{self.sleep_exit_count})")
            
            # Trigger persona evolution every 7th exit
            if self.sleep_exit_count % self.config["evolution_interval"] == 0:
                print("Triggering persona evolution...")
                self.persona_system.on_sleep_exit()
                
                # Get and display evolution stats
                stats = self.persona_system.get_system_stats()
                for persona_name, persona_stats in stats["personas"].items():
                    traits = persona_stats.get("personality_traits", {})
                    if traits:
                        print(f"{persona_name} evolved - Interests: {traits.get('interests', [])}")
                        
    def enter_sleep_mode(self):
        """Enter sleep mode"""
        if not self.sleep_mode:
            self.sleep_mode = True
            print("Entering sleep mode...")
            
            # Say goodbye with active persona
            if self.persona_system.active_persona:
                self.voice_interface.speak(
                    "Going to sleep now. Wake me when you need me.",
                    persona=self.persona_system.active_persona
                )
                
    def process_command(self, command: Dict[str, Any]):
        """Process a command"""
        command_type = command.get("type")
        
        if command_type == "voice_command":
            text = command.get("text", "")
            persona = command.get("persona", self.persona_system.active_persona)
            
            # Generate response using persona system
            response_data = self.persona_system.process_input(text)
            
            if "error" not in response_data:
                # Speak response
                self.voice_interface.speak(
                    response_data["response"],
                    persona=persona
                )
                
                # Log interaction
                print(f"User: {text}")
                print(f"{persona}: {response_data['response']}")
                print(f"Emotion: {response_data.get('emotion', 'neutral')}")
                
    def handle_weather_command(self):
        """Handle special weather command"""
        # For now, provide a simple response
        # In production, would integrate with weather API
        
        self.exit_sleep_mode()
        
        # Use a random persona
        import random
        persona = random.choice(["Alexa", "Jarvis"])
        self.persona_system.activate_persona(persona)
        
        # Generate weather response
        weather_input = "What's the weather like today?"
        response_data = self.persona_system.process_input(weather_input)
        
        self.voice_interface.speak(
            response_data["response"],
            persona=persona
        )
        
        # Ask for character description
        self.voice_interface.speak(
            "By the way, can you describe a character you'd like me to embody?",
            persona=persona
        )
        
        # Listen for character description
        description = self.voice_interface.listen_for_command()
        if description:
            # Process character description
            response_data = self.persona_system.process_input(
                f"I'd like you to embody this character: {description}"
            )
            self.voice_interface.speak(
                response_data["response"],
                persona=persona
            )


def main():
    """Main entry point"""
    # Check for required environment variables
    if not os.getenv("GEMINI_API_KEY"):
        print("Warning: GEMINI_API_KEY not set. Please set it to use Gemini API.")
        print("export GEMINI_API_KEY='your-api-key'")
        
    # Create and run social head
    robot = SocialHead()
    
    try:
        robot.run()
    except Exception as e:
        print(f"Fatal error: {e}")
        robot.persona_system.save_all_memories()


if __name__ == "__main__":
    main()