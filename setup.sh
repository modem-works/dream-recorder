#!/bin/bash

# Function to log messages
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Check for install-service flag
INSTALL_SERVICE=false
SETUP_KIOSK=false
if [[ "$1" == "--install-service" ]]; then
    INSTALL_SERVICE=true
fi
if [[ "$1" == "--setup-kiosk" || "$2" == "--setup-kiosk" ]]; then
    SETUP_KIOSK=true
fi

# Kill any existing processes
log "Stopping any existing Dream Recorder processes..."
pkill -f 'python.*app.py|python.*gpio' || true
# Give processes time to shut down gracefully
sleep 2
# Force kill any remaining processes
pkill -9 -f 'python.*app.py|python.*gpio' 2>/dev/null || true
log "All existing processes stopped"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    log "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install requirements
log "Installing requirements..."
pip install -r requirements.txt

# Create necessary directories
log "Creating necessary directories..."
mkdir -p media media/audio media/video media/thumbs

# Initialize database if it doesn't exist
if [ ! -f "dreams.db" ]; then
    log "Initializing database..."
    python3 -c "from dream_db import DreamDB; DreamDB()._init_db()"
    log "Database initialized successfully"
else
    log "Database already exists"
fi

# Check for .env file
if [ ! -f ".env" ]; then
    log "Creating .env file from .env.example..."
    if [ -f ".env.example" ]; then
        cp .env.example .env
        log "Created .env file. Please update it with your API keys"
    else
        log "ERROR: .env.example file not found!"
        exit 1
    fi
fi

# Make startup and GPIO scripts executable
log "Making scripts executable..."
chmod +x startup.sh run_gpio.sh

# Install systemd service if requested
if [ "$INSTALL_SERVICE" = true ]; then
    log "Installing systemd service..."
    if [ -f "dream-recorder.service" ]; then
        # Update paths in service file to match current directory
        CURRENT_DIR=$(pwd)
        sed -i "s|WorkingDirectory=.*|WorkingDirectory=$CURRENT_DIR|g" dream-recorder.service
        sed -i "s|ExecStart=.*|ExecStart=$CURRENT_DIR/startup.sh|g" dream-recorder.service
        sed -i "s|User=pi|User=$(whoami)|g" dream-recorder.service
        
        # Install service
        sudo cp dream-recorder.service /etc/systemd/system/
        sudo systemctl daemon-reload
        sudo systemctl enable dream-recorder.service
        log "Service installed and enabled. To start it now, run: sudo systemctl start dream-recorder.service"
        
        # Install kiosk service if both flags are provided
        if [ "$SETUP_KIOSK" = true ] && [ -f "dream-recorder-kiosk.service" ]; then
            log "Installing kiosk mode service..."
            
            # Update user in kiosk service file
            sed -i "s|User=%USER%|User=$(whoami)|g" dream-recorder-kiosk.service
            sed -i "s|XAUTHORITY=/home/%USER%/.Xauthority|XAUTHORITY=/home/$(whoami)/.Xauthority|g" dream-recorder-kiosk.service
            
            # Install and enable kiosk service
            sudo cp dream-recorder-kiosk.service /etc/systemd/system/
            sudo systemctl daemon-reload
            sudo systemctl enable dream-recorder-kiosk.service
            log "Kiosk service installed and enabled. It will start automatically after the Dream Recorder service."
            log "To start it now, run: sudo systemctl start dream-recorder-kiosk.service"
        fi
    else
        log "Error: dream-recorder.service file not found"
    fi
fi

# Check if user has GPIO access (if on Raspberry Pi)
if [ -e "/dev/gpiomem" ]; then
    if [ -r "/dev/gpiomem" ] && [ -w "/dev/gpiomem" ]; then
        log "User has proper GPIO read/write permissions"
    else
        log "WARNING: User does not have proper GPIO permissions!"
        log "You might need to add your user to the gpio or dialout group:"
        log "  sudo usermod -a -G gpio,dialout $USER"
        log "Then log out and log back in for the changes to take effect"
    fi
fi

# Setup Chrome to start in kiosk mode at boot
if [ "$SETUP_KIOSK" = true ]; then
    log "Setting up Chrome kiosk mode autostart..."
    
    # Check if Chromium or Chrome is installed
    if command -v chromium-browser >/dev/null 2>&1; then
        BROWSER_CMD="chromium-browser"
    elif command -v chromium >/dev/null 2>&1; then
        BROWSER_CMD="chromium"
    elif command -v google-chrome >/dev/null 2>&1; then
        BROWSER_CMD="google-chrome"
    else
        log "Installing Chromium browser..."
        sudo apt-get update
        sudo apt-get install -y chromium-browser
        BROWSER_CMD="chromium-browser"
    fi
    
    # Create autostart directory if it doesn't exist
    mkdir -p ~/.config/autostart
    
    # Create desktop entry for autostart
    AUTOSTART_FILE=~/.config/autostart/dream-recorder-kiosk.desktop
    
    # Write desktop entry file
    cat > "$AUTOSTART_FILE" << EOL
[Desktop Entry]
Type=Application
Name=Dream Recorder Kiosk
Exec=$BROWSER_CMD --kiosk --no-first-run --disable-session-crashed-bubble --disable-infobars --app=http://localhost:5000
X-GNOME-Autostart-enabled=true
EOL
    
    # Create script to disable screen blanking and screensaver
    log "Creating script to disable screen blanking..."
    SCREEN_SCRIPT=~/disable-screen-blanking.sh
    
    cat > "$SCREEN_SCRIPT" << EOL
#!/bin/bash
# Disable screen blanking and screensaver
xset s off
xset s noblank
xset -dpms
EOL
    
    chmod +x "$SCREEN_SCRIPT"
    
    # Add script to autostart
    BLANKING_AUTOSTART=~/.config/autostart/disable-screen-blanking.desktop
    
    cat > "$BLANKING_AUTOSTART" << EOL
[Desktop Entry]
Type=Application
Name=Disable Screen Blanking
Exec=$SCREEN_SCRIPT
X-GNOME-Autostart-enabled=true
EOL
    
    log "Chrome kiosk mode has been set up to autostart on boot"
    log "The web interface will be available at http://localhost:5000"
    log "Note: You may need to restart your Raspberry Pi for changes to take effect"
fi

log "Setup complete!"
log "To run the application manually:"
log "  ./startup.sh"
log ""
log "To run with systemd (after installing the service):"
log "  sudo systemctl start dream-recorder.service"
log ""
log "To setup Chrome kiosk mode:"
log "  ./setup.sh --setup-kiosk"
log ""
log "To install both the service and kiosk mode:"
log "  ./setup.sh --install-service --setup-kiosk"
log ""
log "Once running, open http://localhost:5000 in your browser" 