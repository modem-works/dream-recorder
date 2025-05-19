# Dream Recorder
<a href="./docs/images/logo.jpg"><img src="./docs/images/logo.jpg" width="100%" /></a>

## About the physical device

### Shopping list / Bill Of Materials
To build a Dream Recorder, these are the components you will need. The overall cost for these components from the provided links is approximately €285 (Last updated May 2025).

| Item | URL |
| - | - |
| Waveshare 7.9 inch HDMI IPS-TFT-LCD Display 1280x400 | [https://www.tinytronics.nl/nl/displays...](https://www.tinytronics.nl/nl/displays/tft/waveshare-7.9-inch-hdmi-ips-tft-lcd-display-1280*400-pixels-met-touchscreen-raspberry-pi-compatible) |
| Raspberry Pi 5 8GB | [https://www.amazon.nl/Raspberry-Pi...](https://www.amazon.nl/Raspberry-Pi-SC1112-5-8GB/dp/B0CK2FCG1K) |
| USB-C adapter for 5.1V, 5A, 27W (these specs are important) | https://www.amazon.nl/dp/B0D41VN574 |
| Waveshare Active Cooler | https://www.amazon.nl/dp/B0CPLQB4RK |
| MicroSDXC UHS-I-Card - 64 GB | https://www.amazon.nl/dp/B0B7NXBM6P |
| TTP223B Capacitive Touch Sensor | https://www.amazon.nl/dp/B07XPMH2NZ |
| Dupont Jumper Wires - 10 cm (you need 3 x female-female) | https://www.amazon.nl/dp/B07GJLCGG8 |
| USB microphone | https://www.amazon.nl/dp/B0BWFTQL95 |
| 90 degree right-angled FPV male-male HDMI ribbon cable (20cm) | https://www.amazon.nl/dp/B08C7G4J6B |
| 90 degree right-angled FPV male-male Micro-HDMI ribbon cable (20cm) | https://www.amazon.nl/dp/B0177EWVMQ |
| Up-angled USB 2.0 male Type-A to male Micro-USB ribbon cable (20cm) | https://www.amazon.nl/dp/B095LVLTLJ |
| 90 degree USB-C adapter | https://www.amazon.nl/dp/B0DGD52DL3 |
| M2.5 nylon screwset (you need 4 x 15mm male-female stands) | https://www.amazon.nl/dp/B0DCS5C7SN |
| PLA filament - 1.75mm, transparant | https://www.amazon.nl/dp/B07Q1PGH4B |

### What it costs to dream
In order to generate dreams, this application uses OpenAI and LumaLabs' APIs. The approximate costs are as follows (last updated May 2025):

- OpenAI text-to-speech and video prompt generation: < $ 0.01 per dream - [OpenAI Pricing](https://openai.com/api/pricing)
- LumaLabs dream generation (using 540p, 21:9, 5 seconds, ray-flash-2): $ 0.14 per dream - [LumaLabs Pricing](https://lumalabs.ai/api/pricing)

## Getting your Dream Recorder set up

### Building the device

![Dream Recorder components](./docs/images/components.gif "Dream Recorder components")

📄 [Assembly Guide (PDF)](./docs/manuals/assembly_guide.pdf)

### Installing & configuring the OS

#### 💻️ <u>On your computer</u>

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

<details>
   <summary>See step-by-step images 🖼️</summary>

   |<a href="./docs/images/rpi_imager_1.jpg"><img style="display: block; width: 450px;" src="./docs/images/rpi_imager_1.jpg"/></a>|<a href="./docs/images/rpi_imager_2.jpg"><img style="display: block; width: 450px;" src="./docs/images/rpi_imager_2.jpg"/></a>|
   |--|--|
   |<a href="./docs/images/rpi_imager_3.jpg"><img style="display: block; width: 450px;" src="./docs/images/rpi_imager_3.jpg"/></a>|<a href="./docs/images/rpi_imager_4.jpg"><img style="display: block; width: 450px;" src="./docs/images/rpi_imager_4.jpg"/></a>|
   |<a href="./docs/images/rpi_imager_5.jpg"><img style="display: block; width: 450px;" src="./docs/images/rpi_imager_5.jpg"/></a>|<a href="./docs/images/rpi_imager_6.jpg"><img style="display: block; width: 450px;" src="./docs/images/rpi_imager_6.jpg"/></a>|
   |<a href="./docs/images/rpi_imager_7.jpg"><img style="display: block; width: 450px;" src="./docs/images/rpi_imager_7.jpg"/></a>|<a href="./docs/images/rpi_imager_8.jpg"><img style="display: block; width: 450px;" src="./docs/images/rpi_imager_8.jpg"/></a>|
   |<a href="./docs/images/rpi_imager_9.jpg"><img style="display: block; width: 450px;" src="./docs/images/rpi_imager_9.jpg"/></a>|<a href="./docs/images/rpi_imager_10.jpg"><img style="display: block; width: 450px;" src="./docs/images/rpi_imager_10.jpg"/></a>|
   |<a href="./docs/images/rpi_imager_11.jpg"><img style="display: block; width: 450px;" src="./docs/images/rpi_imager_11.jpg"/></a>|<a href="./docs/images/rpi_imager_12.jpg"><img style="display: block; width: 450px;" src="./docs/images/rpi_imager_12.jpg"/></a>|
</details>

#### 🍓 <u>On the Raspberry Pi</u>
- Insert the microSD card into the Raspberry Pi
- Plug the Raspberry Pi in using the power supply and wait for it to boot up

#### Finding the Raspberry Pi's local IP address
You now need to find the IP address that your local network has assigned to the Raspberry Pi. You can do this in one of three ways:
1.  EASY: On the device:
    -   Plug a USB mouse in to the Raspberry Pi
    -   Click on the Wifi icon on the top right of the screen
    -   Advanced Options -> Connection Information
    -   Note the IP address (e.g. 192.168.1.100)
    - ...or...
2.  MEDIUM: On your network router's admin software interface:
	- This approach's exact steps will depend on what your home network's router and software is
	- Essentially you will need to find all connected devices and find the Raspberry Pi
    - ...or...
3.  HARD: In a Terminal console on your computer:
    - Open up a terminal window
    - Check if you have nmap installed by running:
	    - `nmap`
	    - If it's not installed, do so now - [Downloads & instructions](https://nmap.org/download.html)
    -   Find your computer's IP by either:
	    1. Running this command in the terminal:
		    - `ifconfig | grep "inet "`
		    -   Make a note of your computer's IP address (which will most likely look something like `192.168.X.X`)
		    - ...or...
	    2. Referring to your computer's Wifi / Ethernet connection details via settings
    -   Run this command in the terminal, keeping the first three numbers sets the same as your computer's IP and leaving the 0/24 at the end:
	    - `nmap -sn 192.168.1.0/24 | grep dreamer`
	    - So if your computer's IP address is 192.168.1.100 for example, you would run: `nmap -sn 192.168.1.0/24 | grep dreamer`

#### 💻️ <u>On your computer (in a Terminal window)</u>

- Open up a terminal / command line / bash window
- SSH into the Dream Recorder with the following command, using the simple password you created in the Raspberry Pi imager:
   - `ssh dreamer@<DREAM_RECORDER_IP_ADDRESS>`
- Run the Raspberry Pi config tool by running this command:
   - `sudo raspi-config`
   - Interface Options -> VNC -> Yes -> OK
   - Localisation Options -> Configure time zone -> Choose your country & city
   - Select \<Finish\>
- Keep this terminal window open for later   

<details>
   <summary>See step-by-step images 🖼️</summary>

   |<a href="./docs/images/raspi_config_1.jpg"><img style="display: block; width: 450px;" src="./docs/images/raspi_config_1.jpg"/></a>|<a href="./docs/images/raspi_config_2.jpg"><img style="display: block; width: 450px;" src="./docs/images/raspi_config_2.jpg"/></a>|
   |--|--|
   |<a href="./docs/images/raspi_config_3.jpg"><img style="display: block; width: 450px;" src="./docs/images/raspi_config_3.jpg"/></a>|<a href="./docs/images/raspi_config_4.jpg"><img style="display: block; width: 450px;" src="./docs/images/raspi_config_4.jpg"/></a>|
   |<a href="./docs/images/raspi_config_5.jpg"><img style="display: block; width: 450px;" src="./docs/images/raspi_config_5.jpg"/></a>|<a href="./docs/images/raspi_config_6.jpg"><img style="display: block; width: 450px;" src="./docs/images/raspi_config_6.jpg"/></a>|
</details>

### Getting yourself connected to the Pi

#### 💻️ <u>On your computer</u>

- [Download RealVNC](https://www.realvnc.com/en/connect/download), install and run it
   - Connect to the Dream Recorder using the hostname (dreamer), the username (dreamer) and your simple password
   - You now have remote desktop access to the Raspberry Pi
   - Change the screen's orientation:
      - Click the Raspberry Pi icon (top left) -> Preferences -> Screen Configuration
      - Right click on the HDMI-A-1 screen -> Orientation -> "Right" -> OK
      - Drag the window to the left so you can click the "Apply" button
      - Navigating with the mouse might become tricky now, so you can use your keyboard as follows:
         - \<tab\> \<tab\> \<spacebar\>
   - Close RealVNC

<details>
   <summary>See step-by-step images 🖼️</summary>

   |<a href="./docs/images/vnc_viewer_1.jpg"><img style="display: block; width: 250px;" src="./docs/images/vnc_viewer_1.jpg"/></a>|<a href="./docs/images/vnc_viewer_2.jpg"><img style="display: block; width: 250px;" src="./docs/images/vnc_viewer_2.jpg"/></a>|<a href="./docs/images/vnc_viewer_3.jpg"><img style="display: block; width: 250px;" src="./docs/images/vnc_viewer_3.jpg"/></a>|
   |--|--|--|

   <a href="./docs/images/vnc_viewer_4.jpg"><img style="display: block; width: 800px;" src="./docs/images/vnc_viewer_4.jpg"/></a>
</details>

#### 💻️ <u>On your computer (in a web browser)</u>

- Generate an API key for OpenAI:
   - Login / sign up to [OpenAI](https://platform.openai.com/api-keys) and create a secret / API key
   - Copy the value and paste it to a text file temporarily as you will need it shortly
   - Add a few dollars of credits to your account (~$5 suggested)
- Generate an API key for LumaLabs:
   - Login / sign up to [LumaLabs](https://lumalabs.ai/api/dashboard) and create a secret / API key
   - Copy the value and paste it to a text file temporarily as you will need it shortly
   - Add a few dollars of credits to your account (~$20 suggested)
- Copy the URL of the Git repository at the top of this Github page by clicking on the Code button at the top right and copying the 'HTTP' url

#### 💻️ <u>On your computer (in the Terminal window)</u>
- Make sure you are still connected to the Dream Recorder
   - If not, connect again:
      - `ssh dreamer@<DREAM_RECORDER_IP_ADDRESS>`
- Clone the Dream Recorder from Github using the URL you just copied in the step above
   - `git clone <repo_ssh_url>`
- Once completed, navigate into the repo folder:
   - `cd dream-recorder`
- Run the installer:
   - `./pi_installer.sh`
   - When prompted, paste in each of the API keys you generated above
- Reboot the Raspberry Pi: `sudo reboot`
- You are now up and running once the Pi has rebooted!

## Using the Dream Recorder
- Single tap: Play the latest dream
   - Single tapping while a dream is playing will play the previous dream
   - Double tapping while a dream is playing will go back to clock mode
- Double tap: Record a dream
   - Single tap once you are done talking for the dream to be generated

<br />

> <br />*You should be good to go with your Dream Recorder now! Everything below is mostly for those that want to take things further to start tinkering and contributing*<br /><br />

## Configuring the Dream Recorder (optional)
To change the default settings for the Dream Recorder, you can use the command line configuration tool:

- SSH into the Dream Recorder with the following command, using the simple password you created in the Raspberry Pi imager:
   - `ssh dreamer@<DREAM_RECORDER_IP_ADDRESS>`
- Navigate to the Dream Recorder's root folder:
   - `cd dream-recorder`
- Run this command:
   `./dreamctl config`
- After saving (s) and quitting (q), reload the application (if you've changed any core, non-superficial configurations) by running:
   - `docker compose restart`

<details>
   <summary>See step-by-step images 🖼️</summary>

   <a href="./docs/images/config_tool_1.jpg"><img style="display: block; width: 450px;" src="./docs/images/config_tool_1.jpg"/></a>
</details>

## Taking things further

### To get the Dream Recorder up and running on your local machine (for developers & contributors)
- Note: You will need Docker (Compose) installed on your system - [Docker documentation](https://docs.docker.com/compose/install)

```bash
git clone <repo_url>
cd dream-recorder
cp ./.env.example ./.env
cp ./config.example.json ./config.json
# Add your API keys using vim, nano or any text editor you're compfortable with
vim .env
docker compose -f docker-compose.dev.yml build
docker compose -f docker-compose.dev.yml up -d
# Edit the default config options (optional)
./dreamctl config
```

The app will be available at [http://localhost:5000](http://localhost:5000) (unless you choose to change the default port in the config)

To simulate sensor button presses, you can either use the on-screen developer console (available when running in dev mode), or:
   - Note: You will need Python 3.12 installed on your system - [Python documentation](https://wiki.python.org/moin/BeginnersGuide/Download)

   ```bash
   python gpio_service.py --test
   ```

<details>
   <summary>See step-by-step images 🖼️</summary>

   |<a href="./docs/images/debug_tools_1.jpg"><img style="display: block; width: 450px;" src="./docs/images/debug_tools_1.jpg"/></a>|<a href="./docs/images/gpio_service_1.jpg"><img style="display: block; width: 450px;" src="./docs/images/gpio_service_1.jpg"/></a>|
   |--|--|
</details>

#### Running unit tests
Run this command to run the tests:
   - `./dreamctl test`
Run this command to run the tests and see overall test coverage:
   - `./dreamctl test-cov`

<details>
   <summary>See step-by-step images 🖼️</summary>

   <a href="./docs/images/unit_tests_1.jpg"><img style="display: block; width: 450px;" src="./docs/images/unit_tests_1.jpg"/></a>
</details>

#### Visual diagrams
To see how the application's architecture and communication works visually, please refer to the Mermaid diagrams:
- 📈 [Application Architecture](./docs/diagrams/application_architecture.mmd)
- 📈 [Conversation flow](./docs/diagrams/conversation_flow.mmd)

## Managing your dreams
You can access the dream management page from your computer by going to http://dreamer:5000/dreams

<details>
   <summary>See step-by-step images 🖼️</summary>

   |<a href="./docs/images/dreams_page_1.jpg"><img style="display: block; width: 450px;" src="./docs/images/dreams_page_1.jpg"/></a>|<a href="./docs/images/dreams_page_2.jpg"><img style="display: block; width: 450px;" src="./docs/images/dreams_page_2.jpg"/></a>|
   |--|--|
</details>

## Troubleshooting
- **Logs:**
  - App logs: `docker compose logs -f`
  - GPIO logs: `./dreamctl gpio-logs` (for on the Dream Recorder)
  - GPIO logs: `tail -f logs/gpio_service.log` (for during development on your local machine if using `python gpio_service.py --test`)
- **Check running services:**
  ```bash
  docker ps
  ps aux | grep gpio_service.py
  ps aux | grep chromium-browser
  ```
- **Stop the services:**
  ```bash
  docker compose down
  systemctl --user stop dream_recorder_gpio.service
  ```
- **Restart the services:**
  ```bash
  docker compose up -d
  systemctl --user start dream_recorder_gpio.service
  ```
## dreamctl: Simple Command Runner

To make working with the Dream Recorder easier, you can use the `dreamctl` script in the project root. This script simplifies running common commands inside the Docker container.

**Usage:**

```bash
./dreamctl <command>
```

**Available commands:**
- `config`      Edit the Dream Recorder configuration
- `test`        Run unit tests
- `test-cov`    Run unit tests with coverage report
- `gpio-logs`   Tail the GPIO service log (logs/gpio_service.log)
- `help`        Show help message

For example:
- `./dreamctl config` will open the configuration editor
- `./dreamctl test` will run the test suite
- `./dreamctl test-cov` will run the test suite with coverage reporting
- `./dreamctl gpio-logs` will tail the GPIO service log (logs/gpio_service.log)

You can extend `dreamctl` to add more commands as needed.

## Wishlist / Roadmap / Todos
If you would like to contribute to the project, here are some areas we would love help / contribution towards:
- Improving on the shopping list:
   - Including better, more local options (globally) that are not Amazon
   - Finding more efficient purchases for larger packaged items, such as the Dupont cables, nylon screwsets, etc...
- Building out support for multiple (by configuration) AI providers:
   - Support for alternative STT and/or prompt generation providers (Claude, Gemini, etc...)
   - Support for alternative video generation providers
- Adding in support for config-based screen-blanking between configurable times

## License
Dream Recorder is licensed under the MIT License. This means you are free to use, modify, and distribute the software, subject to the terms and conditions of the MIT License. For more details, please see the [LICENSE.md](./LICENSE.md) file in the project repository.

## Questions / Issues / Feedback
Open an issue or contact the lead maintainer for help:

<img src="https://github.com/markhinch.png" width="80px;"/><br /><a href="https://github.com/markhinch">@markhinch</a>

