# memory.py
# Simple persistent memory system for personas (Jarvis, Alexa, etc.).
# Supports long-term JSONL storage and lightweight in-process short-term notes.

from __future__ import annotations

import json
import time
import re
from dataclasses import dataclass, asdict
from pathlib import Path
from threading import RLock
from typing import List, Dict, Optional, Any


DATA_ROOT = Path("data")
PERSONAS_ROOT = DATA_ROOT / "personas"


def _now_ts() -> float:
    return time.time()


def _ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


@dataclass
class MemoryItem:
    persona_key: str
    text: str
    category: str = "fact"  # e.g., fact, preference, task, relationship, reflection, personality_trait
    scope: str = "long"  # "short" or "long"
    tags: Optional[List[str]] = None
    importance: float = 0.5  # 0..1
    created_at: float = 0.0

    def to_json(self) -> Dict[str, Any]:
        data = asdict(self)
        # Ensure types are JSON serializable
        data["created_at"] = float(self.created_at)
        return data


class MemoryStore:
    def __init__(self, root: Path = PERSONAS_ROOT):
        self.root = root
        _ensure_dir(self.root)
        self._lock = RLock()
        self._short_term: Dict[str, List[MemoryItem]] = {}

    def _persona_dir(self, persona_key: str) -> Path:
        p = self.root / persona_key
        _ensure_dir(p)
        return p

    def _long_term_file(self, persona_key: str) -> Path:
        return self._persona_dir(persona_key) / "long_term.jsonl"

    def _profile_file(self, persona_key: str) -> Path:
        return self._persona_dir(persona_key) / "profile.json"

    # ---- Public API ----
    def save_memory(
        self,
        persona_key: str,
        text: str,
        category: str = "fact",
        scope: str = "long",
        tags: Optional[List[str]] = None,
        importance: float = 0.5,
    ) -> MemoryItem:
        item = MemoryItem(
            persona_key=persona_key,
            text=(text or "").strip(),
            category=(category or "fact").strip(),
            scope=(scope or "long").strip(),
            tags=tags or [],
            importance=max(0.0, min(float(importance or 0.5), 1.0)),
            created_at=_now_ts(),
        )
        if not item.text:
            return item
        with self._lock:
            if item.scope == "short":
                self._short_term.setdefault(persona_key, []).append(item)
            else:
                lf = self._long_term_file(persona_key)
                with lf.open("a", encoding="utf-8") as f:
                    f.write(json.dumps(item.to_json(), ensure_ascii=False) + "\n")
        return item

    def recall_memory(
        self,
        persona_key: str,
        query: Optional[str] = None,
        top_k: int = 5,
        categories: Optional[List[str]] = None,
        include_short_term: bool = True,
    ) -> List[Dict[str, Any]]:
        query = (query or "").strip()
        top_k = max(1, min(int(top_k or 5), 25))
        cat_set = set([c.strip() for c in (categories or []) if c and c.strip()])

        def score(item: MemoryItem) -> float:
            s = 0.0
            # Recency bonus (more recent = higher score)
            age_s = max(1.0, _now_ts() - item.created_at)
            s += 1.0 / (1.0 + age_s / (60.0 * 60.0 * 24.0))  # ~decays over days
            # Importance bonus
            s += 0.75 * item.importance
            # Category filter/bonus
            if cat_set:
                if item.category in cat_set:
                    s += 0.5
                else:
                    s -= 0.5
            # Query matching
            if query:
                q = query.lower()
                t = item.text.lower()
                # keyword occurrences
                matches = 0
                for token in set(re.split(r"\W+", q)):
                    if token and token in t:
                        matches += 1
                s += 0.6 * matches
                # exact substring presence
                if q in t:
                    s += 0.8
            return s

        items: List[MemoryItem] = []
        with self._lock:
            if include_short_term:
                items.extend(self._short_term.get(persona_key, []))
            # Read long-term
            lf = self._long_term_file(persona_key)
            if lf.exists():
                try:
                    with lf.open("r", encoding="utf-8") as f:
                        for line in f:
                            try:
                                obj = json.loads(line)
                                items.append(
                                    MemoryItem(
                                        persona_key=obj.get("persona_key", persona_key),
                                        text=obj.get("text", ""),
                                        category=obj.get("category", "fact"),
                                        scope=obj.get("scope", "long"),
                                        tags=obj.get("tags") or [],
                                        importance=float(obj.get("importance", 0.5)),
                                        created_at=float(obj.get("created_at", _now_ts())),
                                    )
                                )
                            except Exception:
                                continue
                except Exception:
                    pass
        ranked = sorted(items, key=score, reverse=True)
        return [i.to_json() for i in ranked[:top_k]]

    def render_system_memory(
        self,
        persona_key: str,
        max_chars: int = 1200,
        include_traits: bool = True,
    ) -> str:
        """
        Produce a compact system-context string containing persona profile and
        top long-term memories.
        """
        profile = self.load_persona_profile(persona_key)
        parts: List[str] = []
        if profile:
            name = profile.get("name")
            world = profile.get("world")
            traits = profile.get("traits") or []
            if include_traits and traits:
                trait_str = ", ".join(traits[:8])
            else:
                trait_str = None
            p_lines = ["Persona Profile:"]
            if name:
                p_lines.append(f"- Name: {name}")
            if world:
                p_lines.append(f"- World: {world}")
            if trait_str:
                p_lines.append(f"- Traits: {trait_str}")
            if profile.get("style_notes"):
                p_lines.append(f"- Style Notes: {profile['style_notes'][:220]}")
            parts.append("\n".join(p_lines))

        # Include a few most relevant memories
        memories = self.recall_memory(persona_key, query=None, top_k=6)
        if memories:
            m_lines = ["Long-term memories (most relevant):"]
            for m in memories:
                t = (m.get("text") or "").strip()
                if not t:
                    continue
                t = t.replace("\n", " ")
                if len(t) > 220:
                    t = t[:217] + "…"
                m_lines.append(f"- {t}")
            parts.append("\n".join(m_lines))

        out = "\n\n".join([p for p in parts if p])
        if len(out) > max_chars:
            out = out[: max_chars - 1] + "…"
        return out or ""

    def save_persona_profile(
        self,
        persona_key: str,
        name: Optional[str] = None,
        world: Optional[str] = None,
        personality: Optional[str] = None,
        voice: Optional[str] = None,
        traits: Optional[List[str]] = None,
        style_notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        with self._lock:
            f = self._profile_file(persona_key)
            profile: Dict[str, Any] = {}
            if f.exists():
                try:
                    profile = json.loads(f.read_text(encoding="utf-8"))
                except Exception:
                    profile = {}
            # Merge
            if name is not None:
                profile["name"] = name
            if world is not None:
                profile["world"] = world
            if personality is not None:
                profile["personality"] = personality
            if voice is not None:
                profile["voice"] = voice
            if traits:
                # De-duplicate, preserve order
                seen = set(profile.get("traits") or [])
                merged = list(profile.get("traits") or [])
                for t in traits:
                    if t not in seen:
                        merged.append(t)
                        seen.add(t)
                profile["traits"] = merged
            if style_notes is not None:
                profile["style_notes"] = style_notes
            # Persist
            f.write_text(json.dumps(profile, ensure_ascii=False, indent=2), encoding="utf-8")
            return profile

    def update_personality(
        self,
        persona_key: str,
        traits_add: Optional[List[str]] = None,
        style_notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        traits_add = traits_add or []
        profile = self.save_persona_profile(
            persona_key=persona_key,
            traits=traits_add,
            style_notes=style_notes,
        )
        # Also record a long-term reflection memory
        joined = ", ".join(traits_add) if traits_add else ""
        reflection_bits = []
        if joined:
            reflection_bits.append(f"Traits updated: {joined}")
        if style_notes:
            reflection_bits.append(f"Style notes: {style_notes}")
        if reflection_bits:
            self.save_memory(
                persona_key=persona_key,
                text="; ".join(reflection_bits),
                category="reflection",
                scope="long",
                importance=0.7,
                tags=["personality_update"],
            )
        return profile

    def load_persona_profile(self, persona_key: str) -> Dict[str, Any]:
        f = self._profile_file(persona_key)
        if not f.exists():
            return {}
        try:
            return json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            return {}


# Singleton store used across the app
store = MemoryStore()


# Convenience wrappers expected by other modules

def save(persona_key: str, text: str, category: str = "fact", scope: str = "long", tags: Optional[List[str]] = None, importance: float = 0.5) -> Dict[str, Any]:
    return store.save_memory(persona_key, text, category, scope, tags, importance).to_json()


def recall(persona_key: str, query: Optional[str] = None, top_k: int = 5, categories: Optional[List[str]] = None, include_short_term: bool = True) -> List[Dict[str, Any]]:
    return store.recall_memory(persona_key, query, top_k, categories, include_short_term)


def render_system_memory(persona_key: str, max_chars: int = 1200) -> str:
    return store.render_system_memory(persona_key, max_chars=max_chars)


def save_profile(persona_key: str, name: Optional[str] = None, world: Optional[str] = None, personality: Optional[str] = None, voice: Optional[str] = None, traits: Optional[List[str]] = None, style_notes: Optional[str] = None) -> Dict[str, Any]:
    return store.save_persona_profile(persona_key, name=name, world=world, personality=personality, voice=voice, traits=traits, style_notes=style_notes)


def update_personality(persona_key: str, traits_add: Optional[List[str]] = None, style_notes: Optional[str] = None) -> Dict[str, Any]:
    return store.update_personality(persona_key, traits_add=traits_add, style_notes=style_notes)
