#!/bin/bash

# Simple GPIO Service for Dream Recorder
# This script runs the GPIO controller service that detects different touch patterns

# Get absolute path to script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Change to the script directory
cd "$SCRIPT_DIR"

# Log start
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting GPIO service..."

# Kill any existing GPIO processes
pkill -f 'python.*gpio' || true
sleep 1

# Run the GPIO service and log output
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Running GPIO service..."

# Ensure log directory exists
mkdir -p "$SCRIPT_DIR/log"

# Run with system Python to ensure GPIO access works correctly
PATH=/usr/local/bin:/usr/bin:/bin
cd "$SCRIPT_DIR"
python3 "$SCRIPT_DIR/gpio_service.py" >> "$SCRIPT_DIR/logs/gpio_service.log" 2>&1 &

# Log the PID
PID=$!
echo "[$(date '+%Y-%m-%d %H:%M:%S')] GPIO service started with PID: $PID" 