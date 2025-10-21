# memory_system.py
# Advanced memory management system for personas with short-term and long-term memory,
# personality development, and intelligent context retrieval.

import json
import os
import time
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any, Optional
from collections import defaultdict, deque
import hashlib
import re
from dataclasses import dataclass, asdict, field
from enum import Enum

# Memory storage directory
MEMORY_DIR = os.path.join(os.path.dirname(__file__), "persona_memories")
os.makedirs(MEMORY_DIR, exist_ok=True)

class MemoryType(Enum):
    """Types of memories that can be stored."""
    FACT = "fact"                    # Factual information about user or world
    PREFERENCE = "preference"        # User preferences and likes/dislikes
    EXPERIENCE = "experience"        # Shared experiences and events
    EMOTION = "emotion"              # Emotional responses and connections
    SKILL = "skill"                  # Learned skills or knowledge
    PERSONALITY = "personality"      # Personality trait observations

class MemoryImportance(Enum):
    """Importance levels for memories."""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

@dataclass
class Memory:
    """Individual memory unit."""
    id: str
    content: str
    memory_type: MemoryType
    importance: MemoryImportance
    timestamp: float
    context: Dict[str, Any] = field(default_factory=dict)
    access_count: int = 0
    last_accessed: float = field(default_factory=time.time)
    embedding_vector: Optional[List[float]] = None  # For future semantic search
    tags: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        """Convert memory to dictionary for serialization."""
        data = asdict(self)
        data['memory_type'] = self.memory_type.value
        data['importance'] = self.importance.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Memory':
        """Create memory from dictionary."""
        data['memory_type'] = MemoryType(data['memory_type'])
        data['importance'] = MemoryImportance(data['importance'])
        return cls(**data)

@dataclass
class PersonalityTrait:
    """Dynamic personality trait that evolves over time."""
    name: str
    value: float  # -1.0 to 1.0
    confidence: float  # 0.0 to 1.0, how sure we are about this trait
    evidence_count: int = 0
    last_updated: float = field(default_factory=time.time)
    
    def update(self, delta: float, confidence_boost: float = 0.1):
        """Update trait value and confidence."""
        # Update value with diminishing returns
        self.value = max(-1.0, min(1.0, self.value + delta * (1 - abs(self.value))))
        # Increase confidence up to 1.0
        self.confidence = min(1.0, self.confidence + confidence_boost)
        self.evidence_count += 1
        self.last_updated = time.time()

