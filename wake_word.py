# wake_word.py
# An efficient, offline process that listens for wake words.

import time
import sys
from pathlib import Path
import re

import numpy as np
import pyaudio
from openwakeword.model import Model
import openwakeword as oww
import onnxruntime as ort

import state
from config import CONFIG, DESIRED_WAKE_MODELS, WAKE_THRESH, POST_SESSION_COOLDOWN_S, ARMING_DELAY_S, PERSONAS
from utils import pretty_model_name, canonical_model_key

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
                print(f"[WAKE_WORD] Found USB microphone: Device {i} - {device_info.get('name')}")
                p.terminate()
                return i
        
        print("[WAKE_WORD] No USB microphone found, using default device")
        p.terminate()
        return None
        
    except Exception as e:
        print(f"[WAKE_WORD] Error detecting USB microphone: {e}")
        return None

# Suppress the benign ONNX warnings
ort.set_default_logger_severity(3)

# =========================
# Wake-word model discovery
# =========================
def _models_dir() -> Path:
    try:
        base = Path(oww.__file__).parent
        return base / "resources" / "models"
    except Exception:
        return Path(".")

def _discover_installed_models(desired_names):
    mdir = _models_dir()
    def norm(s: str) -> str:
        s = Path(s).stem.lower().replace("-", "_").replace(" ", "_")
        return re.sub(r"_+", "_", s)

    onnx_by_key = {norm(p.stem): p for p in mdir.glob("*.onnx")}
    available, missing = [], []
    for name in desired_names:
        key_exact = norm(name)
        key_base = re.sub(r"_v\d+(\.\d+)*$", "", key_exact)
        candidate = None
        if key_exact in onnx_by_key:
            candidate = onnx_by_key[key_exact]
        else:
            for k, p in onnx_by_key.items():
                if k.startswith(key_base):
                    candidate = p
                    break
        if candidate:
            available.append(str(candidate))
        else:
            missing.append(name)
    return available, missing

# =========================
# Main Wake Word Listener Loop
# =========================
def run_wake_word_listener():
    # !!! IMPORTANT !!!
    # Auto-detect USB microphone for Raspberry Pi 5
    # Run list_audio_devices.py to find the correct device index
    MIC_DEVICE_INDEX = _detect_usb_microphone() 
    
    backoff = 1.0
    while state.current_state == state.RobotState.SLEEPING:
        cooldown_left = max(0.0, POST_SESSION_COOLDOWN_S - (time.monotonic() - state.last_session_end))
        if cooldown_left > 0:
            print(f"[WAKE_WORD] Cooldown period: {cooldown_left:.1f}s remaining...")
            time.sleep(cooldown_left)

        available, _ = _discover_installed_models(DESIRED_WAKE_MODELS)
        if not available:
            print("[WAKE_WORD] No .onnx models found. Retrying...", file=sys.stderr)
            time.sleep(min(backoff, 5.0)); backoff = min(backoff * 1.6, 5.0)
            continue

        p = None; mic = None
        try:
            owwModel = Model(wakeword_models=available, inference_framework="onnx")
            backoff = 1.0

            p = pyaudio.PyAudio()
            
            # --- MODIFIED: Added input_device_index ---
            # This tells PyAudio exactly which microphone to listen to.
            mic = p.open(rate=CONFIG["audio"]["rate"], channels=CONFIG["audio"]["channels"],
                         format=CONFIG["audio"]["format"], input=True,
                         frames_per_buffer=CONFIG["audio"]["chunk_size"],
                         input_device_index=MIC_DEVICE_INDEX)
            
            pretty_targets = ", ".join([pretty_model_name(n) for n in available])
            print(f"[WAKE_WORD] Listening for: {pretty_targets}")

            # --- NEW SIMPLIFIED LOGIC ---
            # Create a map of simple names to full paths for easy lookup
            model_paths = {canonical_model_key(p): p for p in available}
            jarvis_path = model_paths.get('hey_jarvis_v0.1')
            alexa_path = model_paths.get('alexa_v0.1')
            weather_path = model_paths.get('weather_v0.1')

            start_t = time.monotonic()
            while state.current_state == state.RobotState.SLEEPING:
                data = mic.read(CONFIG["audio"]["chunk_size"])
                arr = np.frombuffer(data, dtype=np.int16)
                pred = owwModel.predict(arr)

                 # --- DEBUGGING RESTORED ---
                # This line prints the live scores from the model to the console.
                # It uses a carriage return `\r` to update the line in place.
                sys.stdout.write("\r[DEBUG] " + str({Path(k).stem: round(float(v), 5) for k, v in pred.items()}) + "   ")
                sys.stdout.flush()

                if pred.get('hey_jarvis_v0.1') >= 0.8:
                    state.set_persona("jarvis", PERSONAS["jarvis"]["voice"])
                    state.set_session_state()
                    state.set_state(state.RobotState.WAKING)
                    return
                elif pred.get('alexa_v0.1') >= 0.8:
                    state.set_persona("alexa", PERSONAS["alexa"]["voice"])
                    state.set_session_state()
                    state.set_state(state.RobotState.WAKING)
                    return
                elif pred.get('weather_v0.1') >= 0.8:
                    state.set_persona("aoede_concierge", PERSONAS["aoede_concierge"]["voice"])
                    hint = ("Speak out loud now. First, answer: What's the weather right now? "
                            "Then, say out loud exactly: 'Who would you like to talk to today? Describe them for me.'")
                    state.set_session_state(hint=hint, is_concierge_waiting=True)
                    state.set_state(state.RobotState.WAKING)
                    return
        except Exception as e:
            print(f"[WAKE_WORD] Error: {e}", file=sys.stderr)
            time.sleep(min(backoff, 5.0)); backoff = min(backoff * 1.6, 5.0)
        finally:
            if mic: mic.close()
            if p: p.terminate()
