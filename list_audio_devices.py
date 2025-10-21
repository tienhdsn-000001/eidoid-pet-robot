# list_audio_devices.py
# A helper script to list all available audio input and output devices
# that PyAudio can detect. This is crucial for finding the correct
# device index to use in your main application on Raspberry Pi 5.

import pyaudio
import platform
import re

def detect_rpi5_audio_devices():
    """
    Detects and returns recommended audio devices for Raspberry Pi 5.
    Prioritizes USB audio devices over built-in audio.
    """
    p = pyaudio.PyAudio()
    info = p.get_host_api_info_by_index(0)
    num_devices = info.get('deviceCount')

    input_devices = []
    output_devices = []
    usb_input_devices = []
    usb_output_devices = []

    print("=== Raspberry Pi 5 Audio Device Detection ===\n")

    # Collect all devices
    for i in range(num_devices):
        device_info = p.get_device_info_by_host_api_device_index(0, i)
        device_name = device_info.get('name', '')
        
        if device_info.get('maxInputChannels') > 0:
            input_devices.append((i, device_name))
            if any(keyword in device_name.lower() for keyword in ['usb', 'audio', 'microphone', 'mic']):
                usb_input_devices.append((i, device_name))
        
        if device_info.get('maxOutputChannels') > 0:
            output_devices.append((i, device_name))
            if any(keyword in device_name.lower() for keyword in ['usb', 'audio', 'speaker', 'headphone']):
                usb_output_devices.append((i, device_name))

    print("--- Input Devices (Microphones) ---")
    for idx, name in input_devices:
        usb_indicator = " [USB]" if any(keyword in name.lower() for keyword in ['usb', 'audio', 'microphone', 'mic']) else ""
        print(f"Device Index: {idx}, Name: {name}{usb_indicator}")

    print("\n--- Output Devices (Speakers) ---")
    for idx, name in output_devices:
        usb_indicator = " [USB]" if any(keyword in name.lower() for keyword in ['usb', 'audio', 'speaker', 'headphone']) else ""
        print(f"Device Index: {idx}, Name: {name}{usb_indicator}")

    # Recommendations
    print("\n=== RECOMMENDATIONS ===")
    
    if usb_input_devices:
        recommended_input = usb_input_devices[0]
        print(f"Recommended Microphone: Device {recommended_input[0]} - {recommended_input[1]}")
    elif input_devices:
        recommended_input = input_devices[0]
        print(f"Recommended Microphone: Device {recommended_input[0]} - {recommended_input[1]}")
    else:
        print("No input devices found!")

    if usb_output_devices:
        recommended_output = usb_output_devices[0]
        print(f"Recommended Speaker: Device {recommended_output[0]} - {recommended_output[1]}")
    elif output_devices:
        recommended_output = output_devices[0]
        print(f"Recommended Speaker: Device {recommended_output[0]} - {recommended_output[1]}")
    else:
        print("No output devices found!")

    p.terminate()
    return usb_input_devices, usb_output_devices

def list_audio_devices():
    """
    Legacy function for backward compatibility.
    """
    return detect_rpi5_audio_devices()

if __name__ == "__main__":
    print("Detecting audio devices on Raspberry Pi 5...")
    print(f"Platform: {platform.system()} {platform.release()}")
    print()
    
    try:
        usb_inputs, usb_outputs = detect_rpi5_audio_devices()
        
        print("\n=== CONFIGURATION INSTRUCTIONS ===")
        print("1. Update wake_word.py with the recommended microphone device index")
        print("2. Update session_manager.py with the recommended speaker device index")
        print("3. If no USB devices are detected, ensure your USB microphone and speaker are connected")
        print("4. Run 'sudo raspi-config' and enable audio if needed")
        
    except Exception as e:
        print(f"Error detecting audio devices: {e}")
        print("Make sure PyAudio is properly installed and audio devices are connected.")
