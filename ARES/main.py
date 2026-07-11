# from core import brain
# from core import ui_bridge
# ui_bridge.init()

# while True:
#     prompt = input("You: ")
#     if prompt.lower() == "exit":
#         break
#     response = brain.get_response(prompt)
#     if response:
#         print("ARES:", response)

import os
import time
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(__file__), '.env')

if not os.path.exists(env_path):
    print("No .env file found. First time setup.")
    api_key = input("Enter your Google API key: ")
    with open(env_path, 'w') as f:
        f.write(f"GOOGLE_API_KEY={api_key}")
    print(".env file created successfully.")

load_dotenv()

from core import ui_bridge
ui_bridge.init()
ui_bridge.wait_until_connected()

import threading

def handle_text_command(text):
    print(f"Text command: {text}")
    ui_bridge.send_state('processing')
    resp = brain.get_response(text)
    if resp:
        ui_bridge.send_state('speaking')
        ui_bridge.send_response(resp)
        from utils import audio
        audio.speak(resp)
        audio.flush()
    ui_bridge.send_state('standby')

ui_bridge.on_command(lambda text: threading.Thread(
    target=handle_text_command, args=(text,), daemon=True
).start())

from core import brain
from core import listener

listener.listen(listener.aud_stream)