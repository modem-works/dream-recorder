#!/bin/bash

set -e

# Check if running on a Raspberry Pi
if ! grep -q "Raspberry Pi" /proc/device-tree/model 2>/dev/null; then
    echo "ERROR: This script is intended to be run on a Raspberry Pi only." >&2
    exit 1
fi

SCRIPT_PATH="$(realpath "$0")"
SCRIPT_DIR="$(dirname "$SCRIPT_PATH")"

# Ensure Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Docker not found. Installing Docker for Raspberry Pi using Docker's official repository..."
    sudo apt-get update
    sudo apt-get install -y ca-certificates curl
    sudo install -m 0755 -d /etc/apt/keyrings
    sudo curl -fsSL https://download.docker.com/linux/debian/gpg -o /etc/apt/keyrings/docker.asc
    sudo chmod a+r /etc/apt/keyrings/docker.asc

    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/debian \
      $(. /etc/os-release && echo \"$VERSION_CODENAME\") stable" | \
      sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

    sudo apt-get update
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    sudo usermod -aG docker $USER
    echo "Docker installed. You may need to log out and back in for group changes to take effect."
fi

# Ensure jq is installed for JSON parsing
if ! command -v jq &> /dev/null; then
    echo "jq not found. Installing jq..."
    sudo apt-get update
    sudo apt-get install -y jq
fi

# Ensure Chromium is installed
if ! command -v chromium-browser &> /dev/null && ! command -v chromium &> /dev/null; then
    echo "Chromium not found. Installing Chromium browser..."
    sudo apt-get update
    sudo apt-get install -y chromium-browser || sudo apt-get install -y chromium
fi

# Parse the URL from config.production.json
CONFIG_PATH="$SCRIPT_DIR/config.production.json"
if [ ! -f "$CONFIG_PATH" ]; then
    echo "ERROR: $CONFIG_PATH not found!" >&2
    exit 1
fi

KIOSK_URL=$(jq -r '.GPIO_FLASK_URL' "$CONFIG_PATH")
if [ -z "$KIOSK_URL" ] || [ "$KIOSK_URL" == "null" ]; then
    echo "ERROR: Could not parse GPIO_FLASK_URL from $CONFIG_PATH" >&2
    exit 1
fi

# Get the current user and home directory
KIOSK_USER=$(whoami)
KIOSK_HOME="$HOME"

# Find Chromium binary
CHROMIUM_PATH=$(command -v chromium-browser || command -v chromium)
if [ -z "$CHROMIUM_PATH" ]; then
    echo "ERROR: Chromium browser not found after installation." >&2
    exit 1
fi

# Create a systemd service to launch Chromium in kiosk mode
SERVICE_FILE="/etc/systemd/system/kiosk-browser.service"
cat <<EOF | sudo tee $SERVICE_FILE > /dev/null
[Unit]
Description=Chromium Kiosk Browser
After=network.target

[Service]
User=$KIOSK_USER
Environment=XAUTHORITY=$KIOSK_HOME/.Xauthority
Environment=DISPLAY=:0
ExecStart=$CHROMIUM_PATH --noerrdialogs --disable-infobars --kiosk $KIOSK_URL
Restart=on-abort

[Install]
WantedBy=graphical.target
EOF

# Reload systemd, enable and start the service
sudo systemctl daemon-reload
sudo systemctl enable kiosk-browser.service

echo "Kiosk browser service installed for user $KIOSK_USER. It will launch Chromium in kiosk mode on boot."
