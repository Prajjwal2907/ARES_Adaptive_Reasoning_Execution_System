import os

#Audio 
WHISPER_SAMPLE_RATE = 16000
WHISPER_CHUNK_SIZE = 512
COOLDOWN_OF_AUDIO = 3
CONV_COOLDOWN = 30

#Openai Whisper 
WHISPER_MODEL = "small"
LANGUAGE = "en"

# Wakeword
WAKEWORD_SAMPLE_RATE = 16000
WAKEWORD_CHUNK_SIZE = 1280
WAKEWORD_MODEL = r"ARES\assets\ares.onnx"
SENSITIVITY = 0.4

# Google api model
GEMINI_MODEL = "gemini-2.5-flash"
#Hotkeys
HOTKEY = "ctrl + space"

#VAD
SILENCE_SENSITIVITY = 0.1
VAD_CHUNK_SIZE = 512

#paths
current_dir = os.path.dirname(__file__)
HIST_JSON = os.path.join(current_dir, "data", "memory", "history.json")
SYSTEM_PROMPT_FILE = os.path.join(current_dir, "assets", "prompts", "system_prompt.txt")
MEMORY_EXTRACT_PROMPT = os.path.join(current_dir, "assets", "prompts", "memory_extract_prompt.txt")
SQLITE_DB = os.path.join(current_dir,'data','memory','ares_memory.db')
CHROMA_DIR = os.path.join(current_dir,'data','memory','chroma')
ACTION_DB = os.path.join(current_dir,'data','memory','action_log.db')