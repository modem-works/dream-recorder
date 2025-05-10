import os
import json
from dotenv import load_dotenv

_config = None

def load_config():
    global _config
    # Load API keys from .env
    load_dotenv()
    api_keys = {
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
        "LUMALABS_API_KEY": os.getenv("LUMALABS_API_KEY"),
    }

    # Determine which config to load
    config_file = "config.json"

    with open(config_file, "r") as f:
        config = json.load(f)

    # Merge API keys into config
    config.update(api_keys)
    _config = config
    return config

def get_config():
    global _config
    if _config is None:
        return load_config()
    return _config 