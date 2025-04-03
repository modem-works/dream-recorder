# Dream Recorder

Dream Recorder is an application designed to run on a Raspberry Pi 5, allowing you to record and visualize your dreams.

## Setup

### Basic Setup

1. Clone this repository to your Raspberry Pi.
2. Run the setup script:
   ```
   ./setup.sh
   ```
3. Update your API keys in the `.env` file.

### Running the Application

To run the application manually:
```
./startup.sh
```

Once running, open http://localhost:5000 in your browser.

### Installing as a Service

To install Dream Recorder as a service that starts automatically on boot:
```
./setup.sh --install-service
```

This will create and enable a systemd service. To start it immediately:
```
sudo systemctl start dream-recorder.service
```

## Kiosk Mode Setup

Dream Recorder can be set up to run in kiosk mode, where the application opens in a full-screen Chrome browser window on boot.

### Desktop Environment Autostart (Recommended for most users)

To set up kiosk mode using the desktop environment autostart:
```
./setup.sh --setup-kiosk
```

This will:
1. Install Chromium browser if not already installed
2. Create autostart entries to launch Chrome in kiosk mode
3. Set up screen blanking prevention

### Systemd Service Kiosk Mode (Advanced)

For more reliable kiosk mode that works regardless of the desktop environment:
```
./setup.sh --install-service --setup-kiosk
```

This will:
1. Install the Dream Recorder service
2. Install a separate kiosk mode service that starts after the main service
3. Configure both to start at boot

After installation, reboot your Raspberry Pi. The Dream Recorder application should automatically start and open in a full-screen Chrome window.

### Troubleshooting Kiosk Mode

If the kiosk mode doesn't start automatically:

1. Check if the services are running:
   ```
   sudo systemctl status dream-recorder.service
   sudo systemctl status dream-recorder-kiosk.service
   ```

2. Verify the application is running:
   ```
   curl http://localhost:5000
   ```

3. If using desktop autostart, check if the files were created:
   ```
   ls -la ~/.config/autostart/
   ```

4. Ensure your user has proper permissions:
   ```
   ls -la /home/$(whoami)/.Xauthority
   ```

## Hardware Requirements

- Raspberry Pi 5 (4 may also work)
- Capacitive touch sensor (TTP223B) connected to GPIO pin 4
- USB microphone
- Display connected via HDMI
- Internet connection for API access 