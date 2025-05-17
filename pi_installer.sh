#!/bin/bash

set -e

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[1;34m'
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
    echo -e "\n${BLUE}==============================="
    echo -e ">>> $1"
    echo -e "===============================${NC}\n"
}

SCRIPT_PATH="$(realpath "$0")"
SCRIPT_DIR="$(dirname "$SCRIPT_PATH")"
CONFIG_PATH="$SCRIPT_DIR/config.json"

# =============================
# 1. Welcome
# =============================
echo -e "${YELLOW}========================================="
echo -e " Dream Recorder Pi Installer "
echo -e "=========================================${NC}"

# =============================
# 2. Pre-checks & Initialization
# =============================
log_step "Pre-checks and Initialization"

# .env.example check
if [ ! -f "$SCRIPT_DIR/.env.example" ]; then
    log_error ".env.example not found! Please add it to the project root."
    exit 1
fi
# config.example.json check
if [ ! -f "$SCRIPT_DIR/config.example.json" ]; then
    log_error "config.example.json not found! Please add it to the project root."
    exit 1
fi
# Copy .env if missing
if [ ! -f "$SCRIPT_DIR/.env" ]; then
    # Prompt for API keys
    echo -ne "Enter your OPENAI_API_KEY (from OpenAI dashboard): "
    read -r OPENAI_API_KEY
    if [[ ! "$OPENAI_API_KEY" =~ ^[A-Za-z0-9_-]{20,}$ ]]; then
        log_error "OPENAI_API_KEY must be at least 20 alphanumeric characters. Exiting."
        exit 1
    fi
    echo -ne "Enter your LUMALABS_API_KEY (from Luma Labs dashboard): "
    read -r LUMALABS_API_KEY
    if [[ ! "$LUMALABS_API_KEY" =~ ^[A-Za-z0-9_-]{20,}$ ]]; then
        log_error "LUMALABS_API_KEY must be at least 20 alphanumeric characters. Exiting."
        exit 1
    fi
    # Create .env from template, replacing placeholders
    sed -e "s|OPENAI_API_KEY=your-openai-api-key-here|OPENAI_API_KEY=$OPENAI_API_KEY|" \
        -e "s|LUMALABS_API_KEY=your-luma-labs-api-key-here|LUMALABS_API_KEY=$LUMALABS_API_KEY|" \
        "$SCRIPT_DIR/.env.example" > "$SCRIPT_DIR/.env"
    log_info "Created .env with provided API keys."
else
    log_info ".env already exists. Skipping."
fi
# Copy config.json if missing
if [ ! -f "$CONFIG_PATH" ]; then
    cp "$SCRIPT_DIR/config.example.json" "$CONFIG_PATH"
    log_info "Copied config.example.json to config.json."
else
    log_info "config.json already exists. Skipping."
fi

# =============================
# 3. Update System
# =============================
sudo apt update

# =============================
# 4. Docker Installation
# =============================
log_step "Checking for Docker"
if command -v docker &> /dev/null; then
    log_info "Docker is already installed."
