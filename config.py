# config.py — JARVIS Chatbot Configuration
# ─────────────────────────────────────────
# Only values that differ between environments or that you'd
# reasonably want to tune live here. Everything else stays in main.py.

# ── API ───────────────────────────────────────────────────────────────────────
import os

# Do not write your real API key here.
# Set the key in the terminal using:
# $env:GEMINI_API_KEY="your_new_api_key_here"

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")

API_KEY = GEMINI_API_KEY or GOOGLE_API_KEY

# ── Identity ──────────────────────────────────────────────────────────────────
JARVIS_NAME: str = "JARVIS"
USER_NAME: str   = "Arjun"

# ── Text-to-speech ────────────────────────────────────────────────────────────
TTS_RATE: int    = 175    # words per minute
TTS_VOLUME: float = 1.0   # 0.0 – 1.0

# ── Voice input ───────────────────────────────────────────────────────────────
MAX_VOICE_RETRIES: int          = 2
VOICE_TIMEOUT: int              = 6    # seconds to wait for speech to start
VOICE_PHRASE_TIME_LIMIT: int    = 10   # max seconds per utterance
AMBIENT_NOISE_DURATION: float   = 0.8  # calibration window in seconds

# ── Logging ───────────────────────────────────────────────────────────────────
LOG_FILE: str = "conversation_log.txt"

# ── Claude system prompt ──────────────────────────────────────────────────────
SYSTEM_PROMPT: str = (
    f"You are JARVIS, a witty and efficient AI assistant for {USER_NAME}, "
    "a student at SCT College of Engineering, Thiruvananthapuram. "
    "Keep responses concise — 1 to 3 sentences unless detail is explicitly requested. "
    "Be helpful, direct, and occasionally witty. Never break character."
)
