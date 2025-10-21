# Handles the entire hardened, real-time conversation session
# with the Gemini Live API.

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
from firestore_memory import get_firestore_memory
from led_controller import led_controller

# --- MODIFIED: Imported new tool and instruction builder ---
from services import (searcher, send_command_to_mcu,
                      build_character_persona_instructions, blank_key_for_voice,
                      client, motor_tool_decl, shutdown_tool_decl, web_search_tool_decl,
                      persona_switch_tool_decl, character_creation_tool_decl,
                      BASE_SYSTEM_RULES, query_persona_memories, store_persona_memory,
                      analyze_persona_personality, memory_query_tool_decl,
                      memory_store_tool_decl, personality_analysis_tool_decl)
from utils import says_shutdown

# =========================
# USB Audio Detection for Raspberry Pi 5
# =========================
def _detect_usb_microphone():
    """
    Auto-detect USB microphone device index for Raspberry Pi 5.
    Returns None if no USB microphone is found.
    """
    try:
        p = pyaudio.PyAudio()
        info = p.get_host_api_info_by_index(0)
        num_devices = info.get('deviceCount')
        
        for i in range(num_devices):
            device_info = p.get_device_info_by_host_api_device_index(0, i)
            device_name = device_info.get('name', '').lower()
            
            # Look for USB audio devices
            if (device_info.get('maxInputChannels') > 0 and 
                any(keyword in device_name for keyword in ['usb', 'audio', 'microphone', 'mic'])):
                print(f"[SESSION] Found USB microphone: Device {i} - {device_info.get('name')}")
                p.terminate()
                return i
        
        print("[SESSION] No USB microphone found, using default device")
        p.terminate()
        return None
        
    except Exception as e:
        print(f"[SESSION] Error detecting USB microphone: {e}")
        return None

def _detect_usb_speaker():
    """
    Auto-detect USB speaker device index for Raspberry Pi 5.
    Returns None if no USB speaker is found.
    """
    try:
        p = pyaudio.PyAudio()
        info = p.get_host_api_info_by_index(0)
        num_devices = info.get('deviceCount')
        
        for i in range(num_devices):
            device_info = p.get_device_info_by_host_api_device_index(0, i)
            device_name = device_info.get('name', '').lower()
            
            # Look for USB audio devices
            if (device_info.get('maxOutputChannels') > 0 and 
                any(keyword in device_name for keyword in ['usb', 'audio', 'speaker', 'headphone'])):
                print(f"[SESSION] Found USB speaker: Device {i} - {device_info.get('name')}")
                p.terminate()
                return i
        
        print("[SESSION] No USB speaker found, using default device")
        p.terminate()
        return None
        
    except Exception as e:
        print(f"[SESSION] Error detecting USB speaker: {e}")
        return None

