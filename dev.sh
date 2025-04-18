#!/bin/bash

# Development script for Dream Recorder
# This script sets up and runs the application in development mode

# Get absolute path to the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Function to log messages
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Kill any existing processes
log "Stopping any existing Dream Recorder processes..."
pkill -f 'python.*app.py' || true
sleep 2
pkill -9 -f 'python.*app.py' 2>/dev/null || true
log "All existing processes stopped"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    log "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install requirements if needed
if [ ! -f "venv/.requirements_installed" ]; then
    log "Installing requirements..."
    pip install -r requirements.txt
    touch venv/.requirements_installed
fi

# Create necessary directories
log "Creating necessary directories..."
mkdir -p media media/audio media/video media/thumbs

# Check for .env file
if [ ! -f ".env" ]; then
    log "Creating .env file from .env.example..."
    if [ -f ".env.example" ]; then
        cp .env.example .env
        log "Created .env file. Please update it with your API keys"
    else
        log "Error: .env.example file not found"
        exit 1
    fi
fi

# Start the Flask app in development mode
log "Starting Flask application in development mode..."
FLASK_ENV=development python app.py --reload 