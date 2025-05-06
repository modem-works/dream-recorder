# Dream Recorder

## Getting started

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
- To change config variables:
   - Run: `docker compose exec app python3 scripts/config_editor.py`
   - After saving (s) and quitting (q), reload the application by running: `docker compose restart app`


### For Developers (Local/Development)

To get the app running on your local machine:
   ```bash
   git clone <repo_url>
   cd dream-recorder
   cp .env.example .env
   cp config.example.json config.json
   # Add your API keys using vim, nano or any text editor you're compfortable with
   vim .env
   docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d
   # Edit the default config options (optional)
   docker compose exec app python3 scripts/config_editor.py
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

## Troubleshooting

- **Logs:**
  - App logs: `docker compose logs -f`
  - GPIO logs: `tail -f logs/gpio_service.log`
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

## Questions?

Open an issue or contact the lead maintainer for help:

<img src="https://github.com/markhinch.png" width="80px;"/><br /><a href="https://github.com/markhinch">@markhinch</a>
