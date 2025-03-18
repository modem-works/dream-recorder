#!/bin/bash

# This script fixes Python 3.12 compatibility issues with the Dream Recorder application

echo "🔧 Applying Python 3.12 compatibility fixes..."

# Check if the virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Error: Virtual environment not found. Please run './setup.sh' first."
    exit 1
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Check Python version
PYTHON_VERSION=$(python3 --version | cut -d " " -f 2)
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -ge 12 ]; then
    echo "📌 Python 3.12+ detected (version: $PYTHON_VERSION). Applying fixes."
else
    echo "📌 Python version: $PYTHON_VERSION is below 3.12, but we'll apply the fixes anyway for future compatibility."
fi

# Install gevent and gevent-websocket
echo "📦 Installing gevent and gevent-websocket..."
if pip install gevent==23.9.1 gevent-websocket==0.10.1; then
    echo "✅ Successfully installed gevent packages."
else
    echo "❌ Error installing gevent packages. Please check your Python environment."
    exit 1
fi

# Update permissions
echo "🔑 Making scripts executable..."
chmod +x run.sh dev.sh setup.sh
if [ -f "scripts/install_pyaudio.sh" ]; then
    chmod +x scripts/install_pyaudio.sh
fi
chmod +x scripts/fix_python312.sh

echo "✅ Python 3.12 compatibility fixes applied!"
echo "🚀 You can now run the application with ./run.sh" 