import os
import json
from dotenv import load_dotenv

def load_config():
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
    return config 