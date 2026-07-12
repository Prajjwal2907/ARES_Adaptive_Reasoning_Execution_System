import websocket
import json
import threading
import time

_ws = None
_connected = False
_command_callback = None
_memory_request_callback = None
_memory_action_callback = None

def on_command(callback):
    global _command_callback
    _command_callback = callback

def on_memory_request(callback):
    global _memory_request_callback
    _memory_request_callback = callback

def on_memory_action(callback):
    global _memory_action_callback
    _memory_action_callback = callback

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

def send_memory_data(data):
    global _ws, _connected
    if _connected and _ws:
        try:
            _ws.send(json.dumps({"type": "memory-data", "value": data}))
        except Exception:
            _connected = False

def _listen_loop():
    global _ws, _connected
    while True:
        try:
            _ws = websocket.WebSocket()
            _ws.connect("ws://localhost:8765")
            _ws.settimeout(1.0)
            _connected = True
            print("UI bridge connected")

            while True:
                try:
                    message = _ws.recv()
                    if message:
                        data = json.loads(message)
                        if data['type'] == 'command' and _command_callback:
                            _command_callback(data['value'])
                        elif data['type'] == 'get-memory' and _memory_request_callback:
                            _memory_request_callback()
                        elif data['type'] == 'memory-action' and _memory_action_callback:
                            _memory_action_callback(data['action'], data['payload'])
                except websocket.WebSocketTimeoutException:
                    continue
                except Exception:
                    break

        except Exception:
            _connected = False
            print("UI bridge disconnected, retrying in 3 seconds...")
            time.sleep(3)

def wait_until_connected(timeout=30):
    start = time.time()
    while not _connected:
        if time.time() - start > timeout:
            print("UI not connected after 30 seconds, continuing anyway...")
            return
        time.sleep(0.2)
    print("UI ready.")

def init():
    thread = threading.Thread(target=_listen_loop, daemon=True)
    thread.start()