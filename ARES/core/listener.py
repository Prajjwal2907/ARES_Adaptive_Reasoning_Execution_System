# Importing modules
import whisper
import openwakeword
import torch
import pyaudio
import numpy as np
import config
from openwakeword.model import Model
import time
import threading
from collections import deque
from . import brain

# Initialising models
whisper_model = whisper.load_model(config.WHISPER_MODEL)
VAD_model, VAD_utils = torch.hub.load(repo_or_dir="snakers4/silero-vad", model = "silero_vad", force_reload=False)
wakeword_model = Model(wakeword_models=[config.WAKEWORD_MODEL], inference_framework="onnx")

#starting stream
pyAud = pyaudio.PyAudio()
aud_stream = pyAud.open(format = pyaudio.paInt16, channels = 1, input=True, rate=config.WHISPER_SAMPLE_RATE, frames_per_buffer=config.WHISPER_CHUNK_SIZE)

# WakeWord "ARES" detection thread
def listen(audio_stream): 
    print("Listening....")
    while True:
        # reads audio from stream and checks for wake word "Ares"
        aud_bytes = audio_stream.read(config.WAKEWORD_CHUNK_SIZE, exception_on_overflow=False)
        aud_array = np.frombuffer(aud_bytes, dtype=np.int16) 
        speech_prob = wakeword_model.predict(aud_array)
        
        if speech_prob['ares'] > config.SENSITIVITY:  
                print("Ares activated!")  
                wakeword_model.reset()
                
                conv_silence_duration = time.time()
                chunk_duration = config.WHISPER_CHUNK_SIZE / config.WHISPER_SAMPLE_RATE

                # keeps ares activated for longer time without going completely passive
                while (time.time() - conv_silence_duration) < config.CONV_COOLDOWN:
                    command_buffer = []
                    silence_duration = 0
                    speech_detected = False
                    while True:
                        # Reads audio and converts into all required forms
                        aud_bytes = audio_stream.read(config.WHISPER_CHUNK_SIZE, exception_on_overflow=False)
                        aud_array = np.frombuffer(aud_bytes, dtype=np.int16) 
                        aud_array_normalised = (aud_array/32768.0).astype(np.float32)
                        aud_array_tensor = torch.tensor(aud_array_normalised, dtype=torch.float32)

                        # creates the complete command
                        command_buffer.append(aud_array_normalised)

                        # checks for actual speech
                        speech_prob = VAD_model(aud_array_tensor, config.WHISPER_SAMPLE_RATE)
                        # updates silence duration if no speech detected
                        if speech_prob < config.SILENCE_SENSITIVITY:
                            silence_duration += chunk_duration
                        else: 
                            silence_duration = 0
                            speech_detected = True
                        # Starts transcription if longer than pause silence is recorded
                        if silence_duration > config.COOLDOWN_OF_AUDIO:
                            break 
                    # gets full command and transcribes
                    full_audio = np.concatenate(command_buffer)
                    if speech_detected:
                        transcribed_audio =  whisper_model.transcribe(full_audio, language = config.LANGUAGE)

                        # gets response from brain
                        resp = brain.get_response(transcribed_audio["text"])

                        # prints response if ignore was not returned
                        if resp:
                            print(resp)
                    
                        # resets active listening timer if speech was detected
                    
                        conv_silence_duration = time.time()

                    print("Listening....")
                print("Returning to passive listening....")
try:
    while True: 
        listen(aud_stream)
except KeyboardInterrupt:
    print("exiting")