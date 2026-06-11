import os
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(__file__), '.env')

if not os.path.exists(env_path):
    print("No .env file found. First time setup.")
    api_key = input("Enter your Google API key: ")
    with open(env_path, 'w') as f:
        f.write(f"GOOGLE_API_KEY={api_key}")
    print(".env file created successfully.")

load_dotenv()

from core import brain
from core import memory
from core import listener

listener.listen(listener.aud_stream)