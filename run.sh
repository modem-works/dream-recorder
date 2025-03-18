#!/bin/bash

# Exit on error
set -e

echo "🔮 Starting Dream Recorder..."

# Activate virtual environment first
if [ -d "venv" ]; then
    echo "🔌 Activating virtual environment..."
    source venv/bin/activate
else
    echo "❌ Error: Virtual environment not found. Please run './setup.sh' first."
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 --version | cut -d " " -f 2)
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -ge 12 ]; then
    echo "📌 Python 3.12+ detected. Using gevent for WebSocket support."
    
    # Check if gevent is already installed
    if ! python3 -c "import gevent" 2>/dev/null; then
        echo "📦 Installing gevent for WebSocket support..."
        pip install gevent==23.9.1 gevent-websocket==0.10.1
    else
        echo "✅ gevent already installed."
    fi
else
    echo "📌 Python version: $PYTHON_VERSION"
fi

# Check if .env file exists and has API keys set
if [ ! -f ".env" ]; then
    echo "❌ Error: .env file not found. Please run './setup.sh' first."
    exit 1
fi

# Check if API keys are set
if grep -q "your_openai_api_key" .env || grep -q "your_lumalabs_api_key" .env; then
    echo "⚠️ Warning: You need to set your API keys in the .env file."
    echo "    Please edit the .env file and replace the placeholder values with your actual API keys."
    read -p "Do you want to continue without setting API keys? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Export environment variables
export FLASK_APP=backend/app.py

# Run the application in production mode
echo "🚀 Launching Dream Recorder server..."
python backend/app.py

# The script won't reach here if the server is running, as it blocks the terminal
# If the server is stopped, you'll see this message
echo "💤 Dream Recorder server has stopped." 