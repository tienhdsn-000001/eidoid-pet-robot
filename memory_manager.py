# memory_manager.py
# Manages short-term and long-term memory for each persona,
# enabling personality development and contextual awareness.

import json
import os
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
from collections import deque
from datetime import datetime, timedelta


class PersonaMemory:
    """
    Manages memory for a single persona, including:
    - Short-term memory: Recent conversation context (last N turns)
    - Long-term memory: Important facts, preferences, and personality traits
    - Personality development: Evolving characteristics based on interactions
    """
    
    def __init__(self, persona_key: str, memory_dir: str = ".memory"):
        self.persona_key = persona_key
        self.memory_dir = Path(memory_dir)
        self.memory_file = self.memory_dir / f"{persona_key}_memory.json"
        
        # Short-term memory (conversation buffer)
        self.conversation_buffer = deque(maxlen=12)  # Last 12 turns
        
        # Long-term memory structures
        self.user_facts = []  # Facts learned about the user
        self.interaction_count = 0  # Total interactions
        self.last_interaction = None  # Timestamp of last interaction
        self.personality_traits = {}  # Developing personality characteristics
        self.important_memories = []  # Key memorable moments
        self.preferences = {}  # User preferences learned over time
        
        # Personality development tracking
        self.conversation_topics = {}  # Topics discussed and frequency
        self.emotional_responses = []  # Track emotional tone over time
        self.user_relationship = {
            "familiarity_level": 0,  # 0-100 scale
            "interaction_history": [],  # Timestamps of interactions
            "rapport_indicators": []  # Positive/negative interaction markers
        }
        
        # Load existing memory if available
        self._load_memory()
        
    def _ensure_memory_dir(self):
        """Ensure the memory directory exists."""
        self.memory_dir.mkdir(exist_ok=True)
        
    def _load_memory(self):
        """Load memory from disk if it exists."""
        try:
            if self.memory_file.exists():
                with open(self.memory_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                # Load long-term memory
                self.user_facts = data.get('user_facts', [])
                self.interaction_count = data.get('interaction_count', 0)
                self.last_interaction = data.get('last_interaction')
                self.personality_traits = data.get('personality_traits', {})
                self.important_memories = data.get('important_memories', [])
                self.preferences = data.get('preferences', {})
                self.conversation_topics = data.get('conversation_topics', {})
                self.emotional_responses = data.get('emotional_responses', [])
                self.user_relationship = data.get('user_relationship', {
                    "familiarity_level": 0,
                    "interaction_history": [],
                    "rapport_indicators": []
                })
                
                print(f"[MEMORY] Loaded memory for {self.persona_key}: {self.interaction_count} interactions")
        except Exception as e:
            print(f"[MEMORY] Could not load memory for {self.persona_key}: {e}")
            
    def save_memory(self):
        """Persist memory to disk."""
        try:
            self._ensure_memory_dir()
            
            data = {
                'persona_key': self.persona_key,
                'user_facts': self.user_facts[-100:],  # Keep last 100 facts
                'interaction_count': self.interaction_count,
                'last_interaction': self.last_interaction,
                'personality_traits': self.personality_traits,
                'important_memories': self.important_memories[-50:],  # Keep last 50
                'preferences': self.preferences,
                'conversation_topics': self.conversation_topics,
                'emotional_responses': self.emotional_responses[-100:],  # Keep last 100
                'user_relationship': self.user_relationship
            }
            
            with open(self.memory_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
            print(f"[MEMORY] Saved memory for {self.persona_key}")
        except Exception as e:
            print(f"[MEMORY] Could not save memory for {self.persona_key}: {e}")
            
    def add_conversation_turn(self, role: str, text: str):
        """Add a conversation turn to short-term memory."""
        self.conversation_buffer.append({
            'role': role,
            'text': text,
            'timestamp': time.time()
        })
        
    def record_interaction(self):
        """Record that an interaction occurred."""
        self.interaction_count += 1
        self.last_interaction = datetime.now().isoformat()
        self.user_relationship['interaction_history'].append(self.last_interaction)
        
        # Update familiarity level (increases with interactions)
        # Cap at 100
        self.user_relationship['familiarity_level'] = min(
            100,
            self.user_relationship['familiarity_level'] + 1
        )
        
    def learn_user_fact(self, fact: str, confidence: float = 1.0):
        """
        Store a fact about the user.
        
        Args:
            fact: The fact learned about the user
            confidence: Confidence level (0.0-1.0)
        """
        fact_entry = {
            'fact': fact,
            'learned_at': datetime.now().isoformat(),
            'confidence': confidence,
            'reinforcement_count': 1
        }
        
        # Check if similar fact exists
        fact_lower = fact.lower()
        for existing in self.user_facts:
            if existing['fact'].lower() == fact_lower:
                existing['reinforcement_count'] += 1
                existing['confidence'] = min(1.0, existing['confidence'] + 0.1)
                return
                
        self.user_facts.append(fact_entry)
        
    def add_important_memory(self, memory: str, emotional_weight: float = 0.5):
        """
        Store an important memory with emotional weight.
        
        Args:
            memory: Description of the memorable moment
            emotional_weight: Emotional significance (0.0-1.0)
        """
        memory_entry = {
            'memory': memory,
            'timestamp': datetime.now().isoformat(),
            'emotional_weight': emotional_weight
        }
        self.important_memories.append(memory_entry)
        
    def update_preference(self, category: str, preference: str):
        """
        Update a user preference.
        
        Args:
            category: Category of preference (e.g., 'music', 'topics', 'interaction_style')
            preference: The preference value
        """
        if category not in self.preferences:
            self.preferences[category] = []
            
        if preference not in self.preferences[category]:
            self.preferences[category].append(preference)
            
    def track_conversation_topic(self, topic: str):
        """Track topics discussed to understand user interests."""
        if topic not in self.conversation_topics:
            self.conversation_topics[topic] = 0
        self.conversation_topics[topic] += 1
        
    def develop_personality_trait(self, trait: str, value: float):
        """
        Develop or strengthen a personality trait.
        
        Args:
            trait: Name of the trait (e.g., 'humor', 'formality', 'enthusiasm')
            value: Strength of the trait (0.0-1.0), can be adjusted over time
        """
        if trait not in self.personality_traits:
            self.personality_traits[trait] = value
        else:
            # Blend old and new values (weighted average)
            self.personality_traits[trait] = (
                self.personality_traits[trait] * 0.7 + value * 0.3
            )
            
    def add_rapport_indicator(self, indicator: str, positive: bool):
        """
        Track rapport with the user.
        
        Args:
            indicator: Description of the interaction
            positive: Whether it was positive or negative
        """
        self.user_relationship['rapport_indicators'].append({
            'indicator': indicator,
            'positive': positive,
            'timestamp': datetime.now().isoformat()
        })
        
        # Keep only last 50 indicators
        if len(self.user_relationship['rapport_indicators']) > 50:
            self.user_relationship['rapport_indicators'] = \
                self.user_relationship['rapport_indicators'][-50:]
                
    def get_short_term_context(self, max_turns: int = 6) -> str:
        """
        Get recent conversation context as a formatted string.
        
        Args:
            max_turns: Maximum number of turns to include
            
        Returns:
            Formatted conversation context
        """
        if not self.conversation_buffer:
            return ""
            
        recent = list(self.conversation_buffer)[-max_turns:]
        lines = []
        
        for turn in recent:
            role = "User" if turn['role'] == "user" else "Assistant"
            text = turn['text']
            if len(text) > 300:
                text = text[:300] + "…"
            lines.append(f"{role}: {text}")
            
        return "\n".join(lines)
        
    def get_long_term_context(self) -> str:
        """
        Generate a summary of long-term memory for inclusion in prompts.
        
        Returns:
            Formatted long-term memory summary
        """
        lines = []
        
        # Interaction history
        if self.interaction_count > 0:
            lines.append(f"Interaction count: {self.interaction_count}")
            familiarity = self.user_relationship['familiarity_level']
            if familiarity < 20:
                lines.append("Relationship: New acquaintance")
            elif familiarity < 50:
                lines.append("Relationship: Familiar")
            elif familiarity < 80:
                lines.append("Relationship: Well-known")
            else:
                lines.append("Relationship: Close companion")
                
        # User facts
        if self.user_facts:
            lines.append("\nKnown facts about user:")
            # Sort by confidence and recency
            sorted_facts = sorted(
                self.user_facts[-10:],  # Last 10 facts
                key=lambda f: (f['confidence'], f['learned_at']),
                reverse=True
            )
            for fact in sorted_facts[:5]:  # Top 5 most confident facts
                lines.append(f"  - {fact['fact']}")
                
        # Preferences
        if self.preferences:
            lines.append("\nUser preferences:")
            for category, prefs in list(self.preferences.items())[:3]:
                lines.append(f"  {category}: {', '.join(prefs[:3])}")
                
        # Conversation topics
        if self.conversation_topics:
            top_topics = sorted(
                self.conversation_topics.items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]
            if top_topics:
                lines.append("\nFrequent topics: " + 
                           ", ".join([t[0] for t in top_topics]))
                           
        # Important memories
        if self.important_memories:
            recent_memories = sorted(
                self.important_memories,
                key=lambda m: m['emotional_weight'],
                reverse=True
            )[:3]
            if recent_memories:
                lines.append("\nImportant memories:")
                for mem in recent_memories:
                    lines.append(f"  - {mem['memory']}")
                    
        # Personality traits
        if self.personality_traits:
            lines.append("\nDeveloped personality traits:")
            for trait, value in sorted(
                self.personality_traits.items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]:
                strength = "strongly" if value > 0.7 else "moderately" if value > 0.4 else "slightly"
                lines.append(f"  - {strength} {trait}")
                
        return "\n".join(lines) if lines else ""
        
    def clear_short_term(self):
        """Clear short-term conversation buffer."""
        self.conversation_buffer.clear()
        
    def export_memory(self) -> Dict[str, Any]:
        """Export full memory as a dictionary."""
        return {
            'persona_key': self.persona_key,
            'short_term': list(self.conversation_buffer),
            'user_facts': self.user_facts,
            'interaction_count': self.interaction_count,
            'last_interaction': self.last_interaction,
            'personality_traits': self.personality_traits,
            'important_memories': self.important_memories,
            'preferences': self.preferences,
            'conversation_topics': self.conversation_topics,
            'user_relationship': self.user_relationship
        }


class MemoryManager:
    """
    Central manager for all persona memories.
    Handles loading, saving, and accessing memories for different personas.
    """
    
    def __init__(self, memory_dir: str = ".memory"):
        self.memory_dir = Path(memory_dir)
        self.memories: Dict[str, PersonaMemory] = {}
        self._ensure_memory_dir()
        
    def _ensure_memory_dir(self):
        """Ensure the memory directory exists."""
        self.memory_dir.mkdir(exist_ok=True)
        
    def get_persona_memory(self, persona_key: str) -> PersonaMemory:
        """
        Get or create memory for a persona.
        
        Args:
            persona_key: Unique identifier for the persona
            
        Returns:
            PersonaMemory instance for the persona
        """
        if persona_key not in self.memories:
            self.memories[persona_key] = PersonaMemory(
                persona_key,
                str(self.memory_dir)
            )
        return self.memories[persona_key]
        
    def save_all_memories(self):
        """Save all loaded persona memories."""
        for memory in self.memories.values():
            memory.save_memory()
            
    def clear_persona_memory(self, persona_key: str, keep_long_term: bool = True):
        """
        Clear memory for a persona.
        
        Args:
            persona_key: Unique identifier for the persona
            keep_long_term: If True, only clear short-term memory
        """
        if persona_key in self.memories:
            memory = self.memories[persona_key]
            memory.clear_short_term()
            
            if not keep_long_term:
                # Reset all memory
                self.memories[persona_key] = PersonaMemory(
                    persona_key,
                    str(self.memory_dir)
                )


# Global memory manager instance
memory_manager = MemoryManager()
