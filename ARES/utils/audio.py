import numpy as np
import sounddevice as sd
import os
import torch
from qwen_tts import Qwen3TTSModel
import config
import queue, threading

print("Loading ARES voice model:")
_clone_model = Qwen3TTSModel.from_pretrained(
    config.TTS_MODEL_PATH,
    device_map="cuda:0",
    dtype=torch.bfloat16,
)

print("Building voice clone prompt...")
_voice_clone_prompt = _clone_model.create_voice_clone_prompt(
    ref_audio=config.REFERENCE_AUDIO_PATH,
    ref_text=config.TTS_REFERENCE_TEXT,
)
print("ARES voice ready.")

_buffer = ""

def _process_buffer(chunk):
    global _buffer
    _buffer += chunk
    complete_sentences = []

    while True:
        earliest_index = -1
        earliest_term = None
        search_from = 0

        while True:

            earliest_index = -1
            earliest_term = None

            for term in (".", "?", "!"):
                index = _buffer.find(term, search_from)
                if index != -1:
                    if earliest_index == -1 or index < earliest_index:
                        earliest_index = index
                        earliest_term = term


            if earliest_index == -1:
                break


            if earliest_term == ".":
                before = _buffer[earliest_index - 1] if earliest_index > 0 else ""
                after = _buffer[earliest_index + 1] if earliest_index + 1 < len(_buffer) else ""
                if before.isnumeric() and after.isnumeric():
        
                    search_from = earliest_index + 1
                    continue


            break

        if earliest_index == -1:
            break

        sentence = _buffer[:earliest_index + 1].strip()
        _buffer = _buffer[earliest_index + 1:]

        if sentence:
            complete_sentences.append(sentence)

    return complete_sentences

def _flush():
    global _buffer
    if _buffer:
        final_sentence = _buffer.strip()
        _buffer = ""
        return [final_sentence]
    
def _generate_audio(sentence):
    if sentence:
        sentence = sentence.replace("ARES", "AIReez")

    wavs, sr = _clone_model.generate_voice_clone(
        sentence,
        language="English",
        voice_clone_prompt=_voice_clone_prompt,
    )

    audio = wavs[0]

    pad = np.zeros(int(sr * 0.8), dtype=audio.dtype)

    audio = np.concatenate([pad, audio, pad])
    
    return audio, sr


def _playback_worker():
    while True:
        item = _audio_queue.get()
        if item is None:
            break
        audio_array, sr = item
        sd.play(audio_array, samplerate=sr)
        sd.wait()
        # sd.play(audio_array, sr, blocking=True)
        _audio_queue.task_done()

def speak(chunk):
    # sentences = _process_buffer(chunk)
    # for sentence in sentences:
    #     audio, sr = _generate_audio(sentence)
    #     _audio_queue.put((audio, sr))
    audio, sr = _generate_audio(chunk)
    _audio_queue.put((audio, sr))

def flush():
    sentences = _flush()
    if sentences:
    #     for sentence in sentences:
    #         audio, sr = _generate_audio(sentence)
    #         _audio_queue.put((audio, sr))
        audio, sr = _generate_audio(sentences)
        _audio_queue.put((audio, sr))

_audio_queue = queue.Queue()
_playback_thread = threading.Thread(target=_playback_worker, daemon=True)
_playback_thread.start()