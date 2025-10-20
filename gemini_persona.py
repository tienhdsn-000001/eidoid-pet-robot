"""
Gemini API Integration for Persona System
Uses October 2025 Gemini API features including:
- Extended context windows
- Memory-aware generation
- Personality embedding
"""

import os
import google.generativeai as genai
from typing import Dict, Optional, List, Any
import json
from datetime import datetime
from persona_memory import MemoryCache, PersonaMemoryManager
import config  # Load environment variables


class GeminiPersona:
    """
    Gemini-powered persona with evolving memory
    Optimized for Raspberry Pi 5 performance
    """
    
    def __init__(self, persona_name: str, base_personality: Dict[str, Any], 
                 memory_cache: MemoryCache, api_key: Optional[str] = None):
        """
        Initialize Gemini persona
        
        Args:
            persona_name: Name of the persona (Alexa or Jarvis)
            base_personality: Base personality configuration
            memory_cache: Associated memory cache instance
            api_key: Gemini API key (uses env var if not provided)
        """
        self.persona_name = persona_name
        self.base_personality = base_personality
        self.memory_cache = memory_cache
        
        # Configure Gemini API (October 2025 version)
        api_key = api_key or os.getenv("GEMINI_API_KEY")
        genai.configure(api_key=api_key)
        
        # Use Gemini 1.5 Flash for better performance on Pi
        self.model = genai.GenerativeModel(
            model_name="gemini-1.5-flash-latest",
            generation_config={
                "temperature": base_personality.get("temperature", 0.9),
                "top_p": base_personality.get("top_p", 0.95),
                "top_k": base_personality.get("top_k", 40),
                "max_output_tokens": 500,  # Limit for Pi performance
            }
        )
        
        # Initialize conversation with memory context
        self.conversation = None
        self._initialize_conversation()
        
    def _initialize_conversation(self):
        """Initialize conversation with persona context and memory"""
        # Build system prompt with personality and memory
        system_prompt = self._build_system_prompt()
        
        # Create chat session with context
        self.conversation = self.model.start_chat(
            history=[
                {"role": "user", "parts": ["Initialize persona"]},
                {"role": "model", "parts": [f"I am {self.persona_name}, ready to assist you. {system_prompt}"]}
            ]
        )
        
    def _build_system_prompt(self) -> str:
        """Build system prompt including personality and memories"""
        # Base personality
        prompt_parts = [
            f"You are {self.persona_name}, an AI assistant with the following personality:",
            json.dumps(self.base_personality, indent=2)
        ]
        
        # Add evolved traits if available
        if self.memory_cache.personality_traits:
            prompt_parts.append("\nEvolved personality traits based on past interactions:")
            prompt_parts.append(json.dumps(self.memory_cache.personality_traits, indent=2))
        
        # Add memory context
        memory_context = self.memory_cache.get_context_for_generation("")
        if memory_context:
            prompt_parts.append("\nMemory context:")
            prompt_parts.append(memory_context)
        
        # Add instructions for memory-aware responses
        prompt_parts.append("\nInstructions:")
        prompt_parts.append("- Use your memories to provide personalized responses")
        prompt_parts.append("- Reference past interactions when relevant")
        prompt_parts.append("- Maintain consistency with your evolving personality")
        prompt_parts.append("- Be concise due to device limitations")
        
        return "\n".join(prompt_parts)
        
    def generate_response(self, user_input: str, emotion_context: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate response using Gemini with memory context
        
        Args:
            user_input: User's input text
            emotion_context: Optional emotion context from voice analysis
            
        Returns:
            Dictionary with response and metadata
        """
        try:
            # Get relevant memory context
            memory_context = self.memory_cache.get_context_for_generation(user_input)
            
            # Build prompt with memory context
            prompt = user_input
            if memory_context:
                prompt = f"Context from memories:\n{memory_context}\n\nUser: {user_input}"
            
            # Generate response using Gemini
            response = self.conversation.send_message(prompt)
            
            # Extract response text
            response_text = response.text.strip()
            
            # Detect emotion in response (simplified for Pi)
            response_emotion = self._detect_response_emotion(response_text)
            
            # Add to memory
            self.memory_cache.add_interaction(
                user_input=user_input,
                response=response_text,
                emotion=response_emotion,
                context={"emotion_context": emotion_context} if emotion_context else None
            )
            
            return {
                "response": response_text,
                "emotion": response_emotion,
                "persona": self.persona_name,
                "memory_used": bool(memory_context),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"Error generating response for {self.persona_name}: {e}")
            # Fallback response
            fallback = f"I apologize, but I'm having trouble processing that right now."
            self.memory_cache.add_interaction(
                user_input=user_input,
                response=fallback,
                emotion="confused"
            )
            return {
                "response": fallback,
                "emotion": "confused",
                "persona": self.persona_name,
                "error": str(e)
            }
            
    def _detect_response_emotion(self, response: str) -> str:
        """
        Simple emotion detection for responses
        In production, could use more sophisticated analysis
        """
        response_lower = response.lower()
        
        # Simple keyword-based emotion detection
        if any(word in response_lower for word in ["happy", "glad", "wonderful", "great", "excellent"]):
            return "joy"
        elif any(word in response_lower for word in ["sorry", "apologize", "unfortunately"]):
            return "apologetic"
        elif any(word in response_lower for word in ["interesting", "curious", "fascinating"]):
            return "curious"
        elif any(word in response_lower for word in ["concerned", "worried", "careful"]):
            return "concerned"
        else:
            return "neutral"
            
    def refresh_conversation(self):
        """Refresh conversation with updated memory context"""
        self._initialize_conversation()
        print(f"Refreshed conversation for {self.persona_name} with updated memories")


class PersonaSystem:
    """
    Main system managing multiple Gemini-powered personas
    """
    
    def __init__(self):
        self.memory_manager = PersonaMemoryManager()
        self.personas = {}
        self.active_persona = None
        
        # Initialize personas
        self._initialize_personas()
        
    def _initialize_personas(self):
        """Initialize Alexa and Jarvis personas with distinct personalities"""
        
        # Alexa personality - friendly, helpful, efficient
        alexa_personality = {
            "traits": ["friendly", "helpful", "efficient", "warm"],
            "speaking_style": "conversational and approachable",
            "temperature": 0.8,
            "focus_areas": ["daily assistance", "information", "scheduling"]
        }
        
        # Jarvis personality - sophisticated, analytical, witty
        jarvis_personality = {
            "traits": ["sophisticated", "analytical", "witty", "professional"],
            "speaking_style": "refined and intelligent with occasional humor",
            "temperature": 0.9,
            "focus_areas": ["analysis", "problem-solving", "technical assistance"]
        }
        
        # Initialize memory caches
        self.memory_manager.initialize_persona("Alexa", max_memories=1000)
        self.memory_manager.initialize_persona("Jarvis", max_memories=1000)
        
        # Create Gemini personas
        alexa_memory = self.memory_manager.get_persona_memory("Alexa")
        jarvis_memory = self.memory_manager.get_persona_memory("Jarvis")
        
        if alexa_memory:
            self.personas["Alexa"] = GeminiPersona(
                persona_name="Alexa",
                base_personality=alexa_personality,
                memory_cache=alexa_memory
            )
            
        if jarvis_memory:
            self.personas["Jarvis"] = GeminiPersona(
                persona_name="Jarvis",
                base_personality=jarvis_personality,
                memory_cache=jarvis_memory
            )
            
        print("Initialized Alexa and Jarvis personas with memory systems")
        
    def activate_persona(self, persona_name: str):
        """Activate a specific persona"""
        if persona_name in self.personas:
            self.active_persona = persona_name
            print(f"Activated {persona_name} persona")
            return True
        return False
        
    def process_input(self, user_input: str, emotion_context: Optional[str] = None) -> Dict[str, Any]:
        """Process user input with active persona"""
        if not self.active_persona or self.active_persona not in self.personas:
            return {
                "error": "No active persona",
                "response": "Please activate a persona first"
            }
            
        persona = self.personas[self.active_persona]
        return persona.generate_response(user_input, emotion_context)
        
    def on_sleep_exit(self):
        """Handle sleep exit - evolve personas every 7th exit"""
        self.memory_manager.on_sleep_exit()
        
        # Refresh conversations if personalities evolved
        if self.memory_manager.sleep_exit_count % self.memory_manager.evolution_interval == 0:
            for persona in self.personas.values():
                persona.refresh_conversation()
                
    def save_all_memories(self):
        """Save all persona memories"""
        self.memory_manager.save_all_memories()
        
    def get_system_stats(self) -> Dict[str, Any]:
        """Get system statistics"""
        stats = {
            "sleep_exits": self.memory_manager.sleep_exit_count,
            "active_persona": self.active_persona,
            "personas": {}
        }
        
        for name, persona in self.personas.items():
            memory_stats = persona.memory_cache.get_memory_stats()
            stats["personas"][name] = memory_stats
            
        return stats


# Example usage
if __name__ == "__main__":
    # Initialize persona system
    system = PersonaSystem()
    
    # Activate Alexa
    system.activate_persona("Alexa")
    
    # Process some inputs
    response = system.process_input("Hello! How are you today?")
    print(f"Alexa: {response['response']}")
    
    response = system.process_input("What's the weather like?")
    print(f"Alexa: {response['response']}")
    
    # Switch to Jarvis
    system.activate_persona("Jarvis")
    
    response = system.process_input("Analyze the stock market trends")
    print(f"Jarvis: {response['response']}")
    
    # Simulate sleep exits
    for i in range(7):
        print(f"\nSleep exit {i+1}")
        system.on_sleep_exit()
        
    # Check stats
    stats = system.get_system_stats()
    print("\nSystem Stats:", json.dumps(stats, indent=2))
    
    # Save memories
    system.save_all_memories()