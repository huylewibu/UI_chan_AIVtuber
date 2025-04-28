import os
from dotenv import load_dotenv

load_dotenv()

ELEVENLABS_API_KEY = os.getenv("ELEVEN_API_KEY")
ELEVENLABS_VOICE_ID = os.getenv("ELEVEN_VOICE_ID")
ELEVENLABS_MODEL = "eleven_monolingual_v1"
ELEVENLABS_BASE_URL = "https://api.elevenlabs.io/v1/text-to-speech"
VTUBE_STUDIO_URL = "ws://localhost:8001"