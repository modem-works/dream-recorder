## Dream Recorder

## Quick Start

### For Developers (Local/Development)

1. **Clone the repository on your computer:**
   ```bash
   git clone <repo_url>
   cd dream-recorder
   ```
2. **Set up your API keys:**
   - Copy `.env.example` to `.env` and add your `OPENAI_API_KEY` and `LUMALABS_API_KEY`:
     ```bash
     cp .env.example .env
     # Edit .env and add your keys
     ```

3. **Edit `config.production.json` as needed** for development.

4. **Start in development mode (with live reload):**
   ```bash
   docker compose --profile dev run --service-ports dev
   ```
   - The app will be available at [http://localhost:5000](http://localhost:5000) (or the port in your config).

5. **Simulate sensor button presses:**
   ```bash
   ./python gpio_service.py --test
   ```
   - The app will be available at [http://localhost:5000](http://localhost:5000) (or the port in your config).

6. **Stop the app:**
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

2. **Edit `config.production.json` as needed** for your deployment.

3. **Run the setup and enable kiosk mode:**
   ```bash
   ./pi_installer.sh
   ```

4. **Reboot the Raspberry Pi:**
   ```bash
   sudo reboot
   ```

---

## Troubleshooting

- **Logs:**
  - App logs: `docker logs -f dream-recorder`
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
