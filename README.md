# Dream Recorder

A Raspberry Pi-based device that records your dreams and converts them into videos using AI.

## Overview

Dream Recorder is an interactive device that uses a Raspberry Pi 5, a touch sensor, and a microphone to record and visualize dreams. The user interacts with the device through a capacitive touch sensor, records their dream description, and the system processes this audio to generate a creative visualization using AI.

### Features

- **Simple Physical Interface**: Single touch button (TTP223B capacitive touch sensor) to start/stop recording
- **Voice Recording**: Records user's dream description via USB microphone
- **AI Processing**:
  - Converts speech to text using OpenAI's API
  - Enhances the dream description into a video prompt
  - Generates a video using LumaLabs API
- **Video Post-Processing**: Uses FFmpeg to enhance/customize the generated video
- **Video Playback**: Displays the final video on the attached screen

## Hardware Requirements

- Raspberry Pi 5
- Display screen (HDMI connected)
- TTP223B capacitive touch sensor (connected to GPIO pins)
- USB microphone
- Stable internet connection

## Software Requirements

- Python 3.10+ (Python 3.12 compatibility added)
- Node.js and npm
- FFmpeg

> **Note for Python 3.12 Users**: This application has been updated to work with Python 3.12 by replacing eventlet with gevent for WebSocket support. The setup script will automatically detect your Python version and install the appropriate dependencies.
>
> If you encounter an "externally-managed-environment" error, run the `scripts/fix_python312.sh` script to apply compatibility fixes:
> ```bash
> ./scripts/fix_python312.sh
> ```

## Software Architecture

The application consists of:

1. **Backend (Python/Flask)**:
   - Web server for serving the frontend
   - WebSocket server for real-time audio streaming
   - GPIO controller for touch sensor integration
   - API clients for OpenAI and LumaLabs
   - FFmpeg integration for video post-processing

2. **Frontend (HTML/JS/CSS)**:
   - Web interface for user interaction
   - Audio recording and streaming
   - Video playback

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/dream-recorder.git
cd dream-recorder
```

### 2. Run the setup script

```bash
./setup.sh
```

This will install all required dependencies, including:
- Python packages
- Node.js and npm packages (for frontend development)
- FFmpeg

### 3. Configure API Keys

Create a `.env` file in the project root with your API keys:

```
OPENAI_API_KEY=your_openai_api_key
LUMALABS_API_KEY=your_lumalabs_api_key
```

## Running the Application

### On a Raspberry Pi

```bash
./run.sh
```

This will start the Flask server and open the web interface.

### On a Non-Raspberry Pi Device (Test Mode)

For development or testing purposes, you can run the application on any computer:

```bash
./scripts/test_run.sh
```

This runs the application in test mode with:
- GPIO functionality disabled (manual controls only)
- Sample data for testing when hardware is unavailable
- Debug mode enabled for easier development

## Usage Flow

1. Touch the sensor to start recording
2. Describe your dream
3. Touch the sensor again to stop recording
4. Wait while the system processes your dream
5. View the generated visualization of your dream
6. The system will automatically reset for the next dream recording

## Project Structure

- `/backend` - Python Flask server and API clients
- `/frontend` - HTML/JS/CSS files for the web interface
- `/scripts` - Utility scripts for installation and configuration
- `/config` - Configuration files

## Development

### Running in Development Mode

```bash
./dev.sh
```

This will start the application with hot-reloading enabled.

## License

[MIT License](LICENSE)