"""
Persona Memory Cache System for Eidoid Pet Robot
Implements evolving memory for Alexa and Jarvis personas
Optimized for Raspberry Pi 5 constraints
"""

import json
import os
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from collections import deque
import pickle
import threading
from pathlib import Path


class MemoryCache:
    """
    Memory cache implementation optimized for Raspberry Pi 5
    Uses deque for efficient memory management with fixed size
    """
    
    def __init__(self, persona_name: str, max_memories: int = 1000, 
                 max_context_size: int = 5000):
        """
        Initialize memory cache for a specific persona
        
        Args:
            persona_name: Name of the persona (Alexa or Jarvis)
            max_memories: Maximum number of memory entries to store
            max_context_size: Maximum size of context in tokens (approximate)
        """
        self.persona_name = persona_name
        self.max_memories = max_memories
        self.max_context_size = max_context_size
        
        # Use deque for efficient memory management
        self.short_term_memory = deque(maxlen=100)  # Recent interactions
        self.long_term_memory = deque(maxlen=max_memories)  # Persistent memories
        self.personality_traits = {}  # Evolving personality characteristics
        
        # File paths for persistence
        self.memory_dir = Path("persona_memories")
        self.memory_dir.mkdir(exist_ok=True)
        self.memory_file = self.memory_dir / f"{persona_name.lower()}_memory.pkl"
        self.traits_file = self.memory_dir / f"{persona_name.lower()}_traits.json"
        
        # Thread safety
        self.lock = threading.Lock()
        
        # Load existing memories if available
        self.load_memories()
        
    def add_interaction(self, user_input: str, response: str, 
                       emotion: Optional[str] = None, context: Optional[Dict] = None):
        """
        Add a new interaction to memory
        
        Args:
            user_input: What the user said
            response: How the persona responded
            emotion: Optional emotion tag
            context: Optional context dictionary
        """
        with self.lock:
            memory_entry = {
                "timestamp": datetime.now().isoformat(),
                "user_input": user_input,
                "response": response,
                "emotion": emotion,
                "context": context or {},
                "interaction_count": len(self.short_term_memory) + len(self.long_term_memory)
            }
            
            # Add to short-term memory
            self.short_term_memory.append(memory_entry)
            
            # Promote important memories to long-term
            if self._is_significant_memory(memory_entry):
                self.long_term_memory.append(memory_entry)
                
    def _is_significant_memory(self, memory: Dict) -> bool:
        """
        Determine if a memory should be promoted to long-term storage
        """
        # Criteria for significance:
        # 1. Strong emotional content
        # 2. Personal information about user
        # 3. Important events or milestones
        
        if memory.get("emotion") in ["joy", "sadness", "surprise", "anger"]:
            return True
            
        # Check for personal information keywords
        personal_keywords = ["name", "birthday", "favorite", "like", "love", "hate", 
                           "family", "friend", "pet", "job", "home"]
        text = (memory.get("user_input", "") + " " + memory.get("response", "")).lower()
        
        return any(keyword in text for keyword in personal_keywords)
        
    def get_context_for_generation(self, current_input: str) -> str:
        """
        Get relevant context for generating responses
        Optimized for Gemini API context window
        """
        with self.lock:
            context_parts = []
            
            # Add personality traits
            if self.personality_traits:
                traits_str = f"Personality traits: {json.dumps(self.personality_traits)}"
                context_parts.append(traits_str)
            
            # Add recent short-term memories
            recent_memories = list(self.short_term_memory)[-10:]  # Last 10 interactions
            if recent_memories:
                recent_str = "Recent interactions:\n"
                for mem in recent_memories:
                    recent_str += f"- User: {mem['user_input']}\n"
                    recent_str += f"  {self.persona_name}: {mem['response']}\n"
                context_parts.append(recent_str)
            
            # Add relevant long-term memories
            relevant_memories = self._find_relevant_memories(current_input, limit=5)
            if relevant_memories:
                relevant_str = "Relevant past memories:\n"
                for mem in relevant_memories:
                    relevant_str += f"- {mem['timestamp']}: {mem['user_input']} -> {mem['response']}\n"
                context_parts.append(relevant_str)
            
            return "\n\n".join(context_parts)
            
    def _find_relevant_memories(self, query: str, limit: int = 5) -> List[Dict]:
        """
        Find memories relevant to the current query
        Simple keyword-based search optimized for Pi performance
        """
        query_words = set(query.lower().split())
        scored_memories = []
        
        for memory in self.long_term_memory:
            memory_text = (memory.get("user_input", "") + " " + 
                          memory.get("response", "")).lower()
            memory_words = set(memory_text.split())
            
            # Simple relevance score based on word overlap
            score = len(query_words.intersection(memory_words))
            if score > 0:
                scored_memories.append((score, memory))
        
        # Sort by relevance and return top memories
        scored_memories.sort(key=lambda x: x[0], reverse=True)
        return [mem for _, mem in scored_memories[:limit]]
        
    def evolve_personality(self, interaction_summary: Dict[str, Any]):
        """
        Evolve personality traits based on interactions
        Called every 7th sleep loop exit
        """
        with self.lock:
            # Analyze recent interactions for personality evolution
            emotions_count = {}
            topics_count = {}
            
            for memory in list(self.short_term_memory) + list(self.long_term_memory)[-50:]:
                # Count emotions
                emotion = memory.get("emotion")
                if emotion:
                    emotions_count[emotion] = emotions_count.get(emotion, 0) + 1
                
                # Extract topics (simple keyword extraction)
                text = (memory.get("user_input", "") + " " + memory.get("response", ""))
                for word in text.lower().split():
                    if len(word) > 5:  # Simple topic extraction
                        topics_count[word] = topics_count.get(word, 0) + 1
            
            # Update personality traits
            if emotions_count:
                dominant_emotion = max(emotions_count.items(), key=lambda x: x[1])[0]
                self.personality_traits["dominant_emotion"] = dominant_emotion
                
            if topics_count:
                top_topics = sorted(topics_count.items(), key=lambda x: x[1], reverse=True)[:5]
                self.personality_traits["interests"] = [topic for topic, _ in top_topics]
            
            # Add evolution timestamp
            self.personality_traits["last_evolution"] = datetime.now().isoformat()
            self.personality_traits["evolution_count"] = self.personality_traits.get("evolution_count", 0) + 1
            
            # Save updated traits
            self.save_memories()
            
    def save_memories(self):
        """Save memories and traits to disk"""
        with self.lock:
            # Save memory cache
            memory_data = {
                "short_term": list(self.short_term_memory),
                "long_term": list(self.long_term_memory),
                "saved_at": datetime.now().isoformat()
            }
            
            with open(self.memory_file, 'wb') as f:
                pickle.dump(memory_data, f)
            
            # Save personality traits
            with open(self.traits_file, 'w') as f:
                json.dump(self.personality_traits, f, indent=2)
                
    def load_memories(self):
        """Load memories and traits from disk"""
        with self.lock:
            # Load memory cache
            if self.memory_file.exists():
                try:
                    with open(self.memory_file, 'rb') as f:
                        memory_data = pickle.load(f)
                        
                    # Restore memories
                    self.short_term_memory.extend(memory_data.get("short_term", [])[-100:])
                    self.long_term_memory.extend(memory_data.get("long_term", [])[-self.max_memories:])
                except Exception as e:
                    print(f"Error loading memories for {self.persona_name}: {e}")
            
            # Load personality traits
            if self.traits_file.exists():
                try:
                    with open(self.traits_file, 'r') as f:
                        self.personality_traits = json.load(f)
                except Exception as e:
                    print(f"Error loading traits for {self.persona_name}: {e}")
                    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get statistics about the memory cache"""
        with self.lock:
            return {
                "persona": self.persona_name,
                "short_term_count": len(self.short_term_memory),
                "long_term_count": len(self.long_term_memory),
                "personality_traits": self.personality_traits,
                "total_interactions": len(self.short_term_memory) + len(self.long_term_memory)
            }


class PersonaMemoryManager:
    """
    Manages memory caches for multiple personas
    """
    
    def __init__(self):
        self.personas = {}
        self.sleep_exit_count = 0
        self.evolution_interval = 7  # Evolve every 7th sleep exit
        
    def initialize_persona(self, persona_name: str, max_memories: int = 1000):
        """Initialize a persona with memory cache"""
        if persona_name not in self.personas:
            self.personas[persona_name] = MemoryCache(
                persona_name=persona_name,
                max_memories=max_memories
            )
            print(f"Initialized memory cache for {persona_name}")
            
    def get_persona_memory(self, persona_name: str) -> Optional[MemoryCache]:
        """Get memory cache for a specific persona"""
        return self.personas.get(persona_name)
        
    def on_sleep_exit(self):
        """
        Called when exiting sleep loop
        Handles personality evolution every 7th exit
        """
        self.sleep_exit_count += 1
        
        if self.sleep_exit_count % self.evolution_interval == 0:
            print(f"Sleep exit #{self.sleep_exit_count} - Evolving personas...")
            
            for persona_name, memory_cache in self.personas.items():
                # Create interaction summary for evolution
                stats = memory_cache.get_memory_stats()
                interaction_summary = {
                    "total_interactions": stats["total_interactions"],
                    "recent_interaction_count": len(memory_cache.short_term_memory)
                }
                
                # Evolve the personality
                memory_cache.evolve_personality(interaction_summary)
                print(f"Evolved {persona_name} personality - Evolution #{stats['personality_traits'].get('evolution_count', 0)}")
                
    def save_all_memories(self):
        """Save all persona memories"""
        for persona_name, memory_cache in self.personas.items():
            memory_cache.save_memories()
            print(f"Saved memories for {persona_name}")


# Example usage
if __name__ == "__main__":
    # Initialize memory manager
    memory_manager = PersonaMemoryManager()
    
    # Initialize Alexa and Jarvis personas
    memory_manager.initialize_persona("Alexa", max_memories=1000)
    memory_manager.initialize_persona("Jarvis", max_memories=1000)
    
    # Example interaction
    alexa_memory = memory_manager.get_persona_memory("Alexa")
    if alexa_memory:
        alexa_memory.add_interaction(
            user_input="What's the weather today?",
            response="It's sunny with a high of 72 degrees. Perfect day for a walk!",
            emotion="cheerful"
        )
        
        # Get context for next generation
        context = alexa_memory.get_context_for_generation("Tell me about the weather")
        print("Context for generation:", context)
        
    # Simulate sleep exits
    for i in range(14):
        print(f"\nSleep exit {i+1}")
        memory_manager.on_sleep_exit()
        time.sleep(0.1)  # Small delay for demonstration