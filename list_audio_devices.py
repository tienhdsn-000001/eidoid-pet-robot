# list_audio_devices.py
# A helper script to list all available audio input and output devices
# that PyAudio can detect. This is crucial for finding the correct
# device index to use in your main application.

import pyaudio

def list_audio_devices():
    """
    Prints a list of all available audio input and output devices,
    along with their indices.
    """
    p = pyaudio.PyAudio()
    info = p.get_host_api_info_by_index(0)
    num_devices = info.get('deviceCount')

    print("--- Input Devices ---")
    for i in range(num_devices):
        device_info = p.get_device_info_by_host_api_device_index(0, i)
        if device_info.get('maxInputChannels') > 0:
            print(f"Device Index: {i}, Name: {device_info.get('name')}")

    print("\n--- Output Devices ---")
    for i in range(num_devices):
        device_info = p.get_device_info_by_host_api_device_index(0, i)
        if device_info.get('maxOutputChannels') > 0:
            print(f"Device Index: {i}, Name: {device_info.get('name')}")
            
    p.terminate()

if __name__ == "__main__":
    print("Searching for audio devices...")
    list_audio_devices()
    print("\nRun this script on your Raspberry Pi.")
    print("Note the 'Device Index' for your desired microphone and speaker,")
    print("then use those numbers in the wake_word.py and session_manager.py files.")
