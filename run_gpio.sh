#!/bin/bash

# Simple GPIO Service for Dream Recorder
# This script runs the GPIO controller service directly

# Get absolute path to script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Change to the script directory
cd "$SCRIPT_DIR"

# Log start
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting GPIO service..."

# Kill any existing GPIO processes
pkill -f 'python.*gpio_service.py' || true
sleep 1

# Create the GPIO script
cat > "$SCRIPT_DIR/gpio_script.py" << 'EOF'
#!/usr/bin/env python3
import RPi.GPIO as GPIO
import time
import requests
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define the GPIO pin number where the touch sensor is connected
TOUCH_PIN = 4
FLASK_URL = "http://localhost:5000/api/trigger_recording"

# Set up GPIO
logger.info("Setting up GPIO...")
GPIO.setmode(GPIO.BCM)
GPIO.setup(TOUCH_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
logger.info("GPIO setup complete")

try:
    logger.info("GPIO monitor started. Press Ctrl+C to exit.")
    while True:
        if GPIO.input(TOUCH_PIN) == GPIO.HIGH:
            logger.info("Touch detected!")
            try:
                response = requests.post(FLASK_URL)
                if response.status_code == 200:
                    logger.info("Recording triggered successfully")
                else:
                    logger.error(f"Failed to trigger recording: {response.status_code}")
            except Exception as e:
                logger.error(f"Error triggering recording: {str(e)}")
        time.sleep(0.1)
except KeyboardInterrupt:
    logger.info("GPIO monitor shutting down...")
except Exception as e:
    logger.error(f"Error: {str(e)}")
finally:
    GPIO.cleanup()
    logger.info("GPIO resources cleaned up")
EOF

# Make the script executable
chmod +x "$SCRIPT_DIR/gpio_script.py"

# Run the script directly and log output
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Running GPIO service..."

# Run with system Python to ensure GPIO access works correctly
PATH=/usr/local/bin:/usr/bin:/bin
cd "$SCRIPT_DIR"
python3 "$SCRIPT_DIR/gpio_script.py" > "$SCRIPT_DIR/gpio_service.log" 2>&1 &

# Log the PID
PID=$!
echo "[$(date '+%Y-%m-%d %H:%M:%S')] GPIO service started with PID: $PID" 