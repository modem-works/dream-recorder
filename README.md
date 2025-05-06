# Dream Recorder

## Quick Start

### To get the Dream Recorder up and running on your Raspberry Pi

#### On your computer
- Download and install the Raspberry Pi imager software - https://www.raspberrypi.com/software/
- Plug the micro SD card into your computer using an SD card reader
- Open the Raspberry Pi imager software and install it using the following details:
   - Raspberry Pi OS (64-bit)
   - Choose to edit the customisation settings
      - General:
         - Hostname: dreamer
         - Username: dreamer
         - Password: (choose a simple password)
         - Type in your WiFi network's SSID & password carefully
      - Services:
         Enable SSH using password authentication
- Once the installation has finished, safely eject and remove the microSD card

#### On the Raspberry Pi
- Insert the microSD card into the Raspberry Pi
- Plug the Raspberry Pi in using the power supply and wait for it to boot up

#### On your computer
- Find the IP address of the Raspberry Pi in one of the following ways:
   1. On the device:
      - Plug in a USB mouse to the Raspberry Pi
      - Click on the Wifi icon on the top right of the screen
      - Advanced Options -> Connection Information
      - Note the IP address (e.g. 192.168.1.100)
   2. Use your network router's admin software interface to find all connected devices and find the Raspberry Pi
   3. Use nmap in a Terminal window:
      - Install nmap on your system if it's not already installed)
      - Open a terminal and find your IP by running this command: ifconfig
      - Make a note of your computer's IP address (e.g. 192.168.1.100)
      - Run this command: `nmap -sn 192.168.1.0/24 | grep dreamer` - keeping the first three numbers sets the same as your computer's IP (eg. 192.168.1.) and leaving the 0/24 at the end

#### In a Terminal on your computer
- SSH into the Dream Recorder with this command: `ssh dreamer@X.X.X.X` (using the simple password you created in the Raspberry Pi imager)
- Run the Raspberry Pi config tool by running this command: `sudo raspi-config`
   - Interface Options -> VNC -> Yes -> OK
   - Localisation Options -> Configure time zone -> Choose your country & city
   - Select \<Finish\>
- Keep this terminal window open for later   

