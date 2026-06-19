# JARVIS Chatbot

JARVIS-style Python chatbot assignment project for the IEEE RAS TRIGGER daily task.

Author: Arjun, SCT College of Engineering, Thiruvananthapuram

## Features

- Text input mode with a clean console menu
- Voice input mode using `SpeechRecognition`
- Speech-to-text with Google recognition
- Text-to-speech output using `pyttsx3`
- Colored console output with `colorama`
- Timestamped conversation logging
- Local commands for greetings, name, time, date, websites, help, and exit
- Gemini-powered general answers when `GEMINI_API_KEY` is set
- Offline fallback mode when no API key is available
- Graceful handling for microphone, TTS, recognition, and API failures

## Prerequisites

- Python 3.9 or newer
- A Gemini API key for general AI answers
- A microphone for voice input mode

## Installation

```powershell
cd "C:\Users\Arjun\Desktop\CHAT BOT\jarvis-chatbot"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

If `pyaudio` fails to install on Windows, try:

```powershell
python -m pip install pipwin
pipwin install pyaudio
python -m pip install -r requirements.txt
```

## API Key Setup

The project does not store API keys in source files. Set your Gemini key locally in PowerShell before running:

```powershell
$env:GEMINI_API_KEY="your_new_key_here"
```

Do not commit API keys, `.env` files, screenshots showing keys, or terminal output containing secrets.

`ANTHROPIC_API_KEY` is also read safely from the environment for compatibility, but this project uses Gemini for general AI answers.

## How To Run

```powershell
python main.py
```

Choose an input mode from the menu:

- `1` for text input
- `2` for voice input
- `3` to exit

## Demo Instructions

Run the app and test these inputs:

```text
hello
what is your name
what is the time
what is today's date
help
who will win the 2026 world cup?
explain artificial intelligence in simple words
bye
```

With `GEMINI_API_KEY` set, general questions are answered by Gemini. Without a key, JARVIS stays in offline mode and continues to support local commands, speech output, voice input when available, console output, and logging.

## Folder Structure

```text
jarvis-chatbot/
├── main.py
├── config.py
├── requirements.txt
├── README.md
├── conversation_log.txt
├── demo_video_link.txt
└── .gitignore
```

## Security Notes

- API keys are loaded from environment variables only.
- `conversation_log.txt`, `.env`, `*.env`, `.venv/`, `__pycache__/`, and `*.pyc` are ignored by Git.
- Never paste real API keys into `config.py`, `main.py`, `README.md`, or committed files.
