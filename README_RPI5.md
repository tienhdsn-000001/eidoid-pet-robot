# Eidoid Pet Robot - Raspberry Pi 5 Edition

A voice-controlled AI pet robot featuring dual personas (Jarvis and Alexa) with persistent memory, designed specifically for Raspberry Pi 5. The robot uses Google's Gemini Live API for natural conversation and includes LED control, wake word detection, and Firestore integration for persistent memory.

## Features

- **Dual AI Personas**: Switch between Jarvis (deep, authoritative) and Alexa (friendly, upbeat)
- **Wake Word Detection**: "Hey Jarvis", "Alexa", or "What's the weather" to activate
- **Persistent Memory**: Conversations and preferences stored in Google Firestore
- **LED Control**: Visual feedback through USB-connected Pico microcontroller
- **USB Audio Support**: Works with USB microphones and speakers
- **Auto-start Service**: Runs automatically on boot
- **Raspberry Pi 5 Optimized**: Optimized for Raspberry Pi 5 hardware

## Hardware Requirements

### Required Hardware
- Raspberry Pi 5 (4GB or 8GB recommended)
- USB Microphone (tested with common USB audio devices)
- USB Speaker or Headphones
- Raspberry Pi Pico (for LED control)
- MicroSD card (32GB+ recommended)
- Power supply for Raspberry Pi 5

### Optional Hardware
- USB hub (if you need more USB ports)
- Case for Raspberry Pi 5
- Heat sink or fan (recommended for sustained use)

## Software Requirements

- Raspberry Pi OS (64-bit) - Latest version
- Python 3.9 or higher
- Google Cloud Project with Firestore enabled
- Google Gemini API access

## Quick Start

### 1. Initial Setup

1. **Flash Raspberry Pi OS** to your microSD card
2. **Enable SSH** and **WiFi** on first boot
3. **Connect to your Raspberry Pi** via SSH:
   ```bash
   ssh pi@your-pi-ip-address
   ```

### 2. Clone and Setup

```bash
# Clone the repository
git clone <your-repo-url>
cd eidoid-pet-robot

# Switch to Raspberry Pi 5 branch
git checkout rpi5-adaptation

# Run the automated setup script
chmod +x setup_rpi5.sh
./setup_rpi5.sh
```

### 3. Configure API Keys