#### On your computer
- [Download RealVNC](https://www.realvnc.com/en/connect/download), install and run it
   - Connect to the Dream Recorder's IP address using the username (dreamer) and your simple password
   - You should now have remote desktop access to the Raspberry Pi
   - Change the screen's orientation:
      - Click the Raspberry Pi icon (top left) -> Preferences -> Screen Configuration
      - Right click on the HDMI-A-1 screen -> Orientation -> "Right" -> OK
   - Close RealVNC
- Generate an API key for OpenAI:
   - Login / sign up to [OpenAI](https://platform.openai.com/api-keys) and create a secret / API key
   - Copy the value and paste it to a text file temporarily as you will need it shortly
   - Add a few dollars of credits to your account ($5 suggested)
- Generate an API key for LumaLabs:
   - Login / sign up to [LumaLabs](https://lumalabs.ai/api/dashboard) and create a secret / API key
   - Copy the value and paste it to a text file temporarily as you will need it shortly
   - Add a few dollars of credits to your account ($20 suggested)

#### In the Terminal on your computer (which should still be connected to the Raspberry Pi via SSH)
- Clone the Dream Recorder from Github: git clone <repo_ssh_url>
- Once completed, navigate into the repo folder: `cd dream-recorder`
- Run the installer: `./pi_installer.sh`
   - When prompted, paste in the two API keys generated above
- Reboot the Raspberry Pi: `sudo reboot`

### For Developers (Local/Development)

To get the app running on your local machine:
   ```bash
   git clone <repo_url>
   cd dream-recorder
   cp .env.example .env
   cp config.example.json config.json
   vim .env
   # Add your API keys
   docker compose --profile dev run --service-ports dev
   ```
The app will be available at [http://localhost:5000](http://localhost:5000)

To simulate sensor button presses:
```bash
python gpio_service.py --test
```
To stop the app:
```bash
docker compose down
```

## Troubleshooting on the Raspberry Pi

- **Logs:**
  - App logs: `docker logs -f dream-recorder`
  - GPIO logs: `logs/gpio_service.log`
- **Check running services:**
  ```bash
  docker ps
  ps aux | grep gpio_service.py
  ps aux | grep chromium-browser
  ```
- **Stop the services:**
  ```bash
  docker compose down
  systemctl --user stop dream-recorder-gpio.service
  ```
- **Restart the services:**
  ```bash
  docker compose up -d
  systemctl --user start dream-recorder-gpio.service
  ```

---

## Customizing the Clock's appearance

You can customize the clock display by editing or replacing the JSON file referenced by `CLOCK_CONFIG_PATH` in your config.

## Customizing overall functionality

The application's behavior can be customized by editing the variables in your config file (e.g. `config.json`). Here is a list of each configurable variable, what it controls, and the values it accepts:

| Variable | Description | Accepted Values / Type |
|---|---|---|
| **LOG_LEVEL** | Sets the logging verbosity. | "DEBUG", "INFO", "WARNING", "ERROR" |
| **HOST** | The internal network interface the server binds to. | String (e.g. "0.0.0.0", "127.0.0.1") |
| **PORT** | The port the server listens on. | Integer (e.g. 5000) |
| **TOTAL_BACKGROUND_IMAGES** | Number of available background images for the UI (in static/images/background). | Integer (e.g. 1119) |
| **CLOCK_FADE_IN_DURATION** | Milliseconds taken for the clock to fade in. | Integer (ms) |
| **CLOCK_FADE_OUT_DURATION** | Milliseconds taken for the clock to fade out. | Integer (ms) |
| **CLOCK_CONFIG_PATH** | Path to the JSON file defining the clock's appearance and behavior. | String (file path) |
| **PLAYBACK_DURATION** | Duration (in seconds) for audio/video playback. | Integer (seconds) |
| **VIDEO_HISTORY_LIMIT** | Number of videos to loop through in the device's history. | Integer |
| **LOGO_FADE_IN_DURATION** | Milliseconds taken for the logo to fade in. | Integer (ms) |
| **LOGO_FADE_OUT_DURATION** | Milliseconds taken for the logo to fade out. | Integer (ms) |
| **TRANSITION_DELAY** | Delay (in milliseconds) between UI transitions. | Integer (ms) |
| **AUDIO_CHANNELS** | Number of audio channels to record. | 1 (mono), 2 (stereo) |
| **AUDIO_SAMPLE_WIDTH** | Audio sample width in bytes. | Integer (e.g. 2 for 16-bit) |
| **AUDIO_FRAME_RATE** | Audio sample rate in Hz. | Integer (e.g. 44100) |
| **RECORDINGS_DIR** | Directory where audio recordings are stored. | String (directory path) |
| **WHISPER_MODEL** | Name of the OpenAI Whisper model to use for transcription. | String (e.g. "whisper-1, gpt-4o-transcribe, gpt-4o-mini-transcribe") |
| **GPT_MODEL** | Name of the OpenAI GPT model to use for prompt generation. | String (e.g. "gpt-4o-mini, gpt-4o, o1-mini, etc...") |
| **GPT_SYSTEM_PROMPT** | System prompt for the GPT model (single-sentence version). | String |
| **GPT_SYSTEM_PROMPT_EXTEND** | System prompt for the GPT model (two-sentence/extended version). | String |
| **GPT_TEMPERATURE** | Sampling temperature for GPT. | Float (0.0–2.0, e.g. 0.7) |
| **GPT_MAX_TOKENS** | Maximum number of tokens for GPT responses. | Integer (e.g. 400) |
| **LUMA_API_URL** | Base URL for the Luma Labs API. | String (URL) |
| **LUMA_GENERATIONS_ENDPOINT** | Endpoint for generating videos with Luma Labs. | String (URL) |
| **LUMA_EXTEND** | Whether to use the Luma 'extend' feature - which will a generated video and send it back to be doubled in length. | Boolean (true/false) |
| **LUMA_MODEL** | Luma model to use for video generation. | String (e.g. "ray-flash-2, ray-2, ray-1-6") |
| **LUMA_RESOLUTION** | Output video resolution. | String ("540p, 720p, 1080 or 4k") |
| **LUMA_DURATION** | Duration of generated videos. | String ("5s or 9s") |
| **LUMA_ASPECT_RATIO** | Aspect ratio for generated videos. | String ("21:9") |
| **LUMA_POLL_INTERVAL** | Seconds between polling Luma for video generation status. | Integer (seconds) |
| **LUMA_MAX_POLL_ATTEMPTS** | Maximum number of polling attempts for Luma video generation before giving up. | Integer |
| **VIDEOS_DIR** | Directory where generated videos are stored. | String (directory path) |
| **THUMBS_DIR** | Directory where video thumbnails are stored. | String (directory path) |
| **FFMPEG_BRIGHTNESS** | Brightness adjustment for video processing. | Float (e.g. 0.2) |
| **FFMPEG_VIBRANCE** | Vibrance adjustment for video processing. | Float (e.g. 2) |
| **FFMPEG_DENOISE_THRESHOLD** | Denoise threshold for video processing. | Integer |
| **FFMPEG_BILATERAL_SIGMA** | Bilateral filter sigma value for video processing. | Integer |
| **FFMPEG_NOISE_STRENGTH** | Noise strength for video processing. | Integer |
| **GPIO_PIN** | GPIO pin number used for the physical button. | Integer (e.g. 4) |
| **GPIO_FLASK_URL** | URL of the Flask server for GPIO events. | String (URL) |
| **GPIO_SINGLE_TAP_ENDPOINT** | API endpoint for single-tap button events. | String (endpoint path) |
| **GPIO_DOUBLE_TAP_ENDPOINT** | API endpoint for double-tap button events. | String (endpoint path) |
| **GPIO_SINGLE_TAP_MAX_DURATION** | Max duration (seconds) for a single tap to be recognized. | Float (seconds) |
| **GPIO_DOUBLE_TAP_MAX_INTERVAL** | Max interval (seconds) between taps for a double tap. | Float (seconds) |
| **GPIO_DEBOUNCE_TIME** | Debounce time (seconds) for button presses. | Float (seconds) |
| **GPIO_STARTUP_DELAY** | Delay (seconds) before GPIO service starts after boot. | Integer (seconds) |
| **GPIO_SAMPLING_RATE** | Sampling rate (seconds) for reading GPIO pin state. | Float (seconds) |

## Questions?

Open an issue or contact the maintainer for help!
