# services.py
# Contains external service logic for web search and memory management

import json
import re
import sys

# Attempt to import search libraries
SEARCH_BACKEND_OK = True
_ddg_backend = None
try:
    from ddgs import DDGS
    _ddg_backend = "ddgs"
except Exception:
    try:
        from duckduckgo_search import DDGS
        _ddg_backend = "duckduckgo_search"
    except Exception:
        SEARCH_BACKEND_OK = False
try:
    import wikipedia
    wikipedia.set_lang("en")
except Exception:
    SEARCH_BACKEND_OK = False

from google import genai
from config import CONFIG, PERSONAS, VOICE_CATALOG
from memory_system import MemoryType, MemoryImportance, get_memory_manager
from memory_tools import memory_query_tool_decl, memory_store_tool_decl, personality_analysis_tool_decl

# =========================
# Gemini Client
# =========================
client = genai.Client()

# =========================
# System prompt rules
# =========================
BASE_SYSTEM_RULES = (
    "POLICY:\n"
    "- Default to brevity: 1–2 sentences. Expand ONLY if the user clearly asks for more detail.\n"
    "- Avoid filler. Be direct and useful.\n"
    "TOOLS:\n"
    "- You DO have a `web_search` tool. For factual/current events, call `web_search` first, then answer clearly.\n"
    "- If the user says 'Thank you for your time', call `shutdown_robot` and say nothing else.\n"
    "MEMORY:\n"
    "- You have access to memory tools: `query_memories`, `store_important_memory`, and `analyze_personality_development`.\n"
    "- Use `query_memories` to recall past conversations, user preferences, or shared experiences.\n"
    "- Use `store_important_memory` when the user shares significant information worth remembering.\n"
    "- Your personality evolves based on interactions - be consistent with your developing traits.\n"
)

# =========================
# Tool Declarations
# =========================
shutdown_tool_decl = {
    "function_declarations":[
        {"name":"shutdown_robot","description":"Return to wake-word listening.","parameters":{}}
    ]
}

web_search_tool_decl = {
    "function_declarations":[
        {"name":"web_search","description":"Search web (DDG+Wikipedia)",
         "parameters":{"type":"object","properties":{
             "query":{"type":"string"},
             "max_results":{"type":"integer","minimum":1,"maximum":8}
         },"required":["query"]}}
    ]
}

# =========================
# Search Implementation
# =========================
class WebSearcher:
    def __init__(self):
        self.ok = SEARCH_BACKEND_OK
        if not self.ok:
            print("[WARNING] Search libraries not found. Web search will be disabled.", file=sys.stderr)
            print("           Run: pip install -U ddgs wikipedia", file=sys.stderr)

    def search(self, query: str, max_results: int = 5):
        if not self.ok:
            return {"results": [], "error": "Search libraries (ddgs, wikipedia) are not installed."}

        max_results = max(1, min(int(max_results or 5), 8))
        results = []

        try:
            titles = wikipedia.search(query, results=1)
            if titles:
                title = titles[0]
                try:
                    page = wikipedia.page(title, auto_suggest=False)
                    summary = wikipedia.summary(title, sentences=3, auto_suggest=False)
                except Exception:
                    page = wikipedia.page(title)
                    summary = wikipedia.summary(title, sentences=3)
                results.append({"title": page.title, "snippet": summary, "url": page.url})
        except Exception:
            pass # Wikipedia search can be brittle, fail silently

        try:
            with DDGS() as ddgs:
                for hit in ddgs.text(query, max_results=max_results):
                    if not hit: continue
                    title = (hit.get("title") or "").strip()
                    body = (hit.get("body") or "").strip()
                    href = hit.get("href") or hit.get("url") or ""
                    if title and (body or href):
                        results.append({"title": title, "snippet": body[:500], "url": href})
                    if len(results) >= max_results:
                        break
        except Exception as e:
            print(f"[SEARCH] DDGS search failed: {e}", file=sys.stderr)
            pass

        return {"results": results[:max_results], "backend": _ddg_backend}

searcher = WebSearcher()

# =========================
# Memory Management Functions
# =========================
def query_persona_memories(persona_key: str, query: str, memory_type: str = "all", max_results: int = 5):
    """Query memories for a specific persona."""
    memory_mgr = get_memory_manager(persona_key)
    
    if memory_type == "all":
        memories = memory_mgr.get_relevant_memories(query, max_results)
    else:
        memory_type_enum = MemoryType(memory_type)
        memory_ids = memory_mgr.memory_by_type.get(memory_type_enum, [])
        all_memories = [memory_mgr.long_term_memory[mid] for mid in memory_ids if mid in memory_mgr.long_term_memory]
        
        scored_memories = []
        query_words = set(query.lower().split())
        for memory in all_memories:
            memory_words = set(memory.content.lower().split())
            score = len(query_words.intersection(memory_words))
            if score > 0:
                scored_memories.append((memory, score))
        
        scored_memories.sort(key=lambda x: x[1], reverse=True)
        memories = [m[0] for m in scored_memories[:max_results]]
    
    return {
        "memories": [
            {
                "content": m.content,
                "type": m.memory_type.value,
                "importance": m.importance.value,
                "timestamp": m.timestamp,
                "access_count": m.access_count
            }
            for m in memories
        ],
        "total_memories": len(memory_mgr.long_term_memory)
    }

def store_persona_memory(persona_key: str, content: str, memory_type: str, importance: str, tags: list = None):
    """Store a new memory for a persona."""
    memory_mgr = get_memory_manager(persona_key)
    
    memory_type_enum = MemoryType(memory_type)
    importance_map = {
        "low": MemoryImportance.LOW,
        "medium": MemoryImportance.MEDIUM,
        "high": MemoryImportance.HIGH,
        "critical": MemoryImportance.CRITICAL
    }
    importance_enum = importance_map.get(importance.lower(), MemoryImportance.MEDIUM)
    
    memory_mgr._store_memory(content, memory_type_enum, importance_enum, tags or [])
    
    return {"status": "OK", "message": f"Memory stored successfully for {persona_key}"}

def analyze_persona_personality(persona_key: str, include_history: bool = False):
    """Analyze personality development for a persona."""
    memory_mgr = get_memory_manager(persona_key)
    
    result = {
        "persona": persona_key,
        "interaction_count": memory_mgr.interaction_count,
        "personality_summary": memory_mgr.get_personality_summary(),
        "traits": {}
    }
    
    for name, trait in memory_mgr.personality_traits.items():
        result["traits"][name] = {
            "value": trait.value,
            "confidence": trait.confidence,
            "evidence_count": trait.evidence_count,
            "description": memory_mgr.PERSONALITY_DIMENSIONS.get(name, "")
        }
    
    if include_history:
        result["history"] = "Historical tracking not yet implemented"
    
    return result