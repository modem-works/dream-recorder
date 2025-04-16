import os
import sys
from dotenv import load_dotenv

def check_required_env_vars():
    """Check if all required environment variables are set."""
    # Load environment variables
    load_dotenv()
    
    # Read .env.example to get all required variables
    required_vars = set()
    with open('.env.example', 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                var_name = line.split('=')[0].strip()
                required_vars.add(var_name)
    
    # Check which required variables are missing
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print("Error: The following required environment variables are not set in your .env file:", file=sys.stderr)
        for var in missing_vars:
            print(f"  - {var}", file=sys.stderr)
        print("\nPlease copy .env.example to .env and set all required values.", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    check_required_env_vars() 