import os

#Listener
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
GEMINI_MODEL = "gemini-3.1-flash-lite-preview"
# GEMINI_MODEL = "gemini-2.5-flash"

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

# Speaker
REFERENCE_AUDIO_PATH = os.path.join(current_dir, "assets", "sounds", "ares_voice.wav")
TTS_MODEL_PATH = os.path.join(current_dir, "assets", "qwen", "Qwen3-TTS-12Hz-1.7B-Base")
TTS_REFERENCE_TEXT = (
    "Good evening, sir. I've reviewed the system logs while you were away, "
    "and everything appears to be running exactly as it should — though I "
    "did notice the workspace folder could use a bit of tidying when you "
    "have a moment."
)