import requests
import traceback
import pyaudio
from queue import Queue
from pydub import AudioSegment
from io import BytesIO
from modules.api import ELEVENLABS_MODEL, ELEVENLABS_BASE_URL

class ElevenLabsEngine:
    def __init__(self, api_key, voice="Sarah", model=ELEVENLABS_MODEL, speed=1.0):
        self.api_key = api_key
        self.engine_name = "ElevenLabs"
        self.voice = voice
        self.model = model
        self.speed = speed
        self.queue = Queue()
        self.timings = Queue()
        self.can_consume_generators = False

    def text_to_audio(self, text: str) -> bytes:
        url = f"{ELEVENLABS_BASE_URL}/{self.voice}"
        headers = {
            "xi-api-key": self.api_key,
            "Content-Type": "application/json"
        }
        payload = {
            "text": text,
            "model_id": self.model,
            "voice_settings": {
                "stability": 0.9,
                "similarity_boost": 0.3,
                "style": 0.1,
                "use_speaker_boost": False
            }
        }

        response = requests.post(url, headers=headers, json=payload)
        if response.status_code != 200:
            raise Exception(f"⚠️ ElevenLabs Error: {response.status_code} - {response.text}")
        mp3_audio = BytesIO(response.content)
        sound = AudioSegment.from_file(mp3_audio, format="mp3")
        wav_io = BytesIO()
        sound.export(wav_io, format="wav")
        return wav_io.getvalue()

    def get_stream_info(self):
        return pyaudio.paInt16, 1, 44100   

    def reset_audio_duration(self):
    # RealtimeTTS gọi hàm này mỗi lần phát xong âm thanh
    # Với ElevenLabs, không cần làm gì nên để rỗng
        pass

    def synthesize(self, text: str) -> bool:
        try:
            audio = self.text_to_audio(text)
            self.queue.put(audio)
            return True
        except Exception as e:
            print("🔥 Synthesize error:", e)
            traceback.print_exc()
            return False