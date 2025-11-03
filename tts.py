import time
from RealtimeTTS import TextToAudioStream
from constants import *
from eleven_engine import ElevenLabsEngine
from modules.api import ELEVENLABS_API_KEY, ELEVENLABS_VOICE_ID

class TTS:
    def __init__(self, signals):
        api_key = ELEVENLABS_API_KEY
        voice_id = ELEVENLABS_VOICE_ID
    
        self.stream = None
        self.signals = signals
        self.API = self.API(self)
        self.enabled = True

        engine = ElevenLabsEngine(
            api_key=api_key,
            voice=voice_id,
        )

        tts_config = {
            'on_audio_stream_start': self.audio_started,
            'on_audio_stream_stop': self.audio_ended,
            'output_device_index': OUTPUT_DEVICE_INDEX,
        }
        self.stream = TextToAudioStream(engine, **tts_config)
        self.signals.tts_ready = True

    def play(self, message):
        if not self.enabled:
            print("[TTS] Ignored (disabled)")
            return

        if not message.strip():
            print("[TTS] Ignored (empty message)")
            return
        print(f"[TTS] Playing: {message[:50]}...")
        self.signals.sio_queue.put(("current_message", message))
        self.stream.feed(message)
        self.stream.play_async()

    def stop(self):
        self.stream.stop()
        self.signals.AI_speaking = False

    def audio_started(self):
        print("[TTS] Audio started")
        self.signals.AI_speaking = True

    def audio_ended(self):
        print("[TTS] Audio ended")
        self.signals.last_message_time = time.time()
        self.signals.AI_speaking = False

    class API:
        def __init__(self, outer):
            self.outer = outer

        def set_TTS_status(self, status):
            self.outer.enabled = status
            if not status:
                self.outer.stop()
            self.outer.signals.sio_queue.put(('TTS_status', status))

        def get_TTS_status(self):
            return self.outer.enabled

        def abort_current(self):
            self.outer.stop()
