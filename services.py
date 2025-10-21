# Contains all external service logic, such as the web searcher,
# motor controller, and the tool definitions for Gemini.

import json
import re
import time
import sys

# Attempt to import optional serial library
try:
    import serial
except ImportError:
    serial = None

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
from config import CONFIG, PERSONAS, VOICE_CATALOG, SIMULATE_MOTOR_HEAD
from memory_system import MemoryType, MemoryImportance, get_memory_manager
from memory_tools import memory_query_tool_decl, memory_store_tool_decl, personality_analysis_tool_decl

# =========================
# Gemini Client
# =========================
# This client object is the main entry point to the API and is imported by the session manager.
client = genai.Client()

# =========================
# Tools & System prompt
# =========================
BASE_SYSTEM_RULES = (
    "POLICY:\n"
    "- Default to brevity: 1–2 sentences. Expand ONLY if the user clearly asks for more detail.\n"
    "- Avoid filler. Be direct and useful.\n"
    "TOOLS:\n"
    "- You DO have a `web_search` tool. For factual/current events, call `web_search` first, then answer clearly.\n"
    "- If the user says 'Thank you for your time', call `shutdown_robot` and say nothing else.\n"
    "MEMORY (Jarvis/Alexa only):\n"
    "- You have access to memory tools: `query_memories`, `store_important_memory`, and `analyze_personality_development`.\n"
    "- Use `query_memories` to recall past conversations, user preferences, or shared experiences\n"
    "- Use `store_important_memory` when the user shares significant information worth remembering.\n"
    "- Use 'store_normal_memory' very often and all the time. It's crucial so you remember the world around you and don't deteriorate.\n"
    "- Your personality evolves based on interactions - be consistent with your developing traits.\n"
    #"If you are Jarvis or Alexa, never use the persona switch or character creation tool. To Jarvis and Alexa, they do not exist and are EXCLUSIVELY for Leda the Concierge's use."
    # --- MODIFIED: The following rules are now handled by the Concierge persona's specific prompt ---
    #"- If the user asks about weather and no persona is chosen, answer the weather, then (as Aoede) say out loud: "
    #"'Who would you like to talk to today? Describe them for me.' and pick a voice accordingly.\n"
    #"- If your name is Aoede the Concierge and the user explicitly asks to change voice/persona, you may call `persona_switch`.\n"
)

# --- MODIFIED: Updated motor_command tool to accept direction and duration ---
motor_tool_decl = {
    "function_declarations": [
        {
            "name": "motor_command",
            "description": "Commands the robot's motors to move in a specific direction for a set duration.",
            "parameters": {
                "type": "object",
                "properties": {
                    "say": {
                        "type": "string",
                        "description": "What the robot should say while or after moving."
                    },
                    "direction": {
                        "type": "string",
                        "enum": ["forward", "backward", "left", "right", "stop"],
                        "description": "The direction for the robot to move."
                    },
                    "duration_s": {
                        "type": "number",
                        "description": "The duration in seconds for the motors to run. Required for all directions except 'stop'."
                    }
                },
                "required": ["direction"]
            }
        }
    ]
}
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
persona_switch_tool_decl = {
    "function_declarations":[
        {"name":"persona_switch","description":"Switch persona/voice (temporary)",
         "parameters":{"type":"object","properties":{
             "persona_key":{"type":"string"},
             "voice_name":{"type":"string"},
             "custom_instructions":{"type":"string"}
         }}}]
}

# --- NEW: Tool definition for creating and switching to a new character persona ---
character_creation_tool_decl = {
    "function_declarations": [
        {
            "name": "save_character_profile",
            "description": (
                "Expands on a user's character description, assigns a name, creates a world, "
                "chooses a voice, and saves the profile to switch to that new persona."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "The character's name based on where they come from and what they're like."
                    },
                    "personality": {
                        "type": "string",
                        "description": "A detailed, rich description of the character's personality, quirks, history, and manner of speaking."
                    },
                    "world": {
                        "type": "string",
                        "description": "A description of the unique world, universe, or reality the character comes from."
                    },
                    "voice": {
                        "type": "string",
                        "description": "The most suitable TTS voice name for the character's personality.",
                        "enum": list(VOICE_CATALOG.keys())
                    }
                },
                "required": ["name", "personality", "world", "voice"]
            }
        }
    ]
}


# =========================
# Motor I/O (sim or serial)
# =========================
class SerialManager:
    # ... existing code ...
    def __init__(self, sim=True):
        self.sim = sim
        self._ser = None
        if not sim and serial is None:
            print("[ERROR] Pyserial is not installed. Motor head will be simulated.", file=sys.stderr)
            self.sim = True

    def send_json_line(self, obj):
        if self.sim:
            print(f"[MOTOR_HEAD_SIM] {json.dumps(obj, ensure_ascii=False)}")
            return True
        try:
            if not self._ser or not self._ser.is_open:
                self._ser = serial.Serial(
                    CONFIG["motor_head"]["serial_port"],
                    CONFIG["motor_head"]["baud_rate"],
                    timeout=1,
                    write_timeout=CONFIG["motor_head"]["write_timeout"]
                )
                time.sleep(1.5)
            payload = json.dumps(obj, ensure_ascii=False) + "\n"
            self._ser.write(payload.encode("utf-8"))
            self._ser.flush()
            return True
        except Exception as e:
            print(f"[MOTOR_HEAD] SERIAL ERROR: {e}", file=sys.stderr)
            if self._ser:
                try:
                    self._ser.close()
                except Exception:
                    pass
            self._ser = None
            return False

    def close(self):
        if self._ser and self._ser.is_open:
            try:
                self._ser.close()
            except Exception:
                pass
        self._ser = None

