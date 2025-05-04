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
SYSTEMD_USER_DIR="$HOME/.config/systemd/user"
AUTOSTART_DIR="$HOME/.config/autostart"
LOGS_DIR="$SCRIPT_DIR/logs"

# =============================
# 1. Welcome
# =============================
echo -e "${YELLOW}========================================="
echo -e " Dream Recorder Pi Uninstaller "
echo -e "=========================================${NC}"

# =============================
# 2. Remove systemd user services
# =============================
log_step "Disabling and removing systemd user services"
SERVICES=(dream-recorder-docker.service dream-recorder-gpio.service)
for SERVICE in "${SERVICES[@]}"; do
    SERVICE_PATH="$SYSTEMD_USER_DIR/$SERVICE"
    if [ -f "$SERVICE_PATH" ]; then
        systemctl --user stop "$SERVICE" || true
        systemctl --user disable "$SERVICE" || true
        rm -f "$SERVICE_PATH"
        log_info "Removed $SERVICE_PATH and disabled service."
    else
        log_info "$SERVICE_PATH not found. Skipping."
    fi
    # Remove log files if present
    if [ -d "$LOGS_DIR" ]; then
        find "$LOGS_DIR" -type f -name '*.log' -exec rm -f {} +
        log_info "Removed all .log files in $LOGS_DIR."
    fi
    done

systemctl --user daemon-reload || true

# =============================
# 3. Remove autostart desktop entries
# =============================
log_step "Removing autostart desktop entries"
KIOSK_DESKTOP_FILE="$AUTOSTART_DIR/dream-recorder-kiosk.desktop"
BLANKING_AUTOSTART="$AUTOSTART_DIR/disable-screen-blanking.desktop"
for FILE in "$KIOSK_DESKTOP_FILE" "$BLANKING_AUTOSTART"; do
    if [ -f "$FILE" ]; then
        rm -f "$FILE"
        log_info "Removed $FILE."
    else
        log_info "$FILE not found. Skipping."
    fi
    done

# =============================
# 4. Remove disable-screen-blanking.sh
# =============================
log_step "Removing disable-screen-blanking.sh script"
SCREEN_SCRIPT="$HOME/disable-screen-blanking.sh"
if [ -f "$SCREEN_SCRIPT" ]; then
    rm -f "$SCREEN_SCRIPT"
    log_info "Removed $SCREEN_SCRIPT."
else
    log_info "$SCREEN_SCRIPT not found. Skipping."
fi

# =============================
# 5. Remove Docker containers, images, and volumes
# =============================
log_step "Docker cleanup (containers, images, volumes)"
log_warn "This will remove ALL Docker containers, images, and volumes on this system!"
echo -ne "${RED}Are you sure you want to proceed? (type 'yes' to continue): ${NC}"
read CONFIRM
if [ "$CONFIRM" == "yes" ]; then
    docker compose down --volumes || true
    docker rm -f $(docker ps -aq) 2>/dev/null || true
    docker rmi -f $(docker images -aq) 2>/dev/null || true
    docker volume rm $(docker volume ls -q) 2>/dev/null || true
    log_info "All Docker containers, images, and volumes removed."
else
    log_warn "Docker cleanup skipped."
fi

# =============================
# 6. Final message
# =============================
log_step "Uninstallation Complete!"
echo -e "${GREEN}Dream Recorder Pi system settings and services have been removed.${NC}"
echo -e "${YELLOW}You may want to manually remove any remaining config or data files in the project directory if desired.${NC}" 