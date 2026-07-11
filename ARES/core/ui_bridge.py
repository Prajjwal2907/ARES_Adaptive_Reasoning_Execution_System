import websocket
import json
import threading
import time

_ws = None
_connected = False
_command_callback = None

def on_command(callback):
    global _command_callback
    _command_callback = callback
    
def _connect():
    global _ws, _connected

    while True:
        try:
            _ws = websocket.WebSocket()
            _ws.connect("ws://localhost:8765")
            _connected = True
            print("UI bridge connected")

            while True:
                try:
                    message = _ws.recv()
                    if message:
                        data = json.loads(message)
                        if data['type'] == 'command' and _command_callback:
                            _command_callback(data['value'])
                except:
                    break

        except Exception as e:
            _connected = False
            print(f"UI bridge disconnected, retrying in 3 seconds...")
            time.sleep(3)

def init():
    thread = threading.Thread(target=_connect, daemon=True)
    thread.start()

def wait_until_connected(timeout=30):
    import time
    start = time.time()
    while not _connected:
        if time.time() - start > timeout:
            print("UI not connected after 30 seconds, continuing anyway...")
            return
        time.sleep(0.2)
    print("UI ready.")

def send_state(state):
    global _ws, _connected
    if _connected and _ws:
        try:
            _ws.send(json.dumps({"type": "state", "value": state}))
        except Exception:
            _connected = False

def send_response(text):
    global _ws, _connected
    if _connected and _ws:
        try:
            _ws.send(json.dumps({"type": "response", "value": text}))
        except Exception:
            _connected = False