#!/usr/bin/env python3
"""
Eidoid Pet Robot - Main Loop with Evolving Persona Memory
Features wake word detection and personality evolution every 7th sleep cycle exit
"""

import os
import sys
import logging
import time
import signal
from typing import Dict, Optional
from datetime import datetime

from persona import EvolvingPersona
from config import (
    GOOGLE_API_KEY,
    SLEEP_LOOP_CONFIG,
    LOG_LEVEL,
    LOG_FILE,
    PERSONAS
)

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class EidoidRobot:
    """
    Main robot controller with evolving AI personas.
    Manages sleep loops and personality evolution.
    """
    
    def __init__(self):
        """Initialize the robot with personas"""
        self.running = False
        self.sleep_exit_counter = 0
        
        # Validate API key
        if not GOOGLE_API_KEY:
            logger.error("GOOGLE_API_KEY not set in environment!")
            raise ValueError("Missing GOOGLE_API_KEY. Set it in your environment.")
        
        # Initialize personas
        logger.info("Initializing personas...")
        self.personas: Dict[str, EvolvingPersona] = {}
        
        try:
            self.personas["alexa"] = EvolvingPersona("alexa", GOOGLE_API_KEY)
            self.personas["jarvis"] = EvolvingPersona("jarvis", GOOGLE_API_KEY)
            logger.info("All personas initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize personas: {e}")
            raise
        
        # Track active persona
        self.active_persona: Optional[str] = None
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        logger.info(f"Received signal {signum}, shutting down...")
        self.shutdown()
        sys.exit(0)
    
    def start(self):
        """Start the main robot loop"""
        self.running = True
        logger.info("=" * 60)
        logger.info("Eidoid Pet Robot Starting")
        logger.info(f"Personas: {', '.join(self.personas.keys())}")
        logger.info(f"Personality evolution interval: every {SLEEP_LOOP_CONFIG['personality_evolution_interval']} sleep exits")
        logger.info("=" * 60)
        
        self._print_status()
        
        # Main loop
        try:
            self._main_loop()
        except KeyboardInterrupt:
            logger.info("Interrupted by user")
        except Exception as e:
            logger.error(f"Unexpected error in main loop: {e}", exc_info=True)
        finally:
            self.shutdown()
    
    def _main_loop(self):
        """
        Main robot loop with sleep cycle tracking.
        Every 7th exit from the sleep loop triggers personality evolution.
        """
        iteration = 0
        
        while self.running:
            iteration += 1
            
            # Sleep loop - this is where the robot "rests" between activities
            self._sleep_loop()
            
            # Increment counter after exiting sleep loop
            self.sleep_exit_counter += 1
            logger.debug(f"Sleep loop exit #{self.sleep_exit_counter}")
            
            # Check if it's time for personality evolution (every 7th exit)
            if self.sleep_exit_counter % SLEEP_LOOP_CONFIG["personality_evolution_interval"] == 0:
                logger.info(f"🧠 EVOLUTION TRIGGER: Sleep exit #{self.sleep_exit_counter}")
                self._evolve_personas()
            
            # Simulate some activity (in real implementation, this would be wake word detection, etc.)
            self._simulate_interaction()
            
            # Check for forced evolution after many iterations
            if iteration >= SLEEP_LOOP_CONFIG["max_loop_iterations"]:
                logger.info("Max iterations reached, triggering evolution")
                self._evolve_personas()
                iteration = 0
    
    def _sleep_loop(self):
        """
        Sleep loop - robot is idle, waiting for wake word.
        In real implementation, this would include:
        - Wake word detection
        - Low-power mode
        - Background monitoring
        """
        sleep_duration = SLEEP_LOOP_CONFIG["sleep_duration_seconds"]
        
        # For demonstration, sleep for configured duration
        # In production, this would be wake word detection
        time.sleep(sleep_duration)
    
    def _evolve_personas(self):
        """Evolve all personas based on their accumulated memories"""
        logger.info("=" * 60)
        logger.info("🌟 PERSONA EVOLUTION BEGINNING 🌟")
        logger.info("=" * 60)
        
        for persona_key, persona in self.personas.items():
            logger.info(f"\nEvolving {persona.name}...")
            
            try:
                evolution_text = persona.evolve_personality()
                logger.info(f"{persona.name} Evolution:")
                logger.info(evolution_text)
                logger.info("-" * 60)
            except Exception as e:
                logger.error(f"Failed to evolve {persona.name}: {e}")
        
        logger.info("=" * 60)
        logger.info("✨ PERSONA EVOLUTION COMPLETE ✨")
        logger.info("=" * 60)
        
        self._print_status()
    
    def _simulate_interaction(self):
        """
        Simulate an interaction for testing.
        In production, this would be replaced with actual wake word detection
        and voice interaction.
        """
        # Add observations to help personas learn
        # This simulates the robot learning from its environment
        
        # Randomly add observations occasionally
        import random
        if random.random() < 0.1:  # 10% chance
            observations = [
                "User seems happy today",
                "Weather is pleasant",
                "User asked about technical topic",
                "Casual conversation about hobbies",
                "User needed help with task",
                "User showed appreciation",
                "Discussion about current events",
                "User shared personal story",
            ]
            
            persona_key = random.choice(list(self.personas.keys()))
            observation = random.choice(observations)
            importance = random.uniform(0.3, 0.8)
            
            self.personas[persona_key].add_observation(observation, importance)
            logger.debug(f"{persona_key} observed: {observation}")
    
    def interact_with_persona(self, persona_key: str, message: str) -> str:
        """
        Have a conversation with a specific persona.
        
        Args:
            persona_key: Which persona to talk to ('alexa' or 'jarvis')
            message: User's message
            
        Returns:
            Persona's response
        """
        if persona_key not in self.personas:
            logger.error(f"Unknown persona: {persona_key}")
            return f"I don't know who {persona_key} is."
        
        self.active_persona = persona_key
        persona = self.personas[persona_key]
        
        logger.info(f"User -> {persona.name}: {message}")
        response = persona.chat(message)
        logger.info(f"{persona.name} -> User: {response}")
        
        return response
    
    def _print_status(self):
        """Print status of all personas"""
        logger.info("\n" + "=" * 60)
        logger.info("PERSONA STATUS")
        logger.info("=" * 60)
        
        for persona_key, persona in self.personas.items():
            status = persona.get_status()
            logger.info(f"\n{status['name']}:")
            logger.info(f"  Voice: {status['voice']}")
            logger.info(f"  Wake Word: '{status['wake_word']}'")
            logger.info(f"  Evolution Count: {status['evolution_count']}")
            logger.info(f"  Total Memories: {status['memory_stats']['total_memories']}")
            logger.info(f"  Avg Memory Importance: {status['memory_stats']['avg_importance']:.2f}")
            if status['memory_stats']['oldest_memory']:
                logger.info(f"  Oldest Memory: {status['memory_stats']['oldest_memory']}")
        
        logger.info(f"\nSleep Exit Counter: {self.sleep_exit_counter}")
        logger.info(f"Next Evolution: {SLEEP_LOOP_CONFIG['personality_evolution_interval'] - (self.sleep_exit_counter % SLEEP_LOOP_CONFIG['personality_evolution_interval'])} exits away")
        logger.info("=" * 60 + "\n")
    
    def shutdown(self):
        """Gracefully shutdown the robot"""
        logger.info("Shutting down Eidoid Robot...")
        self.running = False
        
        # Clean up cached contexts
        for persona in self.personas.values():
            persona.memory.clear_cache()
        
        logger.info("Shutdown complete")


def main():
    """Main entry point"""
    logger.info("Starting Eidoid Pet Robot with Evolving Persona Memory")
    
    try:
        robot = EidoidRobot()
        robot.start()
    except Exception as e:
        logger.error(f"Failed to start robot: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
