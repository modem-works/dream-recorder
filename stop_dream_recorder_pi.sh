#!/bin/bash
# stop_dream_recorder_pi.sh
# Stops the Dream Recorder Docker app, GPIO service, and Chromium on Raspberry Pi.

# Check if running on a Raspberry Pi
if ! grep -q "Raspberry Pi" /proc/device-tree/model 2>/dev/null; then
    echo "ERROR: This script is intended to be run on a Raspberry Pi only." >&2
    exit 1
fi

# Stop Docker Compose app
echo "Stopping Dream Recorder Docker container..."
docker compose down

# Kill GPIO service
echo "Stopping GPIO service..."
GPIO_PID=$(ps aux | grep '[g]pio_service.py' | awk '{print $2}')
if [ -n "$GPIO_PID" ]; then
    kill $GPIO_PID
    echo "GPIO service (PID $GPIO_PID) stopped."
else
    echo "GPIO service not running."
fi

# Optionally, stop Chromium
CHROME_PID=$(ps aux | grep '[c]hromium-browser' | awk '{print $2}')
if [ -n "$CHROME_PID" ]; then
    kill $CHROME_PID
    echo "Chromium browser (PID $CHROME_PID) stopped."
else
    echo "Chromium browser not running."
fi

echo "All Dream Recorder services stopped." 