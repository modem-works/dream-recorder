import os
from dotenv import load_dotenv
import logging

# Load environment variables from .env file
load_dotenv()

class Config:
    """Application configuration class."""

    # --- Secret Keys (loaded from .env) ---
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    LUMALABS_API_KEY = os.getenv('LUMALABS_API_KEY')

    # --- Logging ---
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()

    # --- Flask Settings ---
    # Development mode can be set via:
    # 1. FLASK_ENV environment variable (preferred)
    # 2. .env file (FLASK_ENV=development)
    # 3. Command line (--reload flag)
    FLASK_ENV = os.getenv('FLASK_ENV', 'production')
    DEBUG = FLASK_ENV == 'development'
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', 5000))

    # --- Audio Settings ---
    AUDIO_CHANNELS = int(os.getenv('AUDIO_CHANNELS', 1))
    AUDIO_SAMPLE_WIDTH = int(os.getenv('AUDIO_SAMPLE_WIDTH', 2)) # Bytes per sample (2 = 16-bit)
    AUDIO_FRAME_RATE = int(os.getenv('AUDIO_FRAME_RATE', 44100)) # Samples per second (Hz)
    RECORDINGS_DIR = os.getenv('RECORDINGS_DIR', 'recordings')

    # --- OpenAI Settings ---
    WHISPER_MODEL = os.getenv('WHISPER_MODEL', 'whisper-1')
    GPT_MODEL = os.getenv('GPT_MODEL', 'gpt-4o-mini') # Adjusted to a newer mini model
    GPT_SYSTEM_PROMPT = os.getenv(
        'GPT_SYSTEM_PROMPT',
        """You are a creative video prompt engineer.
Your task is to transform dream descriptions into detailed, cinematic video prompts.
Focus on visual elements, atmosphere, and emotional tone.
Keep the prompt concise but rich in visual detail.
Format the response as a single paragraph."""
    )
    GPT_TEMPERATURE = float(os.getenv('GPT_TEMPERATURE', 0.7))
    GPT_MAX_TOKENS = int(os.getenv('GPT_MAX_TOKENS', 200))

    # --- Luma Labs Settings ---
    LUMA_API_URL = os.getenv('LUMA_API_URL', 'https://api.lumalabs.ai/dream-machine/v1')
    LUMA_GENERATIONS_ENDPOINT = f"{LUMA_API_URL}/generations"
    LUMA_MODEL = os.getenv('LUMA_MODEL', 'ray-flash-2')
    LUMA_RESOLUTION = os.getenv('LUMA_RESOLUTION', '540p')
    LUMA_DURATION = os.getenv('LUMA_DURATION', '5s')
    LUMA_ASPECT_RATIO = os.getenv('LUMA_ASPECT_RATIO', '21:9')
    LUMA_POLL_INTERVAL = int(os.getenv('LUMA_POLL_INTERVAL', 5)) # seconds
    LUMA_MAX_POLL_ATTEMPTS = int(os.getenv('LUMA_MAX_POLL_ATTEMPTS', 60))
    VIDEOS_DIR = os.getenv('VIDEOS_DIR', 'videos')

    # --- GPIO Service Settings ---
    GPIO_PIN = int(os.getenv('GPIO_PIN', 4))
    GPIO_FLASK_URL = os.getenv('GPIO_FLASK_URL', f'http://localhost:{PORT}') # Use configured port
    GPIO_SINGLE_TAP_ENDPOINT = os.getenv('GPIO_SINGLE_TAP_ENDPOINT', '/api/wake_device')
    GPIO_DOUBLE_TAP_ENDPOINT = os.getenv('GPIO_DOUBLE_TAP_ENDPOINT', '/api/show_previous_dream')
    GPIO_LONG_PRESS_ENDPOINT = os.getenv('GPIO_LONG_PRESS_ENDPOINT', '/api/trigger_recording')
    GPIO_LONG_PRESS_RELEASE_ENDPOINT = os.getenv('GPIO_LONG_PRESS_RELEASE_ENDPOINT', '/api/stop_recording')
    GPIO_SINGLE_TAP_MAX_DURATION = float(os.getenv('GPIO_SINGLE_TAP_MAX_DURATION', 0.5))
    GPIO_DOUBLE_TAP_MAX_INTERVAL = float(os.getenv('GPIO_DOUBLE_TAP_MAX_INTERVAL', 0.7))
    GPIO_LONG_PRESS_MIN_DURATION = float(os.getenv('GPIO_LONG_PRESS_MIN_DURATION', 1.5))
    GPIO_DEBOUNCE_TIME = float(os.getenv('GPIO_DEBOUNCE_TIME', 0.05))
    GPIO_STARTUP_DELAY = int(os.getenv('GPIO_STARTUP_DELAY', 2))
    GPIO_SAMPLING_RATE = float(os.getenv('GPIO_SAMPLING_RATE', 0.01))

# Validate essential API keys
config_instance = Config()
if not config_instance.OPENAI_API_KEY:
    print("Warning: OPENAI_API_KEY is not set in the environment.", file=sys.stderr)
if not config_instance.LUMALABS_API_KEY:
    print("Warning: LUMALABS_API_KEY is not set in the environment.", file=sys.stderr) 