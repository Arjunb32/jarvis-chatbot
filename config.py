"""Configuration for the JARVIS chatbot.

API keys are loaded only from environment variables. Do not write real keys
into this file or any other committed project file.
"""

import os


# API keys: leave these empty unless they are set in the local environment.
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# Identity
JARVIS_NAME = "JARVIS"
USER_NAME = "Arjun"

# Gemini
GEMINI_MODEL = "gemini-2.0-flash"
GEMINI_MAX_OUTPUT_TOKENS = 300
GEMINI_TEMPERATURE = 0.4

# Text-to-speech
TTS_RATE = 175
TTS_VOLUME = 1.0

# Voice input
MAX_VOICE_RETRIES = 2
VOICE_TIMEOUT = 6
VOICE_PHRASE_TIME_LIMIT = 10
AMBIENT_NOISE_DURATION = 1
VOICE_RECORD_SECONDS = 5
MIC_DEVICE_INDEX = os.getenv("MIC_DEVICE_INDEX", "")
PREFERRED_MICROPHONE_KEYWORDS = (
    "microphone array",
    "microphone",
    "input",
)

# Logging
LOG_FILE = "conversation_log.txt"

# Prompting
SYSTEM_PROMPT = (
    "You are JARVIS, a concise and useful AI assistant for Arjun, a student at "
    "SCT College of Engineering, Thiruvananthapuram. Keep answers friendly, "
    "clear, and practical in 1-3 sentences unless the user asks for detail. "
    "Use a light JARVIS-like tone, but do not overdo it."
)

OFFLINE_FALLBACK_RESPONSE = (
    "I am currently running in offline mode. I can handle basic commands like "
    "time, date, opening websites, text input, voice input, speech output, and "
    "logging. For general AI answers, please set GEMINI_API_KEY."
)

GEMINI_PACKAGE_MISSING_RESPONSE = (
    "Gemini support is configured, but the google-genai package is not installed. "
    "Run python -m pip install -r requirements.txt and try again."
)

GEMINI_API_ERROR_RESPONSE = (
    "I could not reach Gemini right now. Please check your internet connection "
    "or GEMINI_API_KEY, then try again."
)

GEMINI_EMPTY_RESPONSE = "Gemini returned an empty response. Please try again."
