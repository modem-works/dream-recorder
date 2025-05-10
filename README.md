# Dream Recorder

## Getting started

### To get the Dream Recorder up and running on your Raspberry Pi

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

   |<img style="display: block; width: 450px;" src="./docs/images/rpi_imager_1.png"/>|<img style="display: block; width: 450px;" src="./docs/images/rpi_imager_2.png"/>|
   |--|--|
   |<img style="display: block; width: 450px;" src="./docs/images/rpi_imager_3.png"/>|<img style="display: block; width: 450px;" src="./docs/images/rpi_imager_4.png"/>|
   |<img style="display: block; width: 450px;" src="./docs/images/rpi_imager_5.png"/>|<img style="display: block; width: 450px;" src="./docs/images/rpi_imager_6.png"/>|
   |<img style="display: block; width: 450px;" src="./docs/images/rpi_imager_7.png"/>|<img style="display: block; width: 450px;" src="./docs/images/rpi_imager_8.png"/>|
   |<img style="display: block; width: 450px;" src="./docs/images/rpi_imager_9.png"/>|<img style="display: block; width: 450px;" src="./docs/images/rpi_imager_10.png"/>|
   |<img style="display: block; width: 450px;" src="./docs/images/rpi_imager_11.png"/>|<img style="display: block; width: 450px;" src="./docs/images/rpi_imager_12.png"/>|
</details>

#### 🍓 <u>On the Raspberry Pi</u>
- Insert the microSD card into the Raspberry Pi
- Plug the Raspberry Pi in using the power supply and wait for it to boot up

#### 💻️ <u>On your computer (in a Terminal window)</u>

- Open up a terminal / command line / bash window
- SSH into the Dream Recorder with the following command, using the simple password you created in the Raspberry Pi imager:
   - `ssh dreamer@dreamer`
- Run the Raspberry Pi config tool by running this command:
   - `sudo raspi-config`
   - Interface Options -> VNC -> Yes -> OK
   - Localisation Options -> Configure time zone -> Choose your country & city
   - Select \<Finish\>
- Keep this terminal window open for later   

<details>
   <summary>See step-by-step images 🖼️</summary>

   |<img style="display: block; width: 450px;" src="./docs/images/raspi_config_1.png"/>|<img style="display: block; width: 450px;" src="./docs/images/raspi_config_2.png"/>|
   |--|--|
   |<img style="display: block; width: 450px;" src="./docs/images/raspi_config_3.png"/>|<img style="display: block; width: 450px;" src="./docs/images/raspi_config_4.png"/>|
   |<img style="display: block; width: 450px;" src="./docs/images/raspi_config_5.png"/>|<img style="display: block; width: 450px;" src="./docs/images/raspi_config_6.png"/>|
</details>

#### 💻️ <u>On your computer</u>

- [Download RealVNC](https://www.realvnc.com/en/connect/download), install and run it
   - Connect to the Dream Recorder's IP address using the username (dreamer) and your simple password
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

   |<img style="display: block; width: 250px;" src="./docs/images/vnc_viewer_1.png"/>|<img style="display: block; width: 250px;" src="./docs/images/vnc_viewer_2.png"/>|<img style="display: block; width: 250px;" src="./docs/images/vnc_viewer_3.png"/>|
   |--|--|--|

   <img style="display: block; width: 800px;" src="./docs/images/vnc_viewer_4.png"/>

   <img style="display: block; width: 800px;" src="./docs/images/vnc_viewer_5.png"/>

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
- Copy the URL of the Git repository at the top of this Github page by clicking on the blue Code button at the top right and copying the 'SSH' url

#### 💻️ <u>On your computer (in the previously opened Terminal window)</u>
- Make sure you are still connected to the Dream Recorder
   - If not, connect again:
      - `ssh dreamer@dreamer`
- Clone the Dream Recorder from Github using the URL you just copied in the step above
   - `git clone <repo_ssh_url>`
- Once completed, navigate into the repo folder:
   - `cd dream-recorder`
- Run the installer:
   - `./pi_installer.sh`
   - When prompted, paste in each of the API keys you generated above
- Reboot the Raspberry Pi: `sudo reboot`
- You are now up and running once the Pi has rebooted!

#### Adjusting the configuration of the Dream Recorder
- SSH into the Dream Recorder with the following command, using the simple password you created in the Raspberry Pi imager:
   - `ssh dreamer@dreamer`
- Navigate to the Dream Recorder's root folder:
   - `cd dream-recorder`
- Run this command:
   `docker compose exec app python3 scripts/config_editor.py`
- After saving (s) and quitting (q), reload the application by running:
   - `docker compose restart app`


### For Developers (Local/Development)
To get the app running on your local machine:
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

#### Running unit tests
Run this command to run the tests:
   - `docker compose exec app pytest`
Run this command to run the tests and see overall test coverage:
   - `docker compose exec app pytest --cov=. --cov-report=term-missing`

## Using the Dream Recorder
- Single tap: Play the latest dream
   - Single tapping while a dream is playing will play the previous dream
   - Double tapping while a dream is playing will go back to clock mode
- Double tap: Record a dream
   - Single tap once you are done talking for the dream to be generated

## Managing your dreams
You can access the dream management page from your computer by going to http://dreamer:5000/dreams

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
  systemctl --user stop dream_recorder_gpio.service
  ```
- **Restart the services:**
  ```bash
  docker compose up -d
  systemctl --user start dream_recorder_gpio.service
  ```

## Questions?

Open an issue or contact the lead maintainer for help:

<img src="https://github.com/markhinch.png" width="80px;"/><br /><a href="https://github.com/markhinch">@markhinch</a>
