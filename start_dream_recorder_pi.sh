#!/bin/bash
# start_dream_recorder_pi.sh
# Starts the Dream Recorder Docker app, GPIO service, and Chromium in kiosk mode on Raspberry Pi.

set -e

# Check if running on a Raspberry Pi
if ! grep -q "Raspberry Pi" /proc/device-tree/model 2>/dev/null; then
    echo "ERROR: This script is intended to be run on a Raspberry Pi only." >&2
    exit 1
fi

SERVICE_NAME="dream-recorder-launcher"
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

# 1. Start Docker Compose (in detached mode)
echo "Starting Dream Recorder Docker container..."
docker compose up -d

# Ensure logs directory exists before starting GPIO service
mkdir -p "$SCRIPT_DIR/logs"

# 2. Start GPIO service (native, in background)
echo "Starting GPIO service..."
nohup python3 "$SCRIPT_DIR/gpio_service.py" > "$SCRIPT_DIR/logs/gpio_service.log" 2>&1 &

# 3. Wait for the web app to be available
APP_URL="http://localhost:5000"
echo "Waiting for Dream Recorder web app to be available at $APP_URL..."
until curl -s $APP_URL > /dev/null; do
    sleep 2
done
echo "Dream Recorder web app is up!"

# 4. Chromium is now started by a user-level systemd service (see kiosk.sh and kiosk.service)

# 5. Optionally, set up systemd service for auto-start on boot
if [ "$1" == "--install-systemd" ]; then
    echo "Setting up systemd service for auto-start on boot..."
    SERVICE_FILE="/etc/systemd/system/$SERVICE_NAME.service"
    sudo bash -c "cat > $SERVICE_FILE" <<EOL
[Unit]
Description=Dream Recorder Launcher
After=network.target docker.service
Requires=docker.service

[Service]
Type=simple
User=$USER
WorkingDirectory=$SCRIPT_DIR
ExecStart=$SCRIPT_PATH
Restart=on-failure
RestartSec=10s

[Install]
WantedBy=multi-user.target
EOL
    sudo systemctl daemon-reload
    sudo systemctl enable $SERVICE_NAME
    echo "Systemd service installed. It will start on boot. To start now: sudo systemctl start $SERVICE_NAME"
fi

echo "All services started. To stop, run ./stop_dream_recorder_pi.sh"

# Instructions for user to add Chromium to autostart
# To launch Chromium automatically on boot, add the following line to ~/.config/lxsession/LXDE-pi/autostart:
# @chromium-browser --kiosk --no-first-run --disable-session-crashed-bubble --disable-infobars --app=http://localhost:5000 