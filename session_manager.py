# Handles the entire hardened, real-time conversation session
# with the Gemini Live API.

import asyncio
import time
import sys
import os
import numpy
from scipy import signal

import pyaudio
from google.genai import types
from websockets.exceptions import ConnectionClosed, ConnectionClosedOK

import state
from config import (CONFIG, LIVE_MODEL, PERSONAS, KEEPALIVE_SECONDS,
                    RECONNECT_BACKOFF_SECONDS, MAX_BACKOFF_SECONDS,
                    SESSION_SHORT_LIFETIME_S, SESSION_INFINITE_RETRY, IDLE_SECONDS,
                    VOICE_CATALOG, SLEEP_INACTIVITY_TIMEOUT_S, SHUTDOWN_INACTIVITY_TIMEOUT_S,
                    VOICE_ACTIVITY_THRESHOLD)
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
        # Suppress ALSA errors during detection
        null_fd = os.open('/dev/null', os.O_WRONLY)
        original_stderr = os.dup(2)
        os.dup2(null_fd, 2)
        
        p = pyaudio.PyAudio()
        info = p.get_host_api_info_by_index(0)
        num_devices = info.get('deviceCount')
        
        for i in range(num_devices):
            device_info = p.get_device_info_by_host_api_device_index(0, i)
            device_name = device_info.get('name', '').lower()
            
            # Look for USB audio devices
            if (device_info.get('maxInputChannels') > 0 and 
                any(keyword in device_name for keyword in ['usb', 'audio', 'microphone', 'mic'])):
                os.dup2(original_stderr, 2)
                os.close(null_fd)
                print(f"[SESSION] Found USB microphone: Device {i} - {device_info.get('name')}")
                p.terminate()
                return i
        
        os.dup2(original_stderr, 2)
        os.close(null_fd)
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
        # Suppress ALSA errors during detection
        null_fd = os.open('/dev/null', os.O_WRONLY)
        original_stderr = os.dup(2)
        os.dup2(null_fd, 2)
        
        p = pyaudio.PyAudio()
        info = p.get_host_api_info_by_index(0)
        num_devices = info.get('deviceCount')
        
        for i in range(num_devices):
            device_info = p.get_device_info_by_host_api_device_index(0, i)
            device_name = device_info.get('name', '').lower()
            
            # Look for USB audio devices
            if (device_info.get('maxOutputChannels') > 0 and 
                any(keyword in device_name for keyword in ['usb', 'audio', 'speaker', 'headphone'])):
                os.dup2(original_stderr, 2)
                os.close(null_fd)
                print(f"[SESSION] Found USB speaker: Device {i} - {device_info.get('name')}")
                p.terminate()
                return i
        
        os.dup2(original_stderr, 2)
        os.close(null_fd)
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

    # Suppress ALSA errors during initialization
    null_fd = os.open('/dev/null', os.O_WRONLY)
    original_stderr = os.dup(2)
    os.dup2(null_fd, 2)
    
    p = pyaudio.PyAudio()
    
    # Check microphone device capabilities and use appropriate sample rate
    if MIC_DEVICE_INDEX is not None:
        mic_info = p.get_device_info_by_index(MIC_DEVICE_INDEX)
        mic_rate = int(mic_info['defaultSampleRate'])
    else:
        mic_rate = CONFIG["audio"]["rate"]
    
    # Check speaker device capabilities and use appropriate sample rate
    if SPEAKER_DEVICE_INDEX is not None:
        speaker_info = p.get_device_info_by_index(SPEAKER_DEVICE_INDEX)
        speaker_rate = int(speaker_info['defaultSampleRate'])
    else:
        speaker_rate = CONFIG["audio"]["speaker_rate"]
    
    # Restore stderr to print device info
    os.dup2(original_stderr, 2)
    os.close(null_fd)
    print(f"[SESSION] Microphone sample rate: {mic_rate}")
    print(f"[SESSION] Speaker sample rate: {speaker_rate}")
    
    # Suppress ALSA errors when opening streams
    null_fd = os.open('/dev/null', os.O_WRONLY)
    os.dup2(null_fd, 2)

    # --- MODIFIED: Use microphone's native sample rate ---
    mic_stream = p.open(format=CONFIG["audio"]["format"], channels=CONFIG["audio"]["channels"],
                        rate=mic_rate, input=True,
                        frames_per_buffer=CONFIG["audio"]["chunk_size"],
                        input_device_index=MIC_DEVICE_INDEX)
                        
    # --- MODIFIED: Added output_device_index and use device's native sample rate ---
    spk_stream = p.open(format=pyaudio.paInt16, channels=CONFIG["audio"]["channels"],
                        rate=speaker_rate, output=True,
                        frames_per_buffer=CONFIG["audio"]["chunk_size"],
                        output_device_index=SPEAKER_DEVICE_INDEX)
    
    # Restore stderr after opening streams
    os.dup2(original_stderr, 2)
    os.close(null_fd)

    reconnect_attempt = 0
    backoff = RECONNECT_BACKOFF_SECONDS

    while state.current_state == state.RobotState.LISTENING:
        mic_enabled_flag = {"on": True}
        send_task = None
        keepalive_task = None
        close_reason = None
        start_of_session = time.monotonic()
        last_activity = start_of_session
        last_voice_activity = start_of_session  # Track last time voice input was detected

        pending_voice = state.active_voice_name
        pending_persona_key = state.active_persona_key

        def touch():
            nonlocal last_activity
            last_activity = time.monotonic()
        
        def touch_voice():
            """Track voice activity separately from other activity"""
            nonlocal last_voice_activity
            last_voice_activity = time.monotonic()

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
                    # Gemini expects 24kHz audio
                    gemini_rate = 24000
                    while state.current_state == state.RobotState.LISTENING:
                        chunk = await asyncio.to_thread(mic_stream.read, CONFIG["audio"]["chunk_size"], False)
                        if mic_enabled_flag["on"]:
                            # Apply microphone gain amplification
                            audio_data = numpy.frombuffer(chunk, dtype=numpy.int16)
                            mic_gain = CONFIG["audio"].get("mic_gain", 1.0)
                            if mic_gain != 1.0:
                                audio_data = numpy.clip(audio_data * mic_gain, -32768, 32767).astype(numpy.int16)
                            
                            # --- NEW: Detect voice activity by analyzing volume ---
                            # Calculate RMS (root mean square) volume
                            volume_rms = numpy.sqrt(numpy.mean(numpy.square(audio_data)))
                            # Normalize volume (int16 range is -32768 to 32767)
                            normalized_volume = volume_rms / 32768.0
                            
                            # Check if volume exceeds threshold (voice activity detected)
                            if normalized_volume > VOICE_ACTIVITY_THRESHOLD:
                                touch_voice()
                            
                            # Resample from mic_rate to gemini_rate if needed
                            if mic_rate != gemini_rate:
                                num_samples = int(len(audio_data) * gemini_rate / mic_rate)
                                audio_data = signal.resample(audio_data, num_samples).astype(numpy.int16)
                            
                            chunk = audio_data.tobytes()
                            yield types.Blob(data=chunk, mime_type=f"audio/pcm;rate={gemini_rate}")
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
                        
                        # Gemini outputs audio at 24kHz, but speaker runs at 48kHz
                        # Resample to match speaker's sample rate to fix pitch
                        audio_data = numpy.frombuffer(msg.data, dtype=numpy.int16)
                        gemini_rate = 24000
                        
                        # Resample from Gemini's 24kHz to speaker's 48kHz
                        if speaker_rate != gemini_rate:
                            num_samples = int(len(audio_data) * speaker_rate / gemini_rate)
                            audio_data = signal.resample(audio_data, num_samples).astype(numpy.int16)
                        
                        # Apply volume control
                        volume = CONFIG["audio"].get("volume", 0.8)
                        audio_data = (audio_data * volume).astype(numpy.int16)
                        spk_stream.write(audio_data.tobytes())
                        played = True

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

                    # --- NEW: Check for inactivity timeouts based on voice activity ---
                    time_since_voice = time.monotonic() - last_voice_activity
                    
                    # Check for extended inactivity (shutdown)
                    if time_since_voice > SHUTDOWN_INACTIVITY_TIMEOUT_S:
                        print(f"[SESSION] No voice activity for {SHUTDOWN_INACTIVITY_TIMEOUT_S/60:.1f} minutes. Shutting down system.")
                        # Turn off LEDs before shutdown
                        led_controller.turn_off()
                        # Call shutdown_robot through the tool mechanism
                        os.system("sudo shutdown -h now")
                        close_reason = "shutdown_to_sleep"
                        break
                    
                    # Check for sleep inactivity (return to sleep loop)
                    if time_since_voice > SLEEP_INACTIVITY_TIMEOUT_S:
                        print(f"[SESSION] No voice activity for {SLEEP_INACTIVITY_TIMEOUT_S/60:.1f} minutes. Returning to sleep.")
                        # Turn off LEDs before returning to sleep
                        led_controller.turn_off()
                        state.set_state(state.RobotState.SLEEPING)
                        close_reason = "sleep_timeout"
                        break
                    
                    # Original idle timeout (kept for backward compatibility)
                    if (time.monotonic() - last_activity) > IDLE_SECONDS:
                        close_reason = "idle_timeout"; break

                    if getattr(msg, "tool_call", None) and getattr(msg.tool_call, "function_calls", None):
                        responses = []
                        for fc in msg.tool_call.function_calls:
                            name = fc.name; args = fc.args or {}; fid = fc.id
                            print(f"[DEBUG] Tool call received: {name} with args: {args}")
                            if name == "motor_command":
                                print("[DEBUG] Motor command received but DISABLED (motors deprecated)")
                                # --- DEPRECATED: Motor functions temporarily disabled ---
                                # send_command_to_mcu(args)
                                responses.append(types.FunctionResponse(id=fid, name=name, response={"status":"DISABLED", "message":"Motor functions are temporarily disabled"}))
                            elif name == "shutdown_robot":
                                print("[DEBUG] Shutdown command triggered")
                                print("[SESSION] 'shutdown_robot' tool called.")
                                # --- NEW: Turn off LEDs immediately when shutdown is called ---
                                led_controller.turn_off()
                                state.set_state(state.RobotState.SLEEPING)
                                close_reason = "shutdown_to_sleep"
                                responses.append(types.FunctionResponse(id=fid, name=name, response={"status":"OK"}))
                            elif name == "web_search":
                                print(f"[DEBUG] Web search: {args.get('query')}")
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

        # --- NEW: Handle sleep timeout (return to sleep loop) ---
        if close_reason == "sleep_timeout":
            # State was already set to SLEEPING, just break out of loop
            break

        # --- NEW: Handle shutdown (system is shutting down) ---
        if close_reason == "shutdown_to_sleep":
            # System shutdown command already executed, just break
            break

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
