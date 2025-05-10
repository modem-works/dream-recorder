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

echo -ne "${RED}Are you sure you want to uninstall Dream Recorder and remove all related services and data? (type 'yes' to continue): ${NC}"
read REALLY_SURE
if [ "$REALLY_SURE" != "yes" ]; then
    log_warn "Uninstall cancelled. No changes made."
    exit 0
fi

# =============================
# 2. Remove systemd user services
# =============================
log_step "Disabling and removing systemd user services"
SERVICES=(dream_recorder_docker.service dream_recorder_gpio.service)
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
KIOSK_DESKTOP_FILE="$AUTOSTART_DIR/dream_recorder_kiosk.desktop"
BLANKING_AUTOSTART="$AUTOSTART_DIR/disable_screen_blanking.desktop"
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
# 5. Remove Docker containers, images, and volumes (project only)
# =============================
log_step "Docker cleanup (project containers, images, volumes only)"
log_warn "This will remove ONLY Docker containers, images, and volumes related to this project!"

echo -ne "${RED}Are you sure you want to proceed? (type 'yes' to continue): ${NC}"
read CONFIRM
if [ "$CONFIRM" == "yes" ]; then
    # Stop and remove containers, networks, and volumes defined in this compose file
    docker compose down --volumes || true

    # Remove images built by this compose file
    IMAGE_IDS=$(docker compose images -q | grep -v "<none>" | sort | uniq)
    if [ -n "$IMAGE_IDS" ]; then
        docker rmi -f $IMAGE_IDS || true
        log_info "Removed Docker images built by this project."
    else
        log_info "No project images to remove."
    fi

    log_info "All Docker containers, images, and volumes for this project removed."
else
    log_warn "Docker cleanup skipped."
fi

# =============================
# 5b. Force remove any remaining containers and named volumes
# =============================
log_step "Force removing any remaining project containers and named volumes"
# Remove any remaining containers related to the project
PROJECT_CONTAINERS=$(docker ps -a --filter "name=dream_recorder" -q)
if [ -n "$PROJECT_CONTAINERS" ]; then
    docker rm -f $PROJECT_CONTAINERS || true
    log_info "Force removed remaining project containers."
else
    log_info "No remaining project containers to remove."
fi

# Remove named volumes if they still exist
VOLUMES=("dream_recorder_logs-data" "dream_recorder_db-data" "dream_recorder_media-data")
for VOLUME in "${VOLUMES[@]}"; do
    if docker volume inspect "$VOLUME" >/dev/null 2>&1; then
        docker volume rm -f "$VOLUME" || true
        log_info "Force removed volume $VOLUME."
    else
        log_info "Volume $VOLUME not found or already removed."
    fi
done

# Optionally prune all unused Docker resources
echo -ne "${RED}Do you want to prune all unused Docker resources? (type 'yes' to continue): ${NC}"
read PRUNE_CONFIRM
if [ "$PRUNE_CONFIRM" == "yes" ]; then
    docker system prune -a --volumes -f
    log_info "Pruned all unused Docker resources."
else
    log_info "Docker system prune skipped."
fi

# =============================
# 6. Final message
# =============================
log_step "Uninstallation Complete!"
echo -e "${GREEN}Dream Recorder Pi system settings and services have been removed.${NC}"
echo -e "${YELLOW}You may want to manually remove any remaining config or data files in the project directory if desired.${NC}" 