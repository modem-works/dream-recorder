#!/bin/bash

# Check if running on a Raspberry Pi
if ! grep -q "Raspberry Pi" /proc/device-tree/model 2>/dev/null; then
    echo "ERROR: This script is intended to be run on a Raspberry Pi only." >&2
    exit 1
fi

SCRIPT_PATH="$(realpath "$0")"
SCRIPT_DIR="$(dirname "$SCRIPT_PATH")"
CONFIG_PATH="$SCRIPT_DIR/config.production.json"

# 1. Start Docker Compose (in detached mode)
echo "Starting Dream Recorder Docker container..."
docker compose up -d

log_step "Checking for config.production.json..."
if [ ! -f "$CONFIG_PATH" ]; then
    log_error "$CONFIG_PATH not found! Please ensure you are running this script from the project directory."
    exit 1
else
    log_info "Found $CONFIG_PATH."
fi

# Ensure logs directory exists before starting GPIO service
mkdir -p "$SCRIPT_DIR/logs"

# 2. Start GPIO service (native, in background)
echo "Starting GPIO service..."
nohup python3 "$SCRIPT_DIR/gpio_service.py" > "$SCRIPT_DIR/logs/gpio_service.log" 2>&1 &

# 3. Wait for the web app to be available
APP_URL=$(jq -r '.GPIO_FLASK_URL' "$CONFIG_PATH")
echo "Waiting for Dream Recorder web app to be available at $APP_URL..."
until curl -s $APP_URL > /dev/null; do
    sleep 2
done
echo "Dream Recorder web app is up!"
