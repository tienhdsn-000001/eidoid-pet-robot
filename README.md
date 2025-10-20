# Persona Memory Service

Evolving working memory for two personas (Alexa and Jarvis) with Gemini integration. Designed to run on a Raspberry Pi 5.

## Features
- Separate working memory namespaces for Alexa and Jarvis
- SQLite-backed memory with LRU-style eviction by count and token budget
- Persona evolution: every 7th loop, persona evolution note is appended
- Minimal Gemini REST client (Oct 2025 API shape) using `httpx`
- Lightweight dependencies suitable for a Raspberry Pi 5

## Requirements
- Python 3.10+
- `GEMINI_API_KEY` environment variable

Optional env vars (with defaults):
- `MEMORY_DB_PATH=/workspace/data/memory.db`
- `GEMINI_MODEL=gemini-1.5-pro`
- `GEMINI_API_BASE=https://generativelanguage.googleapis.com`
- `MAX_ITEMS_PER_PERSONA=2000` (adjust down if storage constrained)
- `MAX_TOKENS_PER_PERSONA=200000` (approximate token budget)
- `REQUEST_TIMEOUT_SECONDS=30`

## Install
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Run
```bash
export GEMINI_API_KEY=...  # required
persona-memory
```

Stop with Ctrl+C.

## Notes on Evolution
- Every 7th iteration for a persona, a "Persona evolution checkpoint" note is recorded.
- The `system_prompt` incorporates summarized recent memory to guide adaptive behavior.

## Implementation Notes
- Token counting uses a simple heuristic; budgets are approximate.
- SQLite is configured for WAL and moderate mmap for Pi-friendly performance.
