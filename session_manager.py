# session_manager.py
# Streamlined session manager for Alexa and Jarvis personas

import asyncio
import time
import sys

import pyaudio
from google.genai import types
from websockets.exceptions import ConnectionClosed, ConnectionClosedOK

import state
from config import (CONFIG, LIVE_MODEL, PERSONAS, KEEPALIVE_SECONDS,
                    RECONNECT_BACKOFF_SECONDS, MAX_BACKOFF_SECONDS,
                    SESSION_SHORT_LIFETIME_S, SESSION_INFINITE_RETRY, IDLE_SECONDS,
                    VOICE_CATALOG)
from services import (searcher, client, shutdown_tool_decl, web_search_tool_decl,
                      BASE_SYSTEM_RULES, query_persona_memories, store_persona_memory,
                      analyze_persona_personality, memory_query_tool_decl,
                      memory_store_tool_decl, personality_analysis_tool_decl)
from utils import says_shutdown
from led_controller import led_controller

# =========================
# Gemini Live Session Main Function
# =========================
async def gemini_live_session():
    """
    Manages a persistent, auto-reconnecting conversation with the Gemini Live API.
    Streamlined for Alexa and Jarvis personas only.
    """
    state.set_state(state.RobotState.LISTENING)

    # !!! IMPORTANT !!!
    # Replace None with the device indices from list_audio_devices.py
    MIC_DEVICE_INDEX = None 
    SPEAKER_DEVICE_INDEX = None

    p = pyaudio.PyAudio()

    mic_stream = p.open(format=CONFIG["audio"]["format"], channels=CONFIG["audio"]["channels"],
                        rate=CONFIG["audio"]["rate"], input=True,
                        frames_per_buffer=CONFIG["audio"]["chunk_size"],
                        input_device_index=MIC_DEVICE_INDEX)
                        
    spk_stream = p.open(format=pyaudio.paInt16, channels=CONFIG["audio"]["channels"],
                        rate=CONFIG["audio"]["speaker_rate"], output=True,
                        frames_per_buffer=CONFIG["audio"]["chunk_size"],
                        output_device_index=SPEAKER_DEVICE_INDEX)

    reconnect_attempt = 0
    backoff = RECONNECT_BACKOFF_SECONDS

    while state.current_state == state.RobotState.LISTENING:
        mic_enabled_flag = {"on": True}
        send_task = None
        keepalive_task = None
        close_reason = None
        start_of_session = time.monotonic()
        last_activity = start_of_session

        def touch():
            nonlocal last_activity
            last_activity = time.monotonic()

        def compose_system_instruction():
            persona = PERSONAS.get(state.active_persona_key, {"prompt": "", "voice": "Charon"})
            memory = state.render_memory_recency()
            brevity_guard = (
                "Always keep answers to 1–2 sentences unless the user explicitly asks for more "
                "(e.g., 'explain', 'details', 'teach me')."
            )
            return (
                (persona["prompt"] + "\n\n" if persona["prompt"] else "") +
                BASE_SYSTEM_RULES + "\n" + brevity_guard + "\n\n" + memory
            )

        def build_live_config():
            # Tools available to both Alexa and Jarvis
            all_tools = [
                shutdown_tool_decl, 
                web_search_tool_decl,
                memory_query_tool_decl, 
                memory_store_tool_decl, 
                personality_analysis_tool_decl
            ]

            return {
                "system_instruction": compose_system_instruction(),
                "response_modalities": ["AUDIO"],
                "tools": all_tools,
                "speech_config": {"voice_config": {"prebuilt_voice_config": {"voice_name": state.active_voice_name}}},
            }
        
        live_model_id = LIVE_MODEL

        try:
            print(f"[SESSION] Starting Gemini Live with model {live_model_id} as {state.active_persona_key}...")
            async with client.aio.live.connect(model=live_model_id, config=build_live_config()) as session:
                reconnect_attempt = 0
                backoff = RECONNECT_BACKOFF_SECONDS
                print(f"[SESSION] Connected as {state.active_persona_key}")
                touch()

                # Keepalive task
                async def keepalive():
                    while True:
                        await asyncio.sleep(KEEPALIVE_SECONDS)
                        try:
                            await session.send_realtime_input(text="[[keepalive]]")
                        except Exception:
                            break
                keepalive_task = asyncio.create_task(keepalive())

                # Microphone input generator
                async def mic_gen():
                    while state.current_state == state.RobotState.LISTENING:
                        chunk = await asyncio.to_thread(mic_stream.read, CONFIG["audio"]["chunk_size"], False)
                        if mic_enabled_flag["on"]:
                            yield types.Blob(data=chunk, mime_type="audio/pcm;rate=16000")
                            touch()
                        else:
                            await asyncio.sleep(0.02)

                # Send audio task
                async def send_audio():
                    try:
                        async for blob in mic_gen():
                            await session.send_realtime_input(audio=blob)
                    except (ConnectionClosed, ConnectionClosedOK, asyncio.CancelledError):
                        pass
                send_task = asyncio.create_task(send_audio())

                is_speaking = False
                
                # Main message processing loop
                async for msg in session.receive():
                    touch()
                    if getattr(msg, "go_away", None):
                        close_reason = "go_away"
                        break

                    # Handle audio output
                    played = False
                    if hasattr(msg, "data") and isinstance(getattr(msg, "data"), (bytes, bytearray)):
                        if not is_speaking: 
                            is_speaking = True
                            mic_enabled_flag["on"] = False
                            led_controller.pulse_start()  # Start pulsing LED while speaking
                        spk_stream.write(msg.data)
                        played = True

                    # Handle server content
                    sc = getattr(msg, "server_content", None)
                    if sc:
                        # Handle input transcription
                        in_tr = getattr(sc, "input_transcription", None)
                        if in_tr and getattr(in_tr, "text", None):
                            txt = (in_tr.text or "").strip()
                            if txt:
                                state.add_user_utt(txt)
                                if says_shutdown(txt):
                                    print("[SESSION] Shutdown phrase detected.")
                                    state.set_state(state.RobotState.SLEEPING)
                                    close_reason = "shutdown_to_sleep"

                        # Handle output transcription
                        out_tr = getattr(sc, "output_transcription", None)
                        if out_tr and getattr(out_tr, "text", None):
                            txt = (out_tr.text or "").strip()
                            if txt: 
                                state.add_assistant_utt(txt)

                    # Handle end of speech
                    if is_speaking and not played:
                        is_speaking = False
                        mic_enabled_flag["on"] = True
                        led_controller.pulse_stop()  # Stop pulsing when done speaking
                        led_controller.turn_on()  # Keep LED on while listening

                    # Check for idle timeout
                    if (time.monotonic() - last_activity) > IDLE_SECONDS:
                        close_reason = "idle_timeout"
                        break

                    # Handle tool calls
                    if getattr(msg, "tool_call", None) and getattr(msg.tool_call, "function_calls", None):
                        responses = []
                        for fc in msg.tool_call.function_calls:
                            name = fc.name
                            args = fc.args or {}
                            fid = fc.id
                            
                            if name == "shutdown_robot":
                                print("[SESSION] 'shutdown_robot' tool called.")
                                state.set_state(state.RobotState.SLEEPING)
                                close_reason = "shutdown_to_sleep"
                                responses.append(types.FunctionResponse(id=fid, name=name, response={"status":"OK"}))
                            
                            elif name == "web_search":
                                led_controller.flash(count=1, on_time=0.1, off_time=0.1)  # Quick flash for search
                                data = searcher.search(args.get("query"), args.get("max_results"))
                                responses.append(types.FunctionResponse(id=fid, name=name, response=data))
                            
                            elif name == "query_memories":
                                query = args.get("query", "")
                                memory_type = args.get("memory_type", "all")
                                max_results = args.get("max_results", 5)
                                result = query_persona_memories(state.active_persona_key, query, memory_type, max_results)
                                responses.append(types.FunctionResponse(id=fid, name=name, response=result))
                            
                            elif name == "store_important_memory":
                                content = args.get("content")
                                memory_type = args.get("memory_type")
                                importance = args.get("importance")
                                tags = args.get("tags", [])
                                if content and memory_type and importance:
                                    result = store_persona_memory(state.active_persona_key, content, memory_type, importance, tags)
                                    responses.append(types.FunctionResponse(id=fid, name=name, response=result))
                                else:
                                    responses.append(types.FunctionResponse(id=fid, name=name, response={"status": "ERROR", "message": "Missing required parameters"}))
                            
                            elif name == "analyze_personality_development":
                                include_history = args.get("include_history", False)
                                result = analyze_persona_personality(state.active_persona_key, include_history)
                                responses.append(types.FunctionResponse(id=fid, name=name, response=result))
                        
                        if responses: 
                            await session.send_tool_response(function_responses=responses)

                    if close_reason: 
                        break
                
                if not close_reason: 
                    close_reason = "server_closed"

        except (ConnectionClosed, ConnectionClosedOK): 
            close_reason = "server_closed"
        except Exception as e: 
            close_reason = f"error: {e}"
        finally:
            if keepalive_task: 
                keepalive_task.cancel()
            if send_task: 
                send_task.cancel()
            print(f"[SESSION] Closing session. Reason: {close_reason or 'client'}", file=sys.stderr)
            led_controller.turn_off()  # Turn off LED when session ends

        if state.current_state != state.RobotState.LISTENING:
            break

        # Handle reconnection logic
        if close_reason == "server_closed" or (time.monotonic() - start_of_session) < SESSION_SHORT_LIFETIME_S:
            if not SESSION_INFINITE_RETRY and reconnect_attempt >= 3: 
                break
            reconnect_attempt += 1
            await asyncio.sleep(backoff)
            backoff = min(backoff * 1.7, MAX_BACKOFF_SECONDS)
            continue
        
        break

    if mic_stream: 
        mic_stream.close()
    if spk_stream: 
        spk_stream.close()
    if p: 
        p.terminate()