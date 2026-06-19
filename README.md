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
- Voice recording through `sounddevice`, with optional PyAudio support when available

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

If `python main.py` says a module is missing, make sure `pip` and `python` are from the same interpreter:

```powershell
python -m pip install -r requirements.txt
python main.py
```

If voice or speech output fails on your laptop, the chatbot now keeps running in text mode instead of crashing.

On Python 3.14, PyAudio may fail to install because no wheel is available. This project uses `sounddevice` for microphone recording, so voice mode still works without PyAudio.

Voice mode automatically selects an input-capable microphone. If Windows picks the wrong device, set a microphone index before running:

```powershell
$env:MIC_DEVICE_INDEX="1"
python main.py
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

- `1` for continuous text chat
- `2` for continuous voice chat
- `3` to exit

Inside text chat, type `4` to return to the mode menu or type `exit`, `quit`, `bye`, or `3` to quit.

Inside voice chat, use the push-to-talk controls:

- Press `Enter` to record one voice message
- Type `4` to return to the mode menu
- Type `3`, `exit`, `quit`, or `bye` to quit

During the short recording window after pressing `Enter`:

- Press `3` to exit immediately
- Press `4` to return to the mode menu
- Press `q` or `Esc` to cancel the recording and go back to `Voice>`

You can also say `change mode`, `switch mode`, or `four` after recording to return to the mode menu. Say `exit`, `quit`, `bye`, or `stop` after recording to quit.

## Demo Instructions

Run the app and test these inputs:

```text
1
hello
what is your name
what is the time
what is today's date
help
who will win the 2026 world cup?
explain artificial intelligence in simple words
4
3
```

With `GEMINI_API_KEY` set, general questions are answered by Gemini. Without a key, JARVIS stays in offline mode and continues to support local commands, speech output, voice input when available, console output, and logging.

For voice mode, choose `2` from the main menu, press `Enter` when you want to speak, then talk after the listening prompt. If no microphone is available, JARVIS explains the problem and returns to the mode menu automatically.

## Opening Apps and Websites

JARVIS can open common websites and installed Windows apps from text or voice commands. Websites are opened in Google Chrome when Chrome is installed; otherwise, they open in the default browser.

Try commands such as:

```text
open amazon web
open youtube
open google
open github
open whatsapp web
open instagram web
open gmail
open notepad
open calculator
open chrome
open vs code
```

Unknown website-style commands also work:

```text
open netflix web
open example.com
```

For safety, JARVIS refuses destructive system commands such as delete, format, shutdown, restart, and registry-edit requests.

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
