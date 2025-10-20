from __future__ import annotations

import asyncio
import logging
import signal
from typing import Optional

from .config import settings
from .gemini_client import GeminiClient
from .logging_setup import setup_logging
from .memory import MemoryStore
from .persona import Persona


async def run_loop() -> None:
    setup_logging()
    logger = logging.getLogger("app")

    memory = MemoryStore(settings.db_path)
    alexa = Persona("Alexa", [
        "helpful", "concise", "context-aware", "adaptive", "warm"
    ], memory)
    jarvis = Persona("Jarvis", [
        "proactive", "technical", "witty", "efficient", "adaptive"
    ], memory)

    client = GeminiClient()

    shutdown = asyncio.Event()

    def _handle_sig(*_: object) -> None:
        shutdown.set()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, _handle_sig)

    personas = [alexa, jarvis]
    i = 0
    logger.info("Starting main loop. Press Ctrl+C to exit.")

    try:
        while not shutdown.is_set():
            persona = personas[i % len(personas)]
            evolved = persona.evolve_if_due()

            system_prompt = persona.system_prompt()
            user_prompt = "Briefly reflect on a new preference or habit based on memory."

            try:
                reply = await client.generate(system_prompt, user_prompt)
            except Exception as exc:  # noqa: BLE001
                logger.warning("Gemini generate failed: %s", exc)
                reply = "(reflection skipped due to API error)"

            persona.remember("assistant", reply)

            # Sleep a bit to simulate loop pace without burning CPU
            await asyncio.sleep(2)
            i += 1
    finally:
        await client.aclose()


def main() -> None:
    try:
        asyncio.run(run_loop())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
