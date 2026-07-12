import os
import uuid
import sqlite3
import chromadb
import config
import datetime
from sentence_transformers import SentenceTransformer

os.makedirs(config.CHROMA_DIR, exist_ok=True)

conn = sqlite3.connect(config.SQLITE_DB, check_same_thread=False)
chroma_client = chromadb.PersistentClient(path = config.CHROMA_DIR)
sentence_transformer_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

semantic_memory_coll = None
procedural_memory_coll = None

gemini_client = None
def init_memory(client):
    global gemini_client
    gemini_client = client
    cur = conn.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS profile(
                field TEXT PRIMARY KEY,
                val TEXT 
                )''')
    cur.execute('''CREATE TABLE IF NOT EXISTS episodic_memory(
                id INTEGER PRIMARY KEY,
                date_time TEXT,
                conversation TEXT,
                conv_turns INTEGER
                )''')
    cur.execute('''CREATE TABLE IF NOT EXISTS instructions(
                id INTEGER PRIMARY KEY,
                date_passed TEXT,
                instruction TEXT,
                valid INTEGER CHECK(valid IN(0,1))
                )''')
    

    cur.execute('''INSERT OR IGNORE INTO profile(field, val) VALUES
                ('name', ''),
                ('address_as', 'sir')''')
    
    conn.commit()

    global semantic_memory_coll, procedural_memory_coll
    semantic_memory_coll = chroma_client.get_or_create_collection("semantic_memory")
    procedural_memory_coll = chroma_client.get_or_create_collection("procedural_memory")


def update_profile(field, val):
    cur = conn.cursor()
    cur.execute("INSERT INTO profile(field, val) VALUES (?, ?) ON CONFLICT(field) DO UPDATE SET val = excluded.val", (field, val))
    conn.commit()

def store_instruction(instruction):
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM instructions WHERE instruction = ? AND valid = 1", (instruction,))
    count = cur.fetchone()[0]
    if not count:
        cur.execute("INSERT INTO instructions(date_passed, instruction, valid) VALUES (?, ?, ?)", (datetime.datetime.now().isoformat(), instruction, 1))
        conn.commit()

def store_episode(summary,turncount):
    cur = conn.cursor()
    cur.execute("INSERT INTO episodic_memory(date_time, conversation, conv_turns) VALUES(?, ?, ?)", (datetime.datetime.now().isoformat(), summary, turncount))
    conn.commit()

def store_semantic(text, metadata):
    encoded_text = sentence_transformer_model.encode(text).tolist()
    
    if semantic_memory_coll.count() > 0:
        similar = semantic_memory_coll.query(
            query_embeddings=[encoded_text],
            n_results=1
        )
        
        existing_text = similar['documents'][0][0]
        existing_distance = similar['distances'][0][0]
        existing_id = similar['ids'][0][0]
        
        if existing_distance < 0.10:
            if check_contradiction(text, existing_text):
                temporal_qualifiers = ['today', 'this week', 'for now', 'temporarily', 'right now', 'at the moment']
                is_temporary = any(qualifier in text.lower() for qualifier in temporal_qualifiers)
                
                if is_temporary:
                    metadata['memory_type'] = 'temporary'
                else:
                    semantic_memory_coll.delete(ids=[existing_id])
                semantic_memory_coll.add(documents = [text], metadatas = [metadata], embeddings = [encoded_text], ids = [str(uuid.uuid4())])
        elif existing_distance < 0.25:
            semantic_memory_coll.delete(ids=[existing_id])
            semantic_memory_coll.add(documents = [text], metadatas = [metadata], embeddings = [encoded_text], ids = [str(uuid.uuid4())])
        else:
            semantic_memory_coll.add(documents = [text], metadatas = [metadata], embeddings = [encoded_text], ids = [str(uuid.uuid4())])
    else:
            semantic_memory_coll.add(documents = [text], metadatas = [metadata], embeddings = [encoded_text], ids = [str(uuid.uuid4())])

def store_procedural(text, metadata):
    encoded_text = sentence_transformer_model.encode(text).tolist()
    
    if procedural_memory_coll.count() > 0:
        similar = procedural_memory_coll.query(
            query_embeddings=[encoded_text],
            n_results=1
        )
        
        existing_text = similar['documents'][0][0]
        existing_distance = similar['distances'][0][0]
        existing_id = similar['ids'][0][0]
        
        if existing_distance < 0.10:
            if check_contradiction(text, existing_text):
                temporal_qualifiers = ['today', 'this week', 'for now', 'temporarily', 'right now', 'at the moment']
                is_temporary = any(qualifier in text.lower() for qualifier in temporal_qualifiers)
                
                if is_temporary:
                    metadata['memory_type'] = 'temporary'
                else:
                    procedural_memory_coll.delete(ids=[existing_id])
                procedural_memory_coll.add(documents = [text], metadatas = [metadata], embeddings = [encoded_text], ids = [str(uuid.uuid4())])
        elif existing_distance < 0.25:
            procedural_memory_coll.delete(ids=[existing_id])
            procedural_memory_coll.add(documents = [text], metadatas = [metadata], embeddings = [encoded_text], ids = [str(uuid.uuid4())])
        else:
            procedural_memory_coll.add(documents = [text], metadatas = [metadata], embeddings = [encoded_text], ids = [str(uuid.uuid4())])
    else:
            procedural_memory_coll.add(documents = [text], metadatas = [metadata], embeddings = [encoded_text], ids = [str(uuid.uuid4())])

def get_profile():
    profile = {}
    cur = conn.cursor()
    cur.execute("SELECT * FROM profile")
    profile_data = cur.fetchall()
    for data in profile_data:
        profile[data[0]] = data[1]

    return profile

def get_instructions():
    instructions = []
    cur = conn.cursor()
    cur.execute("SELECT * FROM instructions WHERE valid = 1")
    inst_data = cur.fetchall()
    for data in inst_data:
        instructions.append(data[2])

    return instructions

def get_recent_episodes(n):
    episodes = []
    cur = conn.cursor()
    cur.execute("SELECT * FROM episodic_memory ORDER BY date_time DESC LIMIT ?", (n,))
    memories = cur.fetchall()
    for memory in memories:
        episodes.append((memory[1], memory[2]))

    return episodes

def retrieve_memories(query, n_results, recent_context = ""):
    query_encoded = sentence_transformer_model.encode(query).tolist()
    memories = []

    semantic_c = semantic_memory_coll.count()
    if semantic_c:
        n_sem = min(n_results, semantic_c)
        semantic = semantic_memory_coll.query(query_embeddings = [query_encoded], n_results = n_sem)
        documents_sem = semantic['documents'][0]
        metadatas_sem = semantic['metadatas'][0]
        distances_sem = semantic['distances'][0]
        
        for i in range(len(documents_sem)):
            doc = documents_sem[i]
            meta = metadatas_sem[i]
            dist = distances_sem[i]
            memories.append((doc, meta, dist))
    
    procedural_c = procedural_memory_coll.count()
    if procedural_c:
        n_proc = min(n_results, procedural_c)
        procedural = procedural_memory_coll.query(query_embeddings = [query_encoded], n_results = n_proc)
        documents_proc = procedural['documents'][0]
        metadatas_proc = procedural['metadatas'][0]
        distances_proc = procedural['distances'][0]

        for i in range(len(documents_proc)):
            doc = documents_proc[i]
            meta = metadatas_proc[i]
            dist = distances_proc[i]
            memories.append((doc, meta, dist))
    

    scored_memories = []
    for memory in memories:

        semantic_score = (1 - memory[2]) * 0.35

        recency = ((datetime.datetime.now() - datetime.datetime.fromisoformat(memory[1]['timestamp']).replace(tzinfo=None)).days)
        
        if recency < 1:
            recency_score = 1 * 0.3

        elif 1 <= recency < 7:
            recency_score = 0.85 * 0.3

        elif 7 <= recency < 30:
            recency_score = 0.65 * 0.3

        elif 30 <= recency < 90:
            recency_score = 0.45 * 0.3

        elif 90 <= recency < 180:
            recency_score = 0.30 * 0.3

        elif 180 <= recency:
            recency_score = 0.15 * 0.3

        importance_score = memory[1]['importance'] / 10 * 0.2

        continuity_score = 0
        if recent_context:
            tags = memory[1]['tags'].split(',')
            for tag in tags:
                if tag.strip() in recent_context.lower():
                    continuity_score = 0.15
                    break
        total_score = semantic_score + recency_score + importance_score + continuity_score

        new_memory = memory + (total_score,)
        scored_memories.append(new_memory)
    
    scored_memories = sorted(scored_memories, key=lambda x: x[3], reverse=True)
    return scored_memories[:n_results]
    

def check_contradiction(new_text, existing_text):
    prompt = f"Do the two given texts:\n Text 1:{new_text}\nText 2: {existing_text}\n contradict each other. Answer in a single word as \'yes\' or \'no\'. Do not include anything else in your response. No explanation, no extra words. Only Yes or No"
    response = gemini_client.models.generate_content(model=config.GEMINI_MODEL,
                                                    contents = prompt
                                                    )
    
    if response.text.strip().lower() == "yes":
        return True
    else:
        return False