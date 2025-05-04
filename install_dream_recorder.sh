#!/bin/bash

set -e

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}
log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}
log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}
log_step() {
    echo -e "${YELLOW}==> $1${NC}"
}

SCRIPT_PATH="$(realpath "$0")"
SCRIPT_DIR="$(dirname "$SCRIPT_PATH")"
CONFIG_PATH="$SCRIPT_DIR/config.production.json"

log_step "Checking for Docker..."
if command -v docker &> /dev/null; then
    log_info "Docker is already installed."
else
    log_warn "Docker not found. Installing Docker..."
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
    log_info "Docker installed. You may need to log out and back in for group changes to take effect."
fi

log_step "Checking for jq (JSON parser)..."
if command -v jq &> /dev/null; then
    log_info "jq is already installed."
else
    log_warn "jq not found. Installing jq..."
    sudo apt-get update
    sudo apt-get install -y jq
    log_info "jq installed."
fi

log_step "Checking for Chromium browser..."
if command -v chromium-browser &> /dev/null; then
    BROWSER_CMD="chromium-browser"
    log_info "chromium-browser is already installed."
elif command -v chromium &> /dev/null; then
    BROWSER_CMD="chromium"
    log_info "chromium is already installed."
else
    log_warn "Chromium browser not found. Installing chromium-browser..."
    sudo apt-get update
    if sudo apt-get install -y chromium-browser; then
        BROWSER_CMD="chromium-browser"
        log_info "chromium-browser installed."
    elif sudo apt-get install -y chromium; then
        BROWSER_CMD="chromium"
        log_info "chromium installed."
    else
        log_error "Failed to install Chromium browser. Exiting."
        exit 1
    fi
fi

log_step "Checking for config.production.json..."
if [ ! -f "$CONFIG_PATH" ]; then
    log_error "$CONFIG_PATH not found! Please ensure you are running this script from the project directory."
    exit 1
else
    log_info "Found $CONFIG_PATH."
fi

log_step "Parsing GPIO_FLASK_URL from config.production.json..."
KIOSK_URL=$(jq -r '.GPIO_FLASK_URL' "$CONFIG_PATH")
if [ -z "$KIOSK_URL" ] || [ "$KIOSK_URL" == "null" ]; then
    log_error "Could not parse GPIO_FLASK_URL from $CONFIG_PATH. Exiting."
    exit 1
else
    log_info "Parsed KIOSK URL: $KIOSK_URL"
fi

log_step "Setting up Docker Compose auto-start as a user systemd service..."
SYSTEMD_USER_DIR="$HOME/.config/systemd/user"
mkdir -p "$SYSTEMD_USER_DIR"
SERVICE_FILE="$SYSTEMD_USER_DIR/dream-recorder-docker.service"

cat > "$SERVICE_FILE" <<EOL
[Unit]
Description=Dream Recorder Docker Compose
After=network.target

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=$SCRIPT_DIR
ExecStart=/usr/bin/docker compose up -d
ExecStop=/usr/bin/docker compose down

[Install]
WantedBy=default.target
EOL

log_info "Created user systemd service at $SERVICE_FILE."

log_step "Reloading user systemd daemon and enabling service..."
systemctl --user daemon-reload
systemctl --user enable dream-recorder-docker.service && \
    log_info "Enabled dream-recorder-docker.service for user $USER." || \
    log_warn "Could not enable dream-recorder-docker.service. You may need to log in with a desktop session first."

log_step "Enabling lingering for user services to start at boot..."
if sudo loginctl enable-linger $USER; then
    log_info "Lingering enabled for $USER. User services will start at boot."
else
    log_warn "Could not enable lingering. You may need to run: sudo loginctl enable-linger $USER"
fi

log_step "Setting up GPIO service as a user systemd service..."
GPIO_SERVICE_FILE="$SYSTEMD_USER_DIR/dream-recorder-gpio.service"
LOGS_DIR="$SCRIPT_DIR/logs"
mkdir -p "$LOGS_DIR"

