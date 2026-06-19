# JARVIS Chatbot

IEEE RAS TRIGGER Daily Task submission by Arjun, SCT College of Engineering.

## Features

1. Dual input support with text and voice modes.
2. Speech-to-text using `speech_recognition` and Google recognition.
3. Claude-powered AI responses through the Anthropic API.
4. Local command handling for greetings, time, date, websites, Notepad, identity, and exit.
5. Dual output with colored console text and spoken responses through `pyttsx3`.
6. Persistent conversation logging in `conversation_log.txt`.
7. Session summary on exit.
8. Graceful text-only fallback when microphone hardware or PyAudio is unavailable.
9. Voice retry logic and a startup ASCII JARVIS banner.

## Prerequisites

- Python 3.8 or newer
- An Anthropic API key
- A working microphone for voice mode
- Windows is recommended for the Notepad command

Set your API key in `config.py`:

```python
ANTHROPIC_API_KEY = "your-real-api-key"
```

## Installation

```powershell
cd "C:\Users\Arjun\Desktop\CHAT BOT\jarvis-chatbot"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## How To Run

```powershell
python main.py
```

At startup, choose:

- `1` for keyboard input
- `2` for microphone input
- `3` to exit

## Folder Structure

```text
jarvis-chatbot/
├── main.py
├── config.py
├── requirements.txt
├── README.md
├── conversation_log.txt
└── demo_video_link.txt
```

## Known Issues

- `pyaudio` can fail to install on Windows with a normal `pip install`.
- If that happens, install `pipwin` first:

```powershell
python -m pip install pipwin
pipwin install pyaudio
```

- If no microphone is connected, JARVIS automatically disables voice mode and continues in text mode.
- If the API key is still set to the placeholder value, general AI questions will not call Claude.

## Author

Arjun  
SCT College of Engineering, Thiruvananthapuram
