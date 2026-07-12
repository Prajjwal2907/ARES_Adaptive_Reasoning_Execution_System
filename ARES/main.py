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
        ui_bridge.send_state('listening')
    ui_bridge.send_state('standby')

ui_bridge.on_command(lambda text: threading.Thread(
    target=handle_text_command, args=(text,), daemon=True
).start())
def handle_memory_request():
    from core import memory

    if memory.semantic_memory_coll is None or memory.procedural_memory_coll is None:
        ui_bridge.send_memory_data({
            "profile": {},
            "instructions": [],
            "episodes": [],
            "semantic": [],
            "procedural": []
        })
        return

    # profile
    profile = memory.get_profile()

    # instructions
    cur = memory.conn.cursor()
    cur.execute("SELECT id, instruction FROM instructions WHERE valid = 1")
    instructions = [{"id": row[0], "text": row[1]} for row in cur.fetchall()]

    # episodic summaries
    cur.execute("SELECT id, date_time, conversation FROM episodic_memory ORDER BY date_time DESC LIMIT 10")
    episodes = [{"id": row[0], "date": row[1], "summary": row[2]} for row in cur.fetchall()]

    # semantic memories
    sem_count = memory.semantic_memory_coll.count()
    semantic = []
    if sem_count > 0:
        results = memory.semantic_memory_coll.get(include=["documents", "metadatas", "ids"])
        for i in range(len(results['ids'])):
            semantic.append({
                "id": results['ids'][i],
                "text": results['documents'][i],
                "metadata": results['metadatas'][i]
            })

    # procedural memories
    proc_count = memory.procedural_memory_coll.count()
    procedural = []
    if proc_count > 0:
        results = memory.procedural_memory_coll.get(include=["documents", "metadatas", "ids"])
        for i in range(len(results['ids'])):
            procedural.append({
                "id": results['ids'][i],
                "text": results['documents'][i],
                "metadata": results['metadatas'][i]
            })

    ui_bridge.send_memory_data({
        "profile": profile,
        "instructions": instructions,
        "episodes": episodes,
        "semantic": semantic,
        "procedural": procedural
    })

def handle_memory_action(action, payload):
    from core import memory
    
    if action == 'delete-semantic':
        memory.semantic_memory_coll.delete(ids=[payload['id']])
        
    elif action == 'delete-procedural':
        memory.procedural_memory_coll.delete(ids=[payload['id']])
        
    elif action == 'revoke-instruction':
        cur = memory.conn.cursor()
        cur.execute("UPDATE instructions SET valid = 0 WHERE id = ?", (payload['id'],))
        memory.conn.commit()
        
    elif action == 'add-instruction':
        memory.store_instruction(payload['text'])
        
    elif action == 'update-profile':
        memory.update_profile(payload['field'], payload['val'])

    # send updated memory data back
    handle_memory_request()

ui_bridge.on_memory_request(
    lambda: threading.Thread(target=handle_memory_request, daemon=True).start()
)
ui_bridge.on_memory_action(
    lambda action, payload: threading.Thread(
        target=handle_memory_action, args=(action, payload), daemon=True
    ).start()
)
from core import brain
from core import listener

listener.listen(listener.aud_stream)