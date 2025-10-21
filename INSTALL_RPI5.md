# Quick Installation Guide - Raspberry Pi 5

## Prerequisites
- Raspberry Pi 5 with Raspberry Pi OS (64-bit)
- USB microphone and speaker connected
- Internet connection
- Google API key and Firestore credentials

## Installation Steps

### 1. Clone and Setup
```bash
git clone <your-repo-url>
cd eidoid-pet-robot
git checkout rpi5-adaptation
chmod +x setup_rpi5.sh
./setup_rpi5.sh
```

### 2. Configure API Keys
```bash
cp .env.template .env
nano .env
```

Add your credentials:
```env
GOOGLE_API_KEY=your_actual_api_key_here
GOOGLE_APPLICATION_CREDENTIALS=/home/pi/eidoid-pet-robot/your-service-account-key.json
FIRESTORE_PROJECT_ID=your-project-id
```

### 3. Test Setup
```bash
source .venv/bin/activate
python test_rpi5_setup.py
```

### 4. Run Robot
```bash
python main.py
```

## Quick Commands

- **"Hey Jarvis"** - Activate Jarvis
- **"Alexa"** - Activate Alexa  
- **"What's the weather"** - Weather + character creation
- **"Thank you for your time"** - End conversation

## Auto-start on Boot
```bash
sudo systemctl enable eidoid-robot.service
sudo systemctl start eidoid-robot.service
```

## Troubleshooting
- Run `python list_audio_devices.py` to check audio
- Check logs: `sudo journalctl -u eidoid-robot.service -f`
- Restart service: `sudo systemctl restart eidoid-robot.service`