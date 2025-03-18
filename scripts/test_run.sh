#!/bin/bash

# This script runs the Dream Recorder application in test mode without requiring Raspberry Pi hardware

# Exit on error
set -e

echo "🧪 Starting Dream Recorder in TEST MODE..."

# Activate virtual environment first
if [ -d "venv" ]; then
    echo "🔌 Activating virtual environment..."
    source venv/bin/activate
else
    echo "❌ Error: Virtual environment not found. Please run './setup.sh' first."
    exit 1
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ Error: .env file not found. Please run './setup.sh' first."
    exit 1
fi

# Force enable test mode and disable GPIO
echo "🔧 Enabling test mode and disabling GPIO..."
export TEST_MODE=true
export ENABLE_GPIO=false

# Export environment variables
export FLASK_APP=backend/app.py
export FLASK_DEBUG=true

# Run the application
echo "🚀 Launching Dream Recorder server in test mode..."
echo "📝 Note: Hardware features are disabled, and sample data will be used for testing."
python backend/app.py

# The script won't reach here if the server is running
echo "💤 Dream Recorder test server has stopped." 