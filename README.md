## Dream Recorder

Dream Recorder is an application designed to run on a Raspberry Pi 5, allowing you to record and review your dreams with simple touch interactions.

---

## Quick Start

### For Developers (Local/Development)

1. **Clone the repository:**
   ```bash
   git clone <repo_url>
   cd dream-recorder
   ```

2. **Set up your API keys:**
   - Copy `.env.example` to `.env` and add your `OPENAI_API_KEY` and `LUMALABS_API_KEY` (no quotes):
     ```bash
     cp .env.example .env
     # Edit .env and add your keys
     ```

3. **Edit configuration as needed:**
   - All non-secret config is in `config.development.json` (for dev) and `config.production.json` (for prod).

4. **Start in development mode (with live reload):**
   ```bash
   docker compose run --service-ports dev
   ```
   - The app will be available at [http://localhost:5000](http://localhost:5000) (or the port in your config).

5. **Stop the app:**
   ```bash
   docker compose down
   ```

---

### For Deployers (Raspberry Pi/Production)

1. **Clone the repository on your Raspberry Pi:**
   ```bash
   git clone <repo_url>
   cd dream-recorder
   ```

2. **Set up your API keys:**
   - Copy `.env.example` to `.env` and add your `OPENAI_API_KEY` and `LUMALABS_API_KEY` (no quotes):
     ```bash
     cp .env.example .env
     # Edit .env and add your keys
     ```

3. **Edit `config.production.json` as needed** for your deployment.

4. **Start the app, GPIO service, and Chromium in kiosk mode:**
   ```bash
   ./start_dream_recorder_pi.sh
   ```
   - This will start the Docker app, the GPIO service, and launch Chromium in kiosk mode.

5. **(Optional) Enable auto-start on boot:**
   ```bash
   sudo ./start_dream_recorder_pi.sh --install-systemd
   ```
   - This will install a systemd service so the app starts automatically on boot.

6. **Stop all services:**
   ```bash
   ./stop_dream_recorder_pi.sh
   ```

---

## Directory Structure

```
dream-recorder/
├── app.py              # Main Flask application
├── gpio_service.py     # GPIO interaction service
├── start_dream_recorder_pi.sh   # Start everything on Raspberry Pi
├── stop_dream_recorder_pi.sh    # Stop everything on Raspberry Pi
├── config.development.json      # Dev config
├── config.production.json       # Production config
├── .env.example        # Example for API keys
├── media/              # Stored media files (audio, video, thumbs)
├── logs/               # Application logs
├── static/             # Static assets (JS, CSS, etc.)
├── templates/          # HTML templates
├── scripts/            # Utility scripts
└── ...
```

---

## Configuration

- **API keys:** Only `OPENAI_API_KEY` and `LUMALABS_API_KEY` go in `.env`.
- **All other config:** Use `config.development.json` (for dev) and `config.production.json` (for prod).
- **Switching environments:** The app automatically loads the correct config based on the `FLASK_ENV` environment variable (set in Docker Compose or by the start script).

---

## Troubleshooting

- **Logs:**
  - App logs: `logs/flask_app.log`
  - GPIO logs: `logs/gpio_service.log`
- **Check running services:**
  ```bash
  docker ps
  ps aux | grep gpio_service.py
  ps aux | grep chromium-browser
  ```
- **Stop all services:**
  ```bash
  ./stop_dream_recorder_pi.sh
  ```
- **Restart everything:**
  ```bash
  ./stop_dream_recorder_pi.sh
  ./start_dream_recorder_pi.sh
  ```

---

## Hardware Requirements

- Raspberry Pi 5 (4 may also work)
- Capacitive touch sensor (TTP223B) connected to GPIO pin 4
- USB microphone
- Display connected via HDMI
- Internet connection for API access

---

## Features

- Record your dreams using the built-in microphone
- Automatic transcription using OpenAI's Whisper
- AI-powered video generation from your dream descriptions
- Real-time audio visualization
- View all your recorded dreams in one place
- Touch interface: single/double tap for navigation and recording
- Kiosk mode: full-screen browser on boot (optional)

---

## Advanced: Customizing the Clock

You can customize the clock display by editing or replacing the JSON file referenced by `CLOCK_CONFIG_PATH` in your config.

---

## Questions?

Open an issue or contact the maintainer for help!
