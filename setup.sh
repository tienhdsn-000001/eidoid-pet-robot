#!/bin/bash

# Setup script for Eidoid Pet Robot on Raspberry Pi 5

echo "Setting up Eidoid Pet Robot..."

# Update system
echo "Updating system packages..."
sudo apt-get update

# Install system dependencies
echo "Installing system dependencies..."
sudo apt-get install -y python3-pyaudio portaudio19-dev espeak ffmpeg libespeak1

# Create virtual environment
echo "Creating Python virtual environment..."
python3 -m venv .venv
source .venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Create necessary directories
echo "Creating directories..."
mkdir -p persona_memories

# Create .env file template
if [ ! -f .env ]; then
    echo "Creating .env template..."
    cat > .env << EOL
# Gemini API Configuration
GEMINI_API_KEY=your-gemini-api-key-here

# Optional: Custom settings
SLEEP_TIMEOUT=30
EVOLUTION_INTERVAL=7
EOL
fi

echo "Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env file and add your Gemini API key"
echo "2. Run: source .venv/bin/activate"
echo "3. Run: python social_head.py"
echo ""
echo "For voice activation:"
echo "- Say 'Alexa' to activate Alexa persona"
echo "- Say 'Hey Jarvis' to activate Jarvis persona"
echo "- Say 'What's the weather' for weather mode"