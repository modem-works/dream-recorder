import os
import sys
import openai

def check_openai_api_key(api_key):
    client = openai.OpenAI(api_key=api_key)
    try:
        client.models.list()
    except openai.AuthenticationError:
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False
    else:
        return True

if __name__ == "__main__":
    api_key = None
    if len(sys.argv) > 1:
        api_key = sys.argv[1]
    else:
        api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("Usage: python test_openai_key.py <OPENAI_API_KEY> or set OPENAI_API_KEY env var.")
        sys.exit(1)
    if check_openai_api_key(api_key):
        print("Valid OpenAI API key.")
    else:
        print("Invalid OpenAI API key.") 