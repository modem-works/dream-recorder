import os
import sys
import requests

def check_luma_api_key(api_key):
    url = "https://api.lumalabs.ai/dream-machine/v1/credits"
    headers = {"Authorization": f"Bearer {api_key}"}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 401:
            return False
        elif response.status_code == 200:
            return True
        else:
            print(f"Unexpected response: {response.status_code} {response.text}")
            return False
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":  # pragma: no cover
    api_key = None
    if len(sys.argv) > 1:
        api_key = sys.argv[1]
    else:
        api_key = os.environ.get("LUMALABS_API_KEY")
    if not api_key:
        print("Usage: python test_luma_key.py <LUMALABS_API_KEY> or set LUMALABS_API_KEY env var.")
        sys.exit(1)
    if check_luma_api_key(api_key):
        print("Valid Luma Labs API key.")
    else:
        print("Invalid Luma Labs API key.")
