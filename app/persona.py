from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import List

from .memory import MemoryStore

logger = logging.getLogger(__name__)


@dataclass
class Persona:
    name: str
    base_traits: List[str]
    memory: MemoryStore
    cycle_count: int = 0

    def system_prompt(self) -> str:
        summary = self.memory.summarize(self.name, max_chars=2000)
        traits = ", ".join(self.base_traits)
        return (
            f"You are {self.name}. You evolve based on cumulative memory.\n"
            f"Core traits: {traits}.\n"
            f"Recent memory:\n{summary}\n"
            f"When responding, incorporate what you have learned; avoid rigid role-play."
        )

    def remember(self, role: str, content: str) -> None:
        self.memory.add(self.name, role, content)

    def evolve_if_due(self) -> bool:
        self.cycle_count += 1
        if self.cycle_count % 7 != 0:
            return False
        # Append an evolution note to memory
        evolution_note = (
            "Persona evolution checkpoint: Consolidate recent experiences into updated tendencies "
            "and preferences. Prefer adaptive behavior over static characterization."
        )
        self.remember("note", evolution_note)
        return True
