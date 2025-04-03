#!/bin/bash

# Function to log messages
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Check for install-service flag
INSTALL_SERVICE=false
if [[ "$1" == "--install-service" ]]; then
    INSTALL_SERVICE=true
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
mkdir -p data/audio videos recordings

# Check for .env file
if [ ! -f ".env" ]; then
    log "Creating .env file from .env.example..."
    if [ -f ".env.example" ]; then
        cp .env.example .env
        # Generate a random secret key
        SECRET_KEY=$(openssl rand -hex 16)
        sed -i "s/SECRET_KEY=\"generate-a-secret-key-here\"/SECRET_KEY=\"$SECRET_KEY\"/g" .env
        log "Created .env file. Please update it with your API keys"
    else
        log "Error: .env.example file not found"
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

log "Setup complete!"
log "To run the application manually:"
log "  ./startup.sh"
log ""
log "To run with systemd (after installing the service):"
log "  sudo systemctl start dream-recorder.service"
log ""
log "Once running, open http://localhost:5000 in your browser" 