cat > "$GPIO_SERVICE_FILE" <<EOL
[Unit]
Description=Dream Recorder GPIO Service
After=network.target dream-recorder-docker.service

[Service]
Type=simple
WorkingDirectory=$SCRIPT_DIR
ExecStart=/usr/bin/python3 $SCRIPT_DIR/gpio_service.py
StandardOutput=append:$LOGS_DIR/gpio_service.log
StandardError=append:$LOGS_DIR/gpio_service.log
Restart=on-failure

[Install]
WantedBy=default.target
EOL

log_info "Created user systemd service at $GPIO_SERVICE_FILE."

log_step "Reloading user systemd daemon and enabling GPIO service..."
systemctl --user daemon-reload
systemctl --user enable dream-recorder-gpio.service && \
    log_info "Enabled dream-recorder-gpio.service for user $USER." || \
    log_warn "Could not enable dream-recorder-gpio.service. You may need to log in with a desktop session first."

log_step "Starting GPIO service now..."
systemctl --user start dream-recorder-gpio.service && \
    log_info "GPIO service started." || \
    log_warn "Could not start GPIO service. You may need to log in with a desktop session first."

log_step "Setting up Chromium kiosk mode autostart..."
AUTOSTART_DIR="$HOME/.config/autostart"
mkdir -p "$AUTOSTART_DIR"
KIOSK_DESKTOP_FILE="$AUTOSTART_DIR/dream-recorder-kiosk.desktop"

# Path to the loading screen HTML (absolute path)
LOADING_SCREEN_SRC="$SCRIPT_DIR/loading_screen/index.html"
LOADING_SCREEN_DST="$SCRIPT_DIR/loading_screen/index.kiosk.html"

# Inject the real app URL into the loading screen HTML
if [ -f "$LOADING_SCREEN_SRC" ]; then
    sed "s|window.KIOSK_APP_URL || window.KIOSK_APP_URL = '"$KIOSK_URL"';|" "$LOADING_SCREEN_SRC" > "$LOADING_SCREEN_DST"
    log_info "Injected KIOSK_URL into loading screen HTML."
else
    log_error "Loading screen HTML not found at $LOADING_SCREEN_SRC."
    exit 1
fi

cat > "$KIOSK_DESKTOP_FILE" <<EOL
[Desktop Entry]
Type=Application
Name=Dream Recorder Kiosk
Exec=$BROWSER_CMD --kiosk --no-first-run --disable-session-crashed-bubble --disable-infobars --app=file://$LOADING_SCREEN_DST
X-GNOME-Autostart-enabled=true
EOL

if [ -f "$KIOSK_DESKTOP_FILE" ]; then
    log_info "Created autostart desktop entry at $KIOSK_DESKTOP_FILE."
else
    log_error "Failed to create autostart desktop entry at $KIOSK_DESKTOP_FILE."
fi

log_step "Creating script to disable screen blanking..."
SCREEN_SCRIPT="$HOME/disable-screen-blanking.sh"
cat > "$SCREEN_SCRIPT" <<EOL
#!/bin/bash
xset s off
xset s noblank
xset -dpms
EOL
chmod +x "$SCREEN_SCRIPT"

BLANKING_AUTOSTART="$AUTOSTART_DIR/disable-screen-blanking.desktop"
cat > "$BLANKING_AUTOSTART" <<EOL
[Desktop Entry]
Type=Application
Name=Disable Screen Blanking
Exec=$SCREEN_SCRIPT
X-GNOME-Autostart-enabled=true
EOL

if [ -f "$BLANKING_AUTOSTART" ]; then
    log_info "Created autostart entry to disable screen blanking at $BLANKING_AUTOSTART."
else
    log_error "Failed to create autostart entry for screen blanking."
fi

log_info "Setup complete!"
echo -e "${GREEN}Docker Compose and Chromium kiosk mode will auto-start on boot.${NC}"
echo -e "${YELLOW}You may need to reboot for all changes to take effect.${NC}" 