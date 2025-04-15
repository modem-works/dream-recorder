#!/bin/bash

# Script to start both Dream Recorder applications
# Usage: ./startup.sh [--setup]
#   --setup: Run setup before starting applications

# Get absolute path to the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Function to log messages
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Parse arguments
SETUP=false

for arg in "$@"; do
    case $arg in
        --setup)
            SETUP=true
            ;;
    esac
done

# Function to kill any existing processes
kill_existing_processes() {
    log "Stopping any existing Dream Recorder processes..."
    pkill -f 'python.*app.py|python.*gpio' || true
    # Give processes time to shut down gracefully
    sleep 2
    # Force kill any remaining processes
    pkill -9 -f 'python.*app.py|python.*gpio' 2>/dev/null || true
    log "All existing processes stopped"
}

# Function to check GPIO permissions
check_gpio_permissions() {
    if [ -e "/dev/gpiomem" ]; then
        log "Checking GPIO permissions..."
        if [ -r "/dev/gpiomem" ] && [ -w "/dev/gpiomem" ]; then
            log "User has proper GPIO read/write permissions"
        else
            log "WARNING: User does not have proper GPIO permissions!"
            log "You might need to add your user to the gpio or dialout group:"
            log "  sudo usermod -a -G gpio,dialout $USER"
            log "Then log out and log back in, or run: newgrp gpio"
        fi
    fi
}

# Function to run setup
run_setup() {
    log "Running setup script..."
    "$SCRIPT_DIR/setup.sh"
}

# Function to start Flask app
start_flask_app() {
    log "Starting Flask application..."
    if is_process_running "python.*app.py"; then
        log "Flask app is already running"
    else
        source "$SCRIPT_DIR/venv/bin/activate"
        # Check if we're in development mode
        if [ "$FLASK_ENV" = "development" ]; then
            log "Development mode detected - enabling auto-reloader"
            nohup python "$SCRIPT_DIR/app.py" --reload > "$SCRIPT_DIR/flask_app.log" 2>&1 &
        else
            nohup python "$SCRIPT_DIR/app.py" > "$SCRIPT_DIR/flask_app.log" 2>&1 &
        fi
        APP_PID=$!
        log "Flask app started with PID: $APP_PID"
    fi
}

# Function to start GPIO service
start_gpio_service() {
    log "Starting GPIO service..."
    if is_process_running "python.*gpio_service.py"; then
        log "GPIO service is already running"
    else
        # Give Flask app time to start up
        log "Waiting for Flask app to initialize..."
        sleep 5
        
        # Run the GPIO service
        "$SCRIPT_DIR/run_gpio.sh"
        log "GPIO service started"
    fi
}

# Function to check if a process is running
is_process_running() {
    pgrep -f "$1" > /dev/null
    return $?
}

# Change to the script directory
cd "$SCRIPT_DIR"

# Always kill existing processes first
kill_existing_processes

# Check GPIO permissions on Raspberry Pi
check_gpio_permissions

# Check for setup flag
if [ "$SETUP" = true ] || [ ! -d "venv" ]; then
    run_setup
fi

# Start both applications
start_flask_app
start_gpio_service

log "Both applications started successfully!"
log "Flask app log: tail -f $SCRIPT_DIR/flask_app.log"
log "GPIO service log: tail -f $SCRIPT_DIR/gpio_service.log"
log "To stop them, use: pkill -f 'python.*app.py|python.*gpio'" 