class PersonaMemory:
    """Complete memory system for a single persona."""
    
    # Core personality dimensions
    PERSONALITY_DIMENSIONS = {
        "warmth": "cold (-1) to warm (1)",
        "formality": "casual (-1) to formal (1)",
        "humor": "serious (-1) to humorous (1)",
        "curiosity": "indifferent (-1) to curious (1)",
        "empathy": "detached (-1) to empathetic (1)",
        "assertiveness": "passive (-1) to assertive (1)",
        "creativity": "practical (-1) to creative (1)",
        "patience": "impatient (-1) to patient (1)"
    }
    
    def __init__(self, persona_key: str):
        self.persona_key = persona_key
        self.memory_file = os.path.join(MEMORY_DIR, f"{persona_key}_memory.json")
        
        # Memory storage
        self.short_term_memory = deque(maxlen=50)  # Recent conversation context
        self.long_term_memory: Dict[str, Memory] = {}  # Persistent memories
        self.personality_traits: Dict[str, PersonalityTrait] = {}
        
        # Memory indices for fast retrieval
        self.memory_by_type: Dict[MemoryType, List[str]] = defaultdict(list)
        self.memory_by_tag: Dict[str, List[str]] = defaultdict(list)
        
        # Session tracking
        self.session_start = time.time()
        self.interaction_count = 0
        
        # Load existing memories
        self.load_memories()
        
        # Initialize personality traits if new persona
        if not self.personality_traits:
            self._initialize_personality()
    
    def _initialize_personality(self):
        """Initialize personality traits with base values."""
        # Set base traits based on persona
        base_traits = {
            "jarvis": {
                "warmth": 0.6, "formality": 0.7, "humor": 0.3, "curiosity": 0.5,
                "empathy": 0.7, "assertiveness": 0.8, "creativity": 0.6, "patience": 0.8
            },
            "alexa": {
                "warmth": 0.8, "formality": -0.2, "humor": 0.6, "curiosity": 0.7,
                "empathy": 0.8, "assertiveness": 0.5, "creativity": 0.7, "patience": 0.7
            }
        }
        
        base = base_traits.get(self.persona_key, {})
        for dimension in self.PERSONALITY_DIMENSIONS:
            initial_value = base.get(dimension, 0.0)
            self.personality_traits[dimension] = PersonalityTrait(
                name=dimension,
                value=initial_value,
                confidence=0.5  # Medium confidence initially
            )
    
    def add_short_term_memory(self, role: str, content: str):
        """Add to short-term conversation memory."""
        self.short_term_memory.append({
            "role": role,
            "content": content,
            "timestamp": time.time()
        })
        self.interaction_count += 1
        
        # Analyze for memory extraction
        if role == "user":
            self._extract_memories_from_utterance(content)
    
    def _extract_memories_from_utterance(self, utterance: str):
        """Extract potential memories from user utterance."""
        utterance_lower = utterance.lower()
        
        # Extract preferences
        preference_patterns = [
            (r"i (like|love|enjoy|prefer) (.+)", MemoryImportance.MEDIUM),
            (r"i (hate|dislike|don't like) (.+)", MemoryImportance.MEDIUM),
            (r"my favorite (.+) is (.+)", MemoryImportance.HIGH),
            (r"i'm (allergic|intolerant) to (.+)", MemoryImportance.CRITICAL)
        ]
        
        for pattern, importance in preference_patterns:
            match = re.search(pattern, utterance_lower)
            if match:
                content = f"User {match.group(0)}"
                self._store_memory(content, MemoryType.PREFERENCE, importance, tags=["user_preference"])
        
        # Extract facts
        fact_patterns = [
            (r"my name is (.+)", MemoryImportance.CRITICAL),
            (r"i('m| am) (\d+) years old", MemoryImportance.HIGH),
            (r"i (work|live|study) (at|in) (.+)", MemoryImportance.HIGH),
            (r"i have (.+) (children|kids|pets)", MemoryImportance.HIGH)
        ]
        
        for pattern, importance in fact_patterns:
            match = re.search(pattern, utterance_lower)
            if match:
                content = f"User {match.group(0)}"
                self._store_memory(content, MemoryType.FACT, importance, tags=["user_fact"])
        
        # Extract emotional context
        emotion_keywords = {
            "happy": 0.3, "excited": 0.4, "sad": -0.3, "angry": -0.4,
            "frustrated": -0.3, "pleased": 0.3, "disappointed": -0.2
        }
        
        for emotion, trait_delta in emotion_keywords.items():
            if emotion in utterance_lower:
                self._update_personality_from_interaction("empathy", trait_delta * 0.1)
                self._store_memory(
                    f"User expressed feeling {emotion}",
                    MemoryType.EMOTION,
                    MemoryImportance.MEDIUM,
                    tags=["emotion", emotion]
                )
    
    def _store_memory(self, content: str, memory_type: MemoryType, 
                      importance: MemoryImportance, tags: List[str] = None):
        """Store a new memory."""
        # Generate unique ID
        memory_id = hashlib.md5(f"{content}{time.time()}".encode()).hexdigest()[:12]
        
        # Create memory
        memory = Memory(
            id=memory_id,
            content=content,
            memory_type=memory_type,
            importance=importance,
            timestamp=time.time(),
            tags=tags or []
        )
        
        # Store in long-term memory
        self.long_term_memory[memory_id] = memory
        
        # Update indices
        self.memory_by_type[memory_type].append(memory_id)
        for tag in memory.tags:
            self.memory_by_tag[tag].append(memory_id)
        
        # Save to disk
        self.save_memories()
    
    def _update_personality_from_interaction(self, trait: str, delta: float):
        """Update personality trait based on interaction."""
        if trait in self.personality_traits:
            self.personality_traits[trait].update(delta)
    
    def get_relevant_memories(self, context: str, max_memories: int = 5) -> List[Memory]:
        """Retrieve most relevant memories for current context."""
        relevant_memories = []
        
        # Simple keyword matching for now (can be enhanced with embeddings)
        context_lower = context.lower()
        context_words = set(context_lower.split())
        
        # Score each memory
        memory_scores = []
        for memory_id, memory in self.long_term_memory.items():
            score = 0
            
            # Content relevance
            memory_words = set(memory.content.lower().split())
            overlap = len(context_words.intersection(memory_words))
            score += overlap * 2
            
            # Importance bonus
            score += memory.importance.value * 3
            
            # Recency bonus (decay over time)
            age_days = (time.time() - memory.timestamp) / (24 * 3600)
            recency_score = max(0, 10 - age_days)
            score += recency_score
            
            # Access frequency bonus
            score += min(memory.access_count, 5)
            
            if score > 0:
                memory_scores.append((memory_id, score))
        
        # Sort by score and get top memories
        memory_scores.sort(key=lambda x: x[1], reverse=True)
        
        for memory_id, _ in memory_scores[:max_memories]:
            memory = self.long_term_memory[memory_id]
            memory.access_count += 1
            memory.last_accessed = time.time()
            relevant_memories.append(memory)
        
        return relevant_memories
    
    def get_personality_summary(self) -> str:
        """Generate a summary of current personality traits."""
        if not self.personality_traits:
            return ""
        
        summary_parts = []
        
        # Get significant traits (high confidence and non-neutral value)
        significant_traits = [
            (name, trait) for name, trait in self.personality_traits.items()
            if trait.confidence > 0.6 and abs(trait.value) > 0.3
        ]
        
        if significant_traits:
            summary_parts.append("Current personality traits:")
            for name, trait in sorted(significant_traits, key=lambda x: abs(x[1].value), reverse=True):
                if trait.value > 0:
                    descriptor = f"quite {name}"
                else:
                    opposite = {
                        "warmth": "reserved",
                        "formality": "casual",
                        "humor": "serious",
                        "curiosity": "focused",
                        "empathy": "objective",
                        "assertiveness": "accommodating",
                        "creativity": "practical",
                        "patience": "direct"
                    }.get(name, f"less {name}")
                    descriptor = f"more {opposite}"
                
                summary_parts.append(f"- Tends to be {descriptor} (confidence: {trait.confidence:.0%})")
        
        return "\n".join(summary_parts)
    
    def generate_context_prompt(self) -> str:
        """Generate context prompt for current conversation."""
        parts = []
        
        # Add personality summary
        personality = self.get_personality_summary()
        if personality:
            parts.append(personality)
        
        # Add recent conversation context
        if self.short_term_memory:
            recent_context = []
            for entry in list(self.short_term_memory)[-10:]:  # Last 10 turns
                role = "User" if entry["role"] == "user" else "Assistant"
                recent_context.append(f"{role}: {entry['content'][:200]}")
            
            if recent_context:
                parts.append("\nRecent conversation:")
                parts.extend(recent_context)
        
        # Add relevant long-term memories
        if self.short_term_memory:
            last_user_utterance = next(
                (e["content"] for e in reversed(self.short_term_memory) if e["role"] == "user"),
                ""
            )
            
            if last_user_utterance:
                relevant_memories = self.get_relevant_memories(last_user_utterance, max_memories=3)
                if relevant_memories:
                    parts.append("\nRelevant memories:")
                    for memory in relevant_memories:
                        parts.append(f"- {memory.content} [{memory.memory_type.value}]")
        
        # Add user facts summary
        user_facts = [
            self.long_term_memory[mid] for mid in self.memory_by_type.get(MemoryType.FACT, [])
            if "user_fact" in self.long_term_memory[mid].tags
        ]
        
        if user_facts:
            parts.append("\nKnown user information:")
            # Sort by importance and recency
            user_facts.sort(key=lambda m: (m.importance.value, m.timestamp), reverse=True)
            for fact in user_facts[:5]:
                parts.append(f"- {fact.content}")
        
        return "\n".join(parts)
    
    def save_memories(self):
        """Save memories to disk."""
        data = {
            "persona_key": self.persona_key,
            "long_term_memory": {
                mid: memory.to_dict() for mid, memory in self.long_term_memory.items()
            },
            "personality_traits": {
                name: asdict(trait) for name, trait in self.personality_traits.items()
            },
            "interaction_count": self.interaction_count,
            "last_saved": time.time()
        }
        
        with open(self.memory_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def load_memories(self):
        """Load memories from disk."""
        if not os.path.exists(self.memory_file):
            return
        
        try:
            with open(self.memory_file, 'r') as f:
                data = json.load(f)
            
            # Load long-term memories
            for mid, memory_data in data.get("long_term_memory", {}).items():
                memory = Memory.from_dict(memory_data)
                self.long_term_memory[mid] = memory
                
                # Rebuild indices
                self.memory_by_type[memory.memory_type].append(mid)
                for tag in memory.tags:
                    self.memory_by_tag[tag].append(mid)
            
            # Load personality traits
            for name, trait_data in data.get("personality_traits", {}).items():
                self.personality_traits[name] = PersonalityTrait(**trait_data)
            
            self.interaction_count = data.get("interaction_count", 0)
            
        except Exception as e:
            print(f"[MEMORY] Error loading memories for {self.persona_key}: {e}")
    
    def forget_old_memories(self, days: int = 30):
        """Remove memories older than specified days (except critical ones)."""
        cutoff_time = time.time() - (days * 24 * 3600)
        memories_to_remove = []
        
        for mid, memory in self.long_term_memory.items():
            if (memory.timestamp < cutoff_time and 
                memory.importance != MemoryImportance.CRITICAL and
                memory.access_count < 3):
                memories_to_remove.append(mid)
        
        for mid in memories_to_remove:
            memory = self.long_term_memory.pop(mid)
            # Remove from indices
            self.memory_by_type[memory.memory_type].remove(mid)
            for tag in memory.tags:
                self.memory_by_tag[tag].remove(mid)
        
        if memories_to_remove:
            self.save_memories()
            
        return len(memories_to_remove)

# Global memory managers for each persona
memory_managers: Dict[str, PersonaMemory] = {}

def get_memory_manager(persona_key: str) -> PersonaMemory:
    """Get or create memory manager for a persona."""
    if persona_key not in memory_managers:
        memory_managers[persona_key] = PersonaMemory(persona_key)
    return memory_managers[persona_key]

def cleanup_all_memories():
    """Save all memories and cleanup."""
    for manager in memory_managers.values():
        manager.save_memories()