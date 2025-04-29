## Dream Recorder

Dream Recorder is an application designed to run on a Raspberry Pi 5, allowing you to record and review your dreams with simple touch interactions.

## Setup

### Hardware Setup

1. Install Raspberry Pi Imager
   - Set up configuration in Pi Imager
2. Find device IP (?)
3. SSH into device (dreamer@IP)
   - sudo raspi-config
      - Interface Options -> VNC -> Yes -> OK
      - Localisation Options -> Configure time zone -> Choose your country & city
      - <Finish>
4. VNC connect
   - Start menu -> Preferences -> Screen Configuration
      - Right click on screen -> Orientation -> Left
      - Drag window a bit to the left and click Apply, then click OK
5. Use SSH connection
   - git clone <repo_url>
   - cd dream-recorder
6. Update your API keys in the `.env` file.
7. Run setup and startup
8. Push button and use VNC to allow microphone access

### Development Setup

1. Create and activate a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Copy `.env.example` to `.env` and update the configuration:
   ```bash
   cp .env.example .env
   ```

4. Start the application in development mode:
   ```bash
   ./startup.sh --dev
   ```

## Usage

The Dream Recorder uses a simple touch interface with two interaction patterns:

1. **Single Tap**: Shows the previous dream recording. If you're currently recording, it will stop the recording.
   - During playback: Shows the next dream in sequence
   - During clock view: Shows the most recent dream
   - During recording: Stops the recording

2. **Double Tap**: Starts a new recording when in clock view, or returns to clock view during playback
   - During clock view: Starts recording
   - During playback: Returns to clock view

## Directory Structure

```
dream-recorder/
├── app.py              # Main Flask application
├── gpio_service.py     # GPIO interaction service
├── static/            # Static assets (JS, CSS, etc.)
├── templates/         # HTML templates
├── scripts/          # Utility scripts
├── media/            # Stored media files
│   ├── audio/       # Audio recordings
│   ├── video/       # Processed videos
│   └── thumbs/      # Video thumbnails
└── logs/            # Application logs
```

## Development

To run the application in development mode with auto-reload:

```bash
./startup.sh --dev
```

For production deployment:

```bash
./startup.sh
```

## Troubleshooting

If you encounter issues:

1. Check the logs:
   ```bash
   tail -f logs/flask_app.log
   tail -f logs/gpio_service.log
   ```

2. Ensure all required services are running:
   ```bash
   ps aux | grep python
   ```

3. Restart the application:
   ```bash
   pkill -f 'python.*app.py|python.*gpio'
   ./startup.sh
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

## Features

### Dream Recording
- Record your dreams using the built-in microphone
- Automatic transcription using OpenAI's Whisper
- AI-powered video generation from your dream descriptions
- Real-time audio visualization

### Dreams Library
- View all your recorded dreams in one place
- Search and sort through your dream history
- Access audio and video recordings
- View detailed information about each dream
- Paginated interface for easy navigation

## Database

Dream Recorder uses SQLite to store all your dreams and their associated data. The database includes:
- User prompts (transcriptions)
- Generated prompts
- Audio file paths
- Video file paths
- Creation timestamps
- Duration information
- Status tracking
- Additional metadata

The database is automatically created and managed by the application. All dreams are stored locally on your device. 