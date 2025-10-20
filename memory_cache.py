"""
Memory Cache System for Evolving AI Personas
Uses Gemini's context caching for efficient memory management
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
import google.generativeai as genai

logger = logging.getLogger(__name__)


@dataclass
class Memory:
    """Represents a single memory entry"""
    timestamp: str
    content: str
    importance: float = 0.5  # 0.0 to 1.0
    tags: List[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Memory':
        return cls(**data)


class MemoryCache:
    """
    Memory cache system with persistent storage and Gemini integration.
    Optimized for Raspberry Pi 5.
    """
    
    def __init__(
        self,
        persona_name: str,
        memory_file: Path,
        max_memories: int = 100,
        max_context_tokens: int = 8000
    ):
        self.persona_name = persona_name
        self.memory_file = memory_file
        self.max_memories = max_memories
        self.max_context_tokens = max_context_tokens
        self.memories: List[Memory] = []
        self.cached_context: Optional[genai.types.CachedContent] = None
        self.cache_expires_at: Optional[datetime] = None
        
        # Load existing memories from disk
        self._load_memories()
        
        logger.info(f"Initialized memory cache for {persona_name} with {len(self.memories)} memories")
    
    def add_memory(self, content: str, importance: float = 0.5, tags: List[str] = None) -> None:
        """Add a new memory to the cache"""
        memory = Memory(
            timestamp=datetime.now().isoformat(),
            content=content,
            importance=importance,
            tags=tags or []
        )
        
        self.memories.append(memory)
        logger.debug(f"Added memory for {self.persona_name}: {content[:50]}...")
        
        # Prune if we exceed max memories
        if len(self.memories) > self.max_memories:
            self._prune_memories()
        
        # Save to disk
        self._save_memories()
        
        # Invalidate cached context
        self.cached_context = None
    
    def get_recent_memories(self, count: int = 10) -> List[Memory]:
        """Get the most recent N memories"""
        return self.memories[-count:] if count > 0 else self.memories
    
    def get_important_memories(self, threshold: float = 0.7, count: int = 20) -> List[Memory]:
        """Get the most important memories above a threshold"""
        important = [m for m in self.memories if m.importance >= threshold]
        important.sort(key=lambda m: m.importance, reverse=True)
        return important[:count]
    
    def search_memories(self, query: str, count: int = 10) -> List[Memory]:
        """Search memories by content (simple string matching)"""
        query_lower = query.lower()
        matches = [m for m in self.memories if query_lower in m.content.lower()]
        return matches[-count:] if matches else []
    
    def get_memory_context(self, include_recent: int = 20, include_important: int = 10) -> str:
        """
        Build a context string from memories for Gemini.
        Combines recent and important memories.
        """
        context_parts = ["=== MEMORY CONTEXT ===\n"]
        
        # Get important memories
        important = self.get_important_memories(threshold=0.7, count=include_important)
        if important:
            context_parts.append("Important Memories:")
            for mem in important:
                context_parts.append(f"- [{mem.timestamp}] {mem.content}")
            context_parts.append("")
        
        # Get recent memories (avoiding duplicates)
        important_ids = {id(m) for m in important}
        recent = [m for m in self.get_recent_memories(include_recent) if id(m) not in important_ids]
        if recent:
            context_parts.append("Recent Memories:")
            for mem in recent:
                context_parts.append(f"- [{mem.timestamp}] {mem.content}")
        
        context_parts.append("=== END MEMORY CONTEXT ===\n")
        return "\n".join(context_parts)
    
    def summarize_memories(self, model: genai.GenerativeModel) -> str:
        """
        Use Gemini to create a summary of memories.
        This helps compress older memories.
        """
        if len(self.memories) < 10:
            return ""
        
        memory_text = "\n".join([
            f"{i+1}. [{m.timestamp}] {m.content}"
            for i, m in enumerate(self.memories)
        ])
        
        prompt = f"""
        Analyze these memories and create a concise personality summary.
        Focus on:
        - Key experiences and learnings
        - Emerging personality traits
        - Important relationships or interactions
        - Growth and changes over time
        
        Memories:
        {memory_text}
        
        Provide a brief but insightful summary (2-3 paragraphs).
        """
        
        try:
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            logger.error(f"Failed to summarize memories: {e}")
            return ""
    
    def _prune_memories(self) -> None:
        """
        Prune old memories, keeping the most important and recent ones.
        Uses a scoring system that combines recency and importance.
        """
        if len(self.memories) <= self.max_memories:
            return
        
        # Score each memory (recency + importance)
        now = datetime.now()
        scored_memories = []
        
        for i, memory in enumerate(self.memories):
            try:
                mem_time = datetime.fromisoformat(memory.timestamp)
                age_hours = (now - mem_time).total_seconds() / 3600
                # Recency score decreases with age (exponential decay)
                recency_score = 1.0 / (1.0 + age_hours / 24.0)
                # Combined score
                total_score = (memory.importance * 0.6) + (recency_score * 0.4)
                scored_memories.append((total_score, i, memory))
            except Exception as e:
                logger.warning(f"Error scoring memory: {e}")
                scored_memories.append((0.5, i, memory))
        
        # Sort by score and keep the top memories
        scored_memories.sort(reverse=True, key=lambda x: x[0])
        self.memories = [m for _, _, m in scored_memories[:self.max_memories]]
        
        # Re-sort by timestamp to maintain chronological order
        self.memories.sort(key=lambda m: m.timestamp)
        
        logger.info(f"Pruned memories for {self.persona_name}, kept {len(self.memories)}")
    
    def _save_memories(self) -> None:
        """Save memories to disk"""
        try:
            data = {
                "persona": self.persona_name,
                "last_updated": datetime.now().isoformat(),
                "memories": [m.to_dict() for m in self.memories]
            }
            
            with open(self.memory_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.debug(f"Saved {len(self.memories)} memories to {self.memory_file}")
        except Exception as e:
            logger.error(f"Failed to save memories: {e}")
    
    def _load_memories(self) -> None:
        """Load memories from disk"""
        if not self.memory_file.exists():
            logger.info(f"No existing memory file for {self.persona_name}")
            return
        
        try:
            with open(self.memory_file, 'r') as f:
                data = json.load(f)
            
            self.memories = [Memory.from_dict(m) for m in data.get("memories", [])]
            logger.info(f"Loaded {len(self.memories)} memories for {self.persona_name}")
        except Exception as e:
            logger.error(f"Failed to load memories: {e}")
            self.memories = []
    
    def clear_cache(self) -> None:
        """Clear the Gemini context cache"""
        if self.cached_context:
            try:
                self.cached_context.delete()
                logger.info(f"Cleared context cache for {self.persona_name}")
            except Exception as e:
                logger.warning(f"Failed to delete cache: {e}")
        
        self.cached_context = None
        self.cache_expires_at = None
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the memory cache"""
        if not self.memories:
            return {
                "total_memories": 0,
                "avg_importance": 0.0,
                "oldest_memory": None,
                "newest_memory": None,
            }
        
        return {
            "total_memories": len(self.memories),
            "avg_importance": sum(m.importance for m in self.memories) / len(self.memories),
            "oldest_memory": self.memories[0].timestamp if self.memories else None,
            "newest_memory": self.memories[-1].timestamp if self.memories else None,
        }
