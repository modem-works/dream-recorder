#!/bin/bash

# Exit on error
set -e

echo "🎤 Installing PyAudio and dependencies..."

# Install system dependencies for PyAudio
if [[ "$(uname)" == "Linux" ]]; then
    # Linux (Ubuntu/Debian/Raspberry Pi)
    echo "📦 Installing system dependencies for PyAudio on Linux..."
    sudo apt-get update
    sudo apt-get install -y portaudio19-dev python3-pyaudio
elif [[ "$(uname)" == "Darwin" ]]; then
    # macOS
    echo "📦 Installing system dependencies for PyAudio on macOS..."
    brew install portaudio
else
    echo "⚠️ Unsupported operating system. Please install PortAudio manually."
    exit 1
fi

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Install PyAudio
echo "📦 Installing PyAudio Python package..."
pip install PyAudio==0.2.13

echo "✅ PyAudio installation complete!"
echo "🔊 You can now record and process audio with Dream Recorder." 