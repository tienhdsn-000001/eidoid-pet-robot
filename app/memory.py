from __future__ import annotations

import json
import logging
import sqlite3
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Tuple

from .config import settings

logger = logging.getLogger(__name__)


@dataclass
class MemoryItem:
    persona: str
    role: str  # e.g., system|user|assistant|note
    content: str
    created_at: float
    tokens: int


class MemoryStore:
    """SQLite-backed working memory with simple token-aware quotas.

    - Separate namespace per persona (e.g., Alexa, Jarvis)
    - Append-only with soft eviction via LRU when exceeding quotas
    - Token estimation uses a rough heuristic to avoid external deps
    """

    def __init__(self, db_path: str | Path) -> None:
        self.db_path = str(db_path)
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._init_db()

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS memory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    persona TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    tokens INTEGER NOT NULL,
                    last_access REAL NOT NULL
                );
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_memory_persona ON memory(persona)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_memory_access ON memory(persona, last_access)"
            )

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=30, isolation_level=None)
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        conn.execute("PRAGMA temp_store=MEMORY;")
        conn.execute("PRAGMA mmap_size=134217728;")  # 128MB
        return conn

    @staticmethod
    def _estimate_tokens(text: str) -> int:
        # Rough heuristic: ~4 chars/token; clamp at minimum 1 for non-empty
        if not text:
            return 0
        est = max(1, int(len(text) / 4))
        # Adjust upward for whitespace-sparse text
        if len(text.split()) <= max(1, len(text) // 12):
            est = int(est * 1.2)
        return est

    def add(self, persona: str, role: str, content: str) -> int:
        created_at = time.time()
        tokens = self._estimate_tokens(content)
        with self._lock, self._connect() as conn:
            cur = conn.execute(
                "INSERT INTO memory(persona, role, content, created_at, tokens, last_access) VALUES (?, ?, ?, ?, ?, ?)",
                (persona, role, content, created_at, tokens, created_at),
            )
            self._evict_if_needed(conn, persona)
            return int(cur.lastrowid)

    def _evict_if_needed(self, conn: sqlite3.Connection, persona: str) -> None:
        # Evict by count
        max_items = settings.max_items_per_persona
        row = conn.execute(
            "SELECT COUNT(*) FROM memory WHERE persona=?",
            (persona,),
        ).fetchone()
        count = int(row[0]) if row else 0
        if count > max_items:
            to_delete = count - max_items
            conn.execute(
                "DELETE FROM memory WHERE id IN (SELECT id FROM memory WHERE persona=? ORDER BY last_access ASC LIMIT ?)",
                (persona, to_delete),
            )

        # Evict by tokens (approx)
        max_tokens = settings.max_total_tokens_per_persona
        row = conn.execute(
            "SELECT COALESCE(SUM(tokens), 0) FROM memory WHERE persona=?",
            (persona,),
        ).fetchone()
        total_tokens = int(row[0]) if row else 0
        if total_tokens > max_tokens:
            # Remove least recently accessed until under budget
            while total_tokens > max_tokens:
                row = conn.execute(
                    "SELECT id, tokens FROM memory WHERE persona=? ORDER BY last_access ASC LIMIT 1",
                    (persona,),
                ).fetchone()
                if not row:
                    break
                conn.execute("DELETE FROM memory WHERE id=?", (int(row[0]),))
                total_tokens -= int(row[1])

    def get_recent(self, persona: str, limit: int = 50) -> List[MemoryItem]:
        with self._lock, self._connect() as conn:
            rows = conn.execute(
                "SELECT persona, role, content, created_at, tokens FROM memory WHERE persona=? ORDER BY created_at DESC LIMIT ?",
                (persona, limit),
            ).fetchall()
            # touch access time
            conn.execute(
                "UPDATE memory SET last_access=? WHERE persona=?",
                (time.time(), persona),
            )
        return [
            MemoryItem(
                persona=row[0], role=row[1], content=row[2], created_at=row[3], tokens=row[4]
            )
            for row in rows
        ]

    def summarize(self, persona: str, max_chars: int = 2000) -> str:
        """Simple summary by concatenation from newest to oldest under char budget."""
        items = self.get_recent(persona, limit=500)
        acc: list[str] = []
        total = 0
        for item in items:
            piece = f"[{item.role}] {item.content}\n"
            if total + len(piece) > max_chars:
                break
            acc.append(piece)
            total += len(piece)
        return "".join(acc)