else
    log_warn "Docker not found. Installing Docker..."
    sudo apt install -y ca-certificates curl
    sudo install -m 0755 -d /etc/apt/keyrings
    sudo curl -fsSL https://download.docker.com/linux/debian/gpg -o /etc/apt/keyrings/docker.asc
    sudo chmod a+r /etc/apt/keyrings/docker.asc
    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/debian \
      $(. /etc/os-release && echo \"$VERSION_CODENAME\") stable" | \
      sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    sudo apt update
    sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    sudo usermod -aG docker $USER
    log_info "Docker installed. You may need to log out and back in for group changes to take effect."
fi

# =============================
# 5. jq Installation
# =============================
log_step "Checking for jq (JSON parser)"
if command -v jq &> /dev/null; then
    log_info "jq is already installed."
else
    log_warn "jq not found. Installing jq..."
    sudo apt update
    sudo apt install -y jq
    log_info "jq installed."
fi

# =============================
# 6. Parse config.json for URLs
# =============================
log_step "Parsing GPIO_FLASK_URL from config.json"
KIOSK_URL=$(jq -r '.GPIO_FLASK_URL' "$CONFIG_PATH")
if [ -z "$KIOSK_URL" ] || [ "$KIOSK_URL" == "null" ]; then
    log_error "Could not parse GPIO_FLASK_URL from $CONFIG_PATH. Exiting."
    exit 1
else
    log_info "Parsed KIOSK URL: $KIOSK_URL"
fi

# =============================
# 7. Systemd Service Setup
# =============================
log_step "Setting up Docker Compose auto-start as a user systemd service"
SYSTEMD_USER_DIR="$HOME/.config/systemd/user"
mkdir -p "$SYSTEMD_USER_DIR"
SERVICE_FILE="$SYSTEMD_USER_DIR/dream_recorder_docker.service"

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

log_step "Reloading user systemd daemon and enabling Docker Compose service"
systemctl --user daemon-reload
systemctl --user enable dream_recorder_docker.service && \
    log_info "Enabled dream_recorder_docker.service for user $USER." || \
    log_warn "Could not enable dream_recorder_docker.service. You may need to log in with a desktop session first."

log_step "Starting Docker Compose service now"
systemctl --user start dream_recorder_docker.service && \
    log_info "Docker Compose service started." || \
    log_warn "Could not start Docker Compose service. You may need to log in with a desktop session first."

# =============================
# 8. Build Docker container
# =============================
log_step "Building Docker images (docker compose build)"
docker compose build

# =============================
# 9. API Key Validation (inside container)
# =============================
log_step "Testing API keys inside the container"
if docker compose exec dream_recorder python scripts/test_openai_key.py; then
    log_info "OpenAI API key is valid."
else
    log_warn "OpenAI API key is invalid. Please check your .env file."
fi
if docker compose exec dream_recorder python scripts/test_luma_key.py; then
    log_info "Luma Labs API key is valid."
else
    log_warn "Luma Labs API key is invalid. Please check your .env file."
fi

log_step "Enabling lingering for user services to start at boot"
if sudo loginctl enable-linger $USER; then
    log_info "Lingering enabled for $USER. User services will start at boot."
else
    log_warn "Could not enable lingering. You may need to run: sudo loginctl enable-linger $USER"
fi

log_step "Setting up GPIO service as a user systemd service"
GPIO_SERVICE_FILE="$SYSTEMD_USER_DIR/dream_recorder_gpio.service"
LOGS_DIR="$SCRIPT_DIR/logs"
mkdir -p "$LOGS_DIR"

cat > "$GPIO_SERVICE_FILE" <<EOL
[Unit]
Description=Dream Recorder GPIO Service
After=network.target dream_recorder_docker.service

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

log_step "Reloading user systemd daemon and enabling GPIO service"
systemctl --user daemon-reload
systemctl --user enable dream_recorder_gpio.service && \
    log_info "Enabled dream_recorder_gpio.service for user $USER." || \
    log_warn "Could not enable dream_recorder_gpio.service. You may need to log in with a desktop session first."

log_step "Starting GPIO service now"
systemctl --user start dream_recorder_gpio.service && \
    log_info "GPIO service started." || \
    log_warn "Could not start GPIO service. You may need to log in with a desktop session first."

# =============================
# 10. Chromium Kiosk Autostart Setup
# =============================
log_step "Setting up Chromium kiosk mode autostart"
AUTOSTART_DIR="$HOME/.config/autostart"
mkdir -p "$AUTOSTART_DIR"
KIOSK_DESKTOP_FILE="$AUTOSTART_DIR/dream_recorder_kiosk.desktop"

# Path to the loading screen HTML (absolute path)
LOADING_SCREEN_SRC="$SCRIPT_DIR/templates/loading.html"
LOADING_SCREEN_DST="$SCRIPT_DIR/templates/loading.kiosk.html"

# Detect Chromium or Chrome
if command -v chromium-browser &> /dev/null; then
    BROWSER_CMD="chromium-browser"
elif command -v chromium &> /dev/null; then
    BROWSER_CMD="chromium"
elif command -v google-chrome &> /dev/null; then
    BROWSER_CMD="google-chrome"
else
    log_warn "Chromium or Chrome not found. Please install Chromium for kiosk mode."
    BROWSER_CMD="chromium-browser"
fi

# Inject the real app URL into the loading screen HTML
if [ -f "$LOADING_SCREEN_SRC" ]; then
    sed "s#const target = window.KIOSK_APP_URL || \"http://localhost:5000\";#const target = '$KIOSK_URL';#" "$LOADING_SCREEN_SRC" > "$LOADING_SCREEN_DST"
    log_info "Injected KIOSK_URL into loading screen HTML."
else
    log_error "Loading screen HTML not found at $LOADING_SCREEN_SRC."
    exit 1
fi

cat > "$KIOSK_DESKTOP_FILE" <<EOL
[Desktop Entry]
Type=Application
Name=Dream Recorder Kiosk
Exec=$BROWSER_CMD --kiosk --no-first-run --disable-session-crashed-bubble --disable-infobars --use-fake-ui-for-media-stream --app=file://$LOADING_SCREEN_DST
X-GNOME-Autostart-enabled=true
EOL

if [ -f "$KIOSK_DESKTOP_FILE" ]; then
    log_info "Created autostart desktop entry at $KIOSK_DESKTOP_FILE."
else
    log_error "Failed to create autostart desktop entry at $KIOSK_DESKTOP_FILE."
fi

# =============================
# 11. Screen Blanking Disable Script
# =============================
log_step "Creating script to disable screen blanking"
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

# =============================
# 12. Final Summary
# =============================
log_step "Setting desktop wallpaper to @0.jpg"
python3 "$SCRIPT_DIR/scripts/set_pi_background.py"

log_step "Setup Complete!"
echo -e "${GREEN}Docker Compose and Chromium kiosk mode will auto-start on boot.${NC}"
echo -e "${YELLOW}You may need to reboot for all changes to take effect.${NC}"
echo -e "${BLUE}If you see any warnings about systemd user services, log in with a desktop session and re-run this script or run the suggested commands.${NC}" 