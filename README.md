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
   docker compose --profile dev run --service-ports dev
   ```
   - The app will be available at [http://localhost:5000](http://localhost:5000) (or the port in your config).
   - The `dev` service is now only started when the `dev` profile is specified.

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

4. **Run the setup and enable kiosk mode:**
   ```bash
   ./install_dream_recorder.sh
   ```
   - This will copy all necessary files, set permissions, and enable the user-level systemd service for kiosk mode.

5. **Log out and log back in (or reboot) to start kiosk mode.**
   - Chromium will launch in kiosk mode after you log in to the graphical desktop.

6. **If you ever need to start the app and GPIO service manually:**
   ```bash
   ./start_dream_recorder_pi.sh
   ```

7. **...or to stop them:**
   ```bash
   ./stop_dream_recorder_pi.sh
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