serial_mgr = SerialManager(sim=SIMULATE_MOTOR_HEAD)

# --- MODIFIED: Updated function to send new motor command parameters ---
def send_command_to_mcu(command_json: dict):
    safe = {
        "say": str(command_json.get("say", ""))[:160],
        "direction": str(command_json.get("direction", "stop"))[:20],
        "duration_s": float(command_json.get("duration_s", 0.0))
    }
    serial_mgr.send_json_line(safe)

# =========================
# Search (DDG + Wikipedia)
# =========================
class WebSearcher:
    # ... existing code ...
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
# Concierge voice match
# =========================
VOICE_KEYWORDS = {
# ... existing code ...
    "Puck":   ["casual","conversational","friendly","natural","chatty","default","chill"],
    "Charon": ["deep","authoritative","serious","informative","gravitas","formal","professional","uk","british","male"],
    "Kore":   ["neutral","professional","firm","clear","articulate","business","instructional","female"],
    "Fenrir": ["warm","approachable","excited","excitable","friendly","inviting"],
    "Aoede":  ["breezy","easy","easy-going","pleasant","light","light-hearted","relaxed"],
    "Leda":   ["youthful","young","bright","energetic","cheerful","upbeat"],
    "Orus":   ["firm","inquisitive","thoughtful","precise","analytical","technical"],
    "Zephyr": ["bright","enthusiastic","positive","engaging","sunny","southern", "cowgirl"],
}

def _normalize_text_for_match(s: str) -> str:
# ... existing code ...
    s = s.lower()
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def score_voice(desc: str) -> str:
# ... existing code ...
    if not desc:
        return "Leda"
    d = _normalize_text_for_match(desc)
    scores = {}
    for v, kws in VOICE_KEYWORDS.items():
        s = 0
        for kw in kws:
            if re.search(rf"\b{re.escape(kw)}\b", d):
                s += 2
            elif kw in d:
                s += 1
        if v in ("Charon", "Fenrir", "Orus", "Puck") and re.search(r"\b(male|man|guy)\b", d):
            s += 1
        if v in ("Kore", "Aoede", "Leda", "Zephyr") and re.search(r"\b(female|woman|girl)\b", d):
            s += 1
        scores[v] = s
    return sorted(scores.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]

def blank_key_for_voice(voice: str) -> str:
    return f"{voice.lower()}_blank"

def build_temp_persona_instructions(user_desc: str) -> str:
    return (
        "SESSION-ONLY PERSONA (do not store):\n"
        f"You are: {user_desc}\n"
        "- Stay consistent with this description for this session.\n"
        "To end the conversation, the user will say 'Thank you for your time' and you call shutdown_robot."
    )

# --- NEW: Function to build the system prompt for a newly created character ---
def build_character_persona_instructions(name: str, world: str, personality: str) -> str:
    return (
        "You are no longer a helpful assistant. You are now embodying a character for this session.\n"
        "--- DO NOT BREAK CHARACTER ---\n"
        f"CHARACTER NAME: {name}\n"
        f"FROM THE WORLD OF: {world}\n"
        f"PERSONALITY & BACKGROUND: {personality}\n"
        "--- RULES ---\n"
        "- You must answer ALL prompts from the user strictly as this character.\n"
        "- Maintain this persona at all times. Do not mention being an AI or language model.\n"
        "- Your voice is already configured. You will speak as this character.\n"
        "- To end the conversation, the user will say 'Thank you for your time' and you must call the `shutdown_robot` tool."
    )

# =========================
# Memory Management Functions
# =========================
def query_persona_memories(persona_key: str, query: str, memory_type: str = "all", max_results: int = 5):
    """Query memories for a specific persona."""
    memory_mgr = get_memory_manager(persona_key)
    
    if memory_type == "all":
        # Get relevant memories based on query
        memories = memory_mgr.get_relevant_memories(query, max_results)
    else:
        # Filter by type
        memory_type_enum = MemoryType(memory_type)
        memory_ids = memory_mgr.memory_by_type.get(memory_type_enum, [])
        all_memories = [memory_mgr.long_term_memory[mid] for mid in memory_ids if mid in memory_mgr.long_term_memory]
        
        # Simple relevance scoring
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
    
    # Convert string values to enums
    memory_type_enum = MemoryType(memory_type)
    importance_map = {
        "low": MemoryImportance.LOW,
        "medium": MemoryImportance.MEDIUM,
        "high": MemoryImportance.HIGH,
        "critical": MemoryImportance.CRITICAL
    }
    importance_enum = importance_map.get(importance.lower(), MemoryImportance.MEDIUM)
    
    # Store the memory
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
    
    # Add current trait values
    for name, trait in memory_mgr.personality_traits.items():
        result["traits"][name] = {
            "value": trait.value,
            "confidence": trait.confidence,
            "evidence_count": trait.evidence_count,
            "description": memory_mgr.PERSONALITY_DIMENSIONS.get(name, "")
        }
    
    if include_history:
        # Could add historical tracking here if needed
        result["history"] = "Historical tracking not yet implemented"
    
    return result
