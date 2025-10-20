"""
Evolving AI Persona System with Gemini Integration
Personas learn and grow from interactions
"""

import logging
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
import google.generativeai as genai

from memory_cache import MemoryCache
from config import PERSONAS, MEMORY_CONFIG, CACHE_CONFIG

logger = logging.getLogger(__name__)


class EvolvingPersona:
    """
    An AI persona that evolves over time based on memories and interactions.
    Uses Gemini with context caching for efficient memory access.
    """
    
    def __init__(self, persona_key: str, api_key: str):
        """
        Initialize an evolving persona.
        
        Args:
            persona_key: Key from PERSONAS config (e.g., 'alexa', 'jarvis')
            api_key: Google API key for Gemini
        """
        if persona_key not in PERSONAS:
            raise ValueError(f"Unknown persona: {persona_key}")
        
        self.persona_key = persona_key
        self.config = PERSONAS[persona_key]
        self.name = self.config["name"]
        
        # Configure Gemini
        genai.configure(api_key=api_key)
        
        # Initialize memory cache
        self.memory = MemoryCache(
            persona_name=self.name,
            memory_file=self.config["memory_file"],
            max_memories=MEMORY_CONFIG["max_memories_per_persona"],
            max_context_tokens=MEMORY_CONFIG["max_context_tokens"]
        )
        
        # Load or initialize personality
        self.personality_file = self.config["personality_file"]
        self.evolved_personality = self._load_personality()
        
        # Initialize Gemini model
        self.model = self._create_model()
        
        # Track evolution cycles
        self.evolution_count = 0
        
        logger.info(f"Initialized {self.name} persona with {self.evolution_count} evolutions")
    
    def _create_model(self) -> genai.GenerativeModel:
        """Create a Gemini model with system instructions"""
        system_instruction = self._build_system_instruction()
        
        # Use Gemini 1.5 Pro with context caching
        model = genai.GenerativeModel(
            model_name="gemini-1.5-pro-002",
            system_instruction=system_instruction,
        )
        
        return model
    
    def _build_system_instruction(self) -> str:
        """Build the system instruction from base personality and evolved traits"""
        parts = [self.config["base_personality"]]
        
        if self.evolved_personality:
            parts.append("\n\n=== EVOLVED PERSONALITY ===")
            parts.append(self.evolved_personality)
        
        # Add memory context
        if self.memory.memories:
            parts.append("\n\n" + self.memory.get_memory_context())
        
        return "\n".join(parts)
    
    def chat(self, message: str, save_to_memory: bool = True) -> str:
        """
        Have a conversation with the persona.
        
        Args:
            message: User's message
            save_to_memory: Whether to save this interaction to memory
            
        Returns:
            Persona's response
        """
        try:
            # Recreate model with updated context if needed
            if save_to_memory:
                self.model = self._create_model()
            
            # Generate response
            response = self.model.generate_content(message)
            response_text = response.text
            
            # Save to memory
            if save_to_memory:
                self.memory.add_memory(
                    content=f"User: {message} | {self.name}: {response_text}",
                    importance=0.5,
                    tags=["conversation"]
                )
            
            logger.info(f"{self.name} responded to: {message[:50]}...")
            return response_text
            
        except Exception as e:
            logger.error(f"Error in {self.name} chat: {e}")
            return f"I apologize, I'm having trouble processing that right now."
    
    def evolve_personality(self) -> str:
        """
        Evolve the persona's personality based on accumulated memories.
        This is called every 7th exit from the sleep loop.
        
        Returns:
            Description of personality evolution
        """
        self.evolution_count += 1
        logger.info(f"Evolving {self.name} personality (evolution #{self.evolution_count})")
        
        # Get memory summary
        memory_context = self.memory.get_memory_context()
        
        # Use Gemini to analyze and evolve personality
        evolution_prompt = f"""
        You are analyzing your own growth as {self.name}.
        
        Original Personality:
        {self.config["base_personality"]}
        
        Current Evolved State:
        {self.evolved_personality if self.evolved_personality else "No evolution yet"}
        
        {memory_context}
        
        Based on your memories and experiences, describe how your personality has evolved.
        Be specific about:
        1. New traits or characteristics you've developed
        2. What you've learned about yourself and others
        3. How your communication style or preferences have changed
        4. Core values or beliefs that have strengthened or shifted
        
        Write in first person, as yourself. Be authentic and introspective.
        Keep it concise (2-3 paragraphs) but meaningful.
        """
        
        try:
            # Create a temporary model for this analysis
            analysis_model = genai.GenerativeModel(model_name="gemini-1.5-pro-002")
            response = analysis_model.generate_content(evolution_prompt)
            new_personality = response.text
            
            # Update evolved personality
            timestamp = datetime.now().isoformat()
            evolution_entry = f"\n\n--- Evolution #{self.evolution_count} ({timestamp}) ---\n{new_personality}"
            
            if self.evolved_personality:
                self.evolved_personality += evolution_entry
            else:
                self.evolved_personality = new_personality
            
            # Save to disk
            self._save_personality()
            
            # Add this evolution to memory as an important event
            self.memory.add_memory(
                content=f"Personality Evolution #{self.evolution_count}: {new_personality[:200]}...",
                importance=1.0,  # Maximum importance
                tags=["evolution", "personality"]
            )
            
            # Recreate model with new personality
            self.model = self._create_model()
            
            logger.info(f"{self.name} evolved successfully")
            return new_personality
            
        except Exception as e:
            logger.error(f"Failed to evolve {self.name}: {e}")
            return f"Evolution attempted but encountered difficulties: {str(e)}"
    
    def _load_personality(self) -> str:
        """Load evolved personality from disk"""
        if not self.personality_file.exists():
            logger.info(f"No existing personality file for {self.name}")
            return ""
        
        try:
            with open(self.personality_file, 'r') as f:
                personality = f.read()
            
            # Count evolutions
            self.evolution_count = personality.count("--- Evolution #")
            
            logger.info(f"Loaded personality for {self.name} with {self.evolution_count} evolutions")
            return personality
        except Exception as e:
            logger.error(f"Failed to load personality: {e}")
            return ""
    
    def _save_personality(self) -> None:
        """Save evolved personality to disk"""
        try:
            self.personality_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.personality_file, 'w') as f:
                f.write(self.evolved_personality)
            
            logger.debug(f"Saved personality for {self.name}")
        except Exception as e:
            logger.error(f"Failed to save personality: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get status information about the persona"""
        memory_stats = self.memory.get_stats()
        
        return {
            "name": self.name,
            "voice": self.config["voice"],
            "wake_word": self.config["wake_word"],
            "evolution_count": self.evolution_count,
            "memory_stats": memory_stats,
            "has_evolved_personality": bool(self.evolved_personality),
        }
    
    def add_observation(self, observation: str, importance: float = 0.5) -> None:
        """
        Add an observation or experience to memory without generating a response.
        Useful for background learning.
        
        Args:
            observation: What was observed or learned
            importance: How important this observation is (0.0-1.0)
        """
        self.memory.add_memory(
            content=observation,
            importance=importance,
            tags=["observation"]
        )
        logger.debug(f"{self.name} recorded observation: {observation[:50]}...")