1. **Get your Google API key** from [Google AI Studio](https://makersuite.google.com/app/apikey)
2. **Create a Google Cloud Project** and enable Firestore
3. **Download your service account JSON key** from Google Cloud Console
4. **Configure environment variables**:
   ```bash
   cp .env.template .env
   nano .env
   ```

   Fill in your credentials:
   ```env
   GOOGLE_API_KEY=your_actual_api_key_here
   GOOGLE_APPLICATION_CREDENTIALS=/home/pi/eidoid-pet-robot/your-service-account-key.json
   FIRESTORE_PROJECT_ID=your-project-id
   ```

### 4. Test Audio Devices

```bash
# Activate virtual environment
source .venv/bin/activate

# Test audio device detection
python list_audio_devices.py
```

Note the device indices for your microphone and speaker.

### 5. First Run

```bash
# Test the robot
python main.py
```

## Detailed Setup Instructions

### Audio Configuration

The robot automatically detects USB audio devices, but you can manually configure them:

1. **Run audio detection**:
   ```bash
   python list_audio_devices.py
   ```

2. **Update device indices** in `wake_word.py` and `session_manager.py` if needed

3. **Test audio**:
   ```bash
   # Test microphone
   arecord -l
   
   # Test speaker
   aplay -l
   ```

### LED Control Setup

The robot uses a Raspberry Pi Pico for LED control:

1. **Flash the Pico** with the provided firmware (if available)
2. **Connect via USB** to the Raspberry Pi 5
3. **Verify connection**:
   ```bash
   ls /dev/ttyUSB*
   ```

### Firestore Setup

1. **Create a Google Cloud Project**
2. **Enable Firestore API**
3. **Create a service account** with Firestore permissions
4. **Download the JSON key** and place it in your project directory
5. **Update the project ID** in your `.env` file

### System Service Setup

To run the robot automatically on boot:

```bash
# Enable the service
sudo systemctl enable eidoid-robot.service

# Start the service
sudo systemctl start eidoid-robot.service

# Check status
sudo systemctl status eidoid-robot.service

# View logs
sudo journalctl -u eidoid-robot.service -f
```

## Usage

### Basic Commands

- **"Hey Jarvis"** - Activates Jarvis persona (deep, authoritative voice)
- **"Alexa"** - Activates Alexa persona (friendly, upbeat voice)  
- **"What's the weather"** - Gets weather and prompts for character creation
- **"Thank you for your time"** - Ends conversation and returns to sleep

### LED Indicators

- **Off** - Robot is sleeping
- **Pulsing** - Robot is waking up or processing
- **Solid** - Robot is actively listening/responding

### Memory System

The robot remembers:
- Past conversations
- User preferences
- Personality development over time
- Context from previous sessions

## Troubleshooting

### Audio Issues

**Problem**: No audio input/output detected
```bash
# Check audio devices
python list_audio_devices.py

# Test microphone
arecord -f cd -d 5 test.wav
aplay test.wav

# Check audio permissions
groups $USER
```

**Problem**: Poor audio quality
- Ensure USB devices are properly connected
- Check for audio interference
- Try different USB ports

### LED Control Issues

**Problem**: LEDs not responding
```bash
# Check USB connection
ls /dev/ttyUSB*

# Test serial communication
python -c "import serial; print(serial.Serial('/dev/ttyUSB0', 115200).readline())"
```

### Service Issues

**Problem**: Service won't start
```bash
# Check service status
sudo systemctl status eidoid-robot.service

# View detailed logs
sudo journalctl -u eidoid-robot.service --no-pager

# Restart service
sudo systemctl restart eidoid-robot.service
```

### API Issues

**Problem**: Google API errors
- Verify API key is correct
- Check service account permissions
- Ensure Firestore is enabled
- Check internet connectivity

## File Structure

```
eidoid-pet-robot/
├── main.py                 # Main application entry point
├── config.py              # Configuration settings
├── wake_word.py           # Wake word detection
├── session_manager.py     # Gemini Live session management
├── led_controller.py      # LED control via Pico
├── firestore_memory.py    # Persistent memory system
├── state.py               # Application state management
├── utils.py               # Utility functions
├── requirements.txt       # Python dependencies
├── setup_rpi5.sh         # Automated setup script
├── list_audio_devices.py  # Audio device detection
├── .env.template         # Environment variables template
└── README_RPI5.md        # This file
```

## Configuration Options

### Audio Settings
- Sample rate: 16kHz (input), 24kHz (output)
- Channels: Mono
- Format: 16-bit PCM

### Wake Word Settings
- Threshold: 0.8 (adjustable in `wake_word.py`)
- Models: hey_jarvis_v0.1, alexa_v0.1, weather_v0.1
- Cooldown: 5 seconds between sessions

### LED Settings
- GPIO Pin: 17 (configurable in `config.py`)
- Serial: 115200 baud
- Commands: ON, OFF, PULSE_START, PULSE_STOP

## Performance Optimization

### For Raspberry Pi 5
- Use a fast microSD card (Class 10 or better)
- Enable GPU memory split: `sudo raspi-config`
- Consider using a USB 3.0 SSD for better performance
- Monitor temperature: `vcgencmd measure_temp`

### Memory Management
- Firestore integration reduces local memory usage
- Automatic cleanup of old sessions
- Configurable conversation turn limits

## Security Considerations

- Store API keys in environment variables
- Use service account with minimal permissions
- Regularly update dependencies
- Monitor system resources

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test on Raspberry Pi 5
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues specific to Raspberry Pi 5:
1. Check the troubleshooting section
2. Review system logs
3. Test individual components
4. Create an issue with detailed information

## Changelog

### Raspberry Pi 5 Edition
- Optimized for Raspberry Pi 5 hardware
- USB audio device auto-detection
- Improved LED control via Pico
- Systemd service integration
- Automated setup script
- Enhanced error handling and logging

---

**Note**: This is a specialized version for Raspberry Pi 5. For other platforms, please use the main branch.