# =========================
# Gemini Live Session Main Function
# =========================
async def gemini_live_session():
    """
    Manages a persistent, auto-reconnecting conversation with the Gemini Live API.
    This function will loop internally, trying to maintain a connection, and will
    only exit fully upon an explicit shutdown command or idle timeout.
    """
    state.set_state(state.RobotState.LISTENING)
    
    # --- NEW: Load conversation history from Firestore ---
    firestore_memory = get_firestore_memory()
    if firestore_memory:
        try:
            # Load recent messages from Firestore into the conversation buffer
            recent_messages = firestore_memory.get_recent_messages(count=20)
            print(f"[FIRESTORE] Loaded {len(recent_messages)} messages from Firestore")
            
            # Add messages to the conversation buffer for context
            for message in recent_messages:
                if hasattr(message, 'content'):
                    if hasattr(message, 'type'):
                        if message.type == 'human':
                            state.add_user_utt(message.content)
                        elif message.type == 'ai':
                            state.add_assistant_utt(message.content)
                    else:
                        # Fallback: assume alternating user/assistant based on position
                        pass  # We'll let the normal flow handle this
        except Exception as e:
            print(f"[FIRESTORE] Error loading conversation history: {e}")
    else:
        print("[FIRESTORE] No Firestore memory available")

    # !!! IMPORTANT !!!
    # Auto-detect USB audio devices for Raspberry Pi 5
    # Run list_audio_devices.py to find the correct device indices
    MIC_DEVICE_INDEX = _detect_usb_microphone()
    SPEAKER_DEVICE_INDEX = _detect_usb_speaker()

    p = pyaudio.PyAudio()

    # --- MODIFIED: Added input_device_index ---
    mic_stream = p.open(format=CONFIG["audio"]["format"], channels=CONFIG["audio"]["channels"],
                        rate=CONFIG["audio"]["rate"], input=True,
                        frames_per_buffer=CONFIG["audio"]["chunk_size"],
                        input_device_index=MIC_DEVICE_INDEX)
                        
    # --- MODIFIED: Added output_device_index ---
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

        pending_voice = state.active_voice_name
        pending_persona_key = state.active_persona_key

        def touch():
            nonlocal last_activity
            last_activity = time.monotonic()

        def compose_system_instruction():
            persona = PERSONAS.get(state.active_persona_key, {"prompt": "", "voice": "Kore"})
            extra = state.session_custom_instructions or ""
            memory = state.render_memory_recency()
            brevity_guard = (
                "Always keep answers to 1–2 sentences unless the user explicitly asks for more "
                "(e.g., 'explain', 'details', 'teach me')."
            )
            return (
                (persona["prompt"] + "\n\n" if persona["prompt"] else "") +
                BASE_SYSTEM_RULES + "\n" + brevity_guard + "\n" +
                (("\n" + extra) if extra else "") +
                "\n\n" + memory
            )

        def build_live_config():
            # --- MODIFIED: Add the new character creation tool to the list ---
            all_tools = [motor_tool_decl, shutdown_tool_decl, web_search_tool_decl, persona_switch_tool_decl]
            if state.concierge_waiting_for_description:
                 all_tools.append(character_creation_tool_decl)
            
            # Add memory tools for Jarvis and Alexa personas
            if state.active_persona_key in ["jarvis", "alexa"]:
                all_tools.extend([memory_query_tool_decl, memory_store_tool_decl, personality_analysis_tool_decl])

            return {
                "system_instruction": compose_system_instruction(),
                "response_modalities": ["AUDIO"],
                "tools": all_tools,
                "speech_config": {"voice_config": {"prebuilt_voice_config": {"voice_name": state.active_voice_name}}},
            }
        
        # --- NEW: Updated model ID based on Oct 2025 documentation ---
        live_model_id = LIVE_MODEL

        try:
            print(f"[SESSION] Starting Gemini Live with model {live_model_id}...")
            async with client.aio.live.connect(model=live_model_id, config=build_live_config()) as session:
                reconnect_attempt = 0
                backoff = RECONNECT_BACKOFF_SECONDS
                print("[SESSION] Connected")
                touch()

                if state.startup_hint:
                    await session.send_realtime_input(text=state.startup_hint)
                    state.set_session_state(hint=None, is_concierge_waiting=state.concierge_waiting_for_description)

                async def keepalive():
                    while True:
                        await asyncio.sleep(KEEPALIVE_SECONDS)
                        try:
                            await session.send_realtime_input(text="[[keepalive]]")
                        except Exception:
                            break
                keepalive_task = asyncio.create_task(keepalive())

                async def mic_gen():
                    while state.current_state == state.RobotState.LISTENING:
                        chunk = await asyncio.to_thread(mic_stream.read, CONFIG["audio"]["chunk_size"], False)
                        if mic_enabled_flag["on"]:
                            yield types.Blob(data=chunk, mime_type="audio/pcm;rate=16000")
                            touch()
                        else:
                            await asyncio.sleep(0.02)

                async def send_audio():
                    try:
                        async for blob in mic_gen():
                            await session.send_realtime_input(audio=blob)
                    except (ConnectionClosed, ConnectionClosedOK, asyncio.CancelledError):
                        pass
                send_task = asyncio.create_task(send_audio())

                is_speaking = False
                
                async for msg in session.receive():
                    touch()
                    if getattr(msg, "go_away", None):
                        close_reason = "go_away"; break

                    played = False
                    if hasattr(msg, "data") and isinstance(getattr(msg, "data"), (bytes, bytearray)):
                        if not is_speaking: 
                            is_speaking = True; 
                            mic_enabled_flag["on"] = False
                            # --- NEW: Turn on solid LEDs when assistant is speaking ---
                            led_controller.turn_on()
                        spk_stream.write(msg.data); played = True

                    sc = getattr(msg, "server_content", None)
                    if sc:
                        in_tr = getattr(sc, "input_transcription", None)
                        if in_tr and getattr(in_tr, "text", None):
                            txt = (in_tr.text or "").strip()
                            if txt:
                                state.add_user_utt(txt)
                                if says_shutdown(txt):
                                    print("[SESSION] Shutdown phrase detected in transcription.")
                                    # --- NEW: Turn off LEDs when shutdown phrase is detected ---
                                    led_controller.turn_off()
                                    state.set_state(state.RobotState.SLEEPING)
                                    close_reason = "shutdown_to_sleep"
                                # --- REMOVED: Old logic for concierge text parsing is now replaced by the tool call below ---

                        out_tr = getattr(sc, "output_transcription", None)
                        if out_tr and getattr(out_tr, "text", None):
                            txt = (out_tr.text or "").strip()
                            if txt: state.add_assistant_utt(txt)

                    if is_speaking and not played:
                        is_speaking = False; 
                        mic_enabled_flag["on"] = True
                        # --- NEW: Return to pulsing LEDs when assistant stops speaking ---
                        led_controller.start_pulse()

                    if (time.monotonic() - last_activity) > IDLE_SECONDS:
                        close_reason = "idle_timeout"; break

                    if getattr(msg, "tool_call", None) and getattr(msg.tool_call, "function_calls", None):
                        responses = []
                        for fc in msg.tool_call.function_calls:
                            name = fc.name; args = fc.args or {}; fid = fc.id
                            if name == "motor_command":
                                send_command_to_mcu(args)
                                responses.append(types.FunctionResponse(id=fid, name=name, response={"status":"OK"}))
                            elif name == "shutdown_robot":
                                print("[SESSION] 'shutdown_robot' tool called.")
                                # --- NEW: Turn off LEDs immediately when shutdown is called ---
                                led_controller.turn_off()
                                state.set_state(state.RobotState.SLEEPING)
                                close_reason = "shutdown_to_sleep"
                                responses.append(types.FunctionResponse(id=fid, name=name, response={"status":"OK"}))
                            elif name == "web_search":
                                data = searcher.search(args.get("query"), args.get("max_results"))
                                responses.append(types.FunctionResponse(id=fid, name=name, response=data))
                            # --- NEW: Handle the character creation tool call ---
                            elif name == "save_character_profile":
                                print("[SESSION] 'save_character_profile' tool called.")
                                char_name = args.get("name")
                                char_world = args.get("world")
                                char_personality = args.get("personality")
                                char_voice = args.get("voice")

                                if char_name and char_world and char_personality and char_voice in VOICE_CATALOG:
                                    custom_instr = build_character_persona_instructions(
                                        name=char_name,
                                        world=char_world,
                                        personality=char_personality
                                    )
                                    # Set up the state for the *next* session
                                    state.set_session_state(is_concierge_waiting=False, custom_instructions=custom_instr)
                                    pending_voice = char_voice
                                    pending_persona_key = blank_key_for_voice(char_voice)
                                    close_reason = "persona_switch"
                                    responses.append(types.FunctionResponse(id=fid, name=name, response={"status": "OK"}))
                                else:
                                    responses.append(types.FunctionResponse(id=fid, name=name, response={"status": "ERROR", "message": "Missing required character profile fields."}))

                            elif name == "persona_switch":
                                pk = args.get("persona_key"); vn = args.get("voice_name"); ci = args.get("custom_instructions")
                                if pk and pk in PERSONAS:
                                    pending_persona_key = pk; pending_voice = PERSONAS[pk]["voice"]; state.session_custom_instructions = ci
                                    close_reason="persona_switch"
                                    responses.append(types.FunctionResponse(id=fid,name=name,response={"status":"OK"}))
                                elif vn and vn in VOICE_CATALOG:
                                    pending_voice = vn; pending_persona_key = blank_key_for_voice(vn); state.session_custom_instructions = ci
                                    close_reason="persona_switch"
                                    responses.append(types.FunctionResponse(id=fid, name=name, response={"status":"OK"}))
                                else:
                                    responses.append(types.FunctionResponse(id=fid,name=name,response={"status":"ERROR"}))
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
                        if responses: await session.send_tool_response(function_responses=responses)

                    if close_reason: break
                if not close_reason: close_reason = "server_closed"

        except (ConnectionClosed, ConnectionClosedOK): close_reason = "server_closed"
        except Exception as e: close_reason = f"error: {e}"
        finally:
            if keepalive_task: keepalive_task.cancel()
            if send_task: send_task.cancel()
            print(f"[SESSION] Closing session. Reason: {close_reason or 'client'}", file=sys.stderr)

        if close_reason == "persona_switch":
            state.set_persona(pending_persona_key, pending_voice)
            await asyncio.sleep(RECONNECT_BACKOFF_SECONDS); continue

        if state.current_state != state.RobotState.LISTENING:
            break

        if close_reason == "server_closed" or (time.monotonic() - start_of_session) < SESSION_SHORT_LIFETIME_S:
            if not SESSION_INFINITE_RETRY and reconnect_attempt >= 3: break
            reconnect_attempt += 1
            await asyncio.sleep(backoff); backoff = min(backoff * 1.7, MAX_BACKOFF_SECONDS); continue
        
        break

    if mic_stream: mic_stream.close()
    if spk_stream: spk_stream.close()
    if p: p.terminate()
