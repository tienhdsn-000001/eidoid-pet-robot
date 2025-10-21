#!/bin/bash
# setup_rpi5.sh
# Automated setup script for Eidoid Pet Robot on Raspberry Pi 5
# Run this script after cloning the repository

set -e  # Exit on any error

echo "=== Eidoid Pet Robot - Raspberry Pi 5 Setup ==="
echo "This script will set up your Raspberry Pi 5 for the Eidoid Pet Robot"
echo ""

# Check if running on Raspberry Pi
if ! grep -q "Raspberry Pi" /proc/cpuinfo; then
    echo "Warning: This script is designed for Raspberry Pi 5"
    echo "Continue anyway? (y/N)"
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Update system packages
echo "Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install system dependencies
echo "Installing system dependencies..."
sudo apt install -y \
    python3-dev \
    python3-pip \
    python3-venv \
    python3-pyaudio \
    libasound2-dev \
    portaudio19-dev \
    git \
    curl \
    wget \
    build-essential \
    cmake \
    pkg-config \
    libjpeg-dev \
    libtiff5-dev \
    libjasper-dev \
    libpng-dev \
    libavcodec-dev \
    libavformat-dev \
    libswscale-dev \
    libv4l-dev \
    libxvidcore-dev \
    libx264-dev \
    libgtk-3-dev \
    libatlas-base-dev \
    gfortran \
    libhdf5-dev \
    libhdf5-serial-dev \
    libhdf5-103 \
    libqtgui4 \
    libqtwebkit4 \
    libqt4-test \
    python3-pyqt5 \
    libatlas-base-dev \
    libjasper-dev

# Enable audio
echo "Enabling audio..."
sudo raspi-config nonint do_audio 0

# Enable I2C and SPI (for future hardware expansion)
echo "Enabling I2C and SPI..."
sudo raspi-config nonint do_i2c 0
sudo raspi-config nonint do_spi 0

# Create virtual environment
echo "Creating Python virtual environment..."
python3 -m venv .venv
source .venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Install additional Raspberry Pi specific packages
echo "Installing Raspberry Pi specific packages..."
pip install RPi.GPIO gpiozero adafruit-circuitpython-neopixel

# Create necessary directories
echo "Creating necessary directories..."
mkdir -p logs
mkdir -p data
mkdir -p config

# Set up audio permissions
echo "Setting up audio permissions..."
sudo usermod -a -G audio $USER
sudo usermod -a -G dialout $USER

# Create systemd service file
echo "Creating systemd service..."
sudo tee /etc/systemd/system/eidoid-robot.service > /dev/null <<EOF
[Unit]
Description=Eidoid Pet Robot
After=network.target sound.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$(pwd)
Environment=PATH=$(pwd)/.venv/bin
ExecStart=$(pwd)/.venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd
sudo systemctl daemon-reload

# Create environment file template
echo "Creating environment file template..."
cat > .env.template <<EOF
# Google API Configuration
GOOGLE_API_KEY=your_google_api_key_here
GOOGLE_APPLICATION_CREDENTIALS=/path/to/your/service-account-key.json

# Firestore Configuration
FIRESTORE_PROJECT_ID=eidoid-1

# Audio Configuration (optional - will auto-detect if not set)
MIC_DEVICE_INDEX=
SPEAKER_DEVICE_INDEX=

# Hardware Configuration
ENABLE_GPIO=true
ENABLE_USB_AUDIO=true
EOF

echo ""
echo "=== Setup Complete! ==="
echo ""
echo "Next steps:"
echo "1. Copy .env.template to .env and fill in your API keys"
echo "2. Place your Google service account JSON file in the project directory"
echo "3. Update .env with the path to your service account JSON file"
echo "4. Connect your USB microphone and speaker"
echo "5. Run 'python list_audio_devices.py' to detect your audio devices"
echo "6. Update the device indices in wake_word.py and session_manager.py if needed"
echo "7. Test the setup with 'python main.py'"
echo ""
echo "To enable auto-start on boot:"
echo "  sudo systemctl enable eidoid-robot.service"
echo "  sudo systemctl start eidoid-robot.service"
echo ""
echo "To check service status:"
echo "  sudo systemctl status eidoid-robot.service"
echo ""
echo "To view logs:"
echo "  sudo journalctl -u eidoid-robot.service -f"
echo ""
echo "Please reboot your Raspberry Pi 5 after completing the setup."