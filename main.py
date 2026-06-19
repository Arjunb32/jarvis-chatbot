"""
main.py — JARVIS AI Chatbot
IEEE RAS TRIGGER Daily Task | 18/06/26
Author: Arjun, SCT College of Engineering, Thiruvananthapuram
"""

import os
import sys
import datetime
import webbrowser
from typing import Optional

import pyttsx3
import speech_recognition as sr
from colorama import init, Fore, Style

import config

# ── Anthropic client (lazy import so text-only mode works without the key) ──
try:
    import anthropic
    _ANTHROPIC_AVAILABLE = True
except ImportError:
    _ANTHROPIC_AVAILABLE = False

init(autoreset=True)  # colorama

# ───────────────────────────── ASCII BANNER ─────────────────────────────────

BANNER = rf"""
{Fore.CYAN}     ██╗ █████╗ ██████╗ ██╗   ██╗██╗███████╗
     ██║██╔══██╗██╔══██╗██║   ██║██║██╔════╝
     ██║███████║██████╔╝██║   ██║██║███████╗
██   ██║██╔══██║██╔══██╗╚██╗ ██╔╝██║╚════██║
╚█████╔╝██║  ██║██║  ██║ ╚████╔╝ ██║███████║
 ╚════╝ ╚═╝  ╚═╝╚═╝  ╚═╝  ╚═══╝  ╚═╝╚══════╝
{Style.DIM}         Just A Rather Very Intelligent System
{Style.RESET_ALL}"""

# ───────────────────────────── TTS ──────────────────────────────────────────

def init_tts() -> pyttsx3.Engine:
    """Initialise and configure the text-to-speech engine."""
    engine = pyttsx3.init()
    engine.setProperty("rate", config.TTS_RATE)
    engine.setProperty("volume", config.TTS_VOLUME)
    # Prefer a male voice if available (more JARVIS-like)
    voices = engine.getProperty("voices")
    for voice in voices:
        if "male" in voice.name.lower() or "david" in voice.name.lower():
            engine.setProperty("voice", voice.id)
            break
    return engine


def speak(engine: pyttsx3.Engine, text: str) -> None:
    """Speak *text* aloud using the TTS engine."""
    try:
        engine.say(text)
        engine.runAndWait()
    except RuntimeError:
        # Engine already running in some edge cases — skip gracefully
        pass


# ───────────────────────────── LOGGING ──────────────────────────────────────

def log(speaker: str, message: str) -> None:
    """Append a timestamped line to the conversation log file."""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(config.LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {speaker}: {message}\n")


def log_divider(label: str = "SESSION STARTED") -> None:
    """Write a session boundary marker to the log."""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(config.LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] --- {label} ---\n")


# ───────────────────────────── OUTPUT ───────────────────────────────────────

def print_jarvis(text: str) -> None:
    """Print JARVIS's response in cyan."""
    print(f"{Fore.CYAN}{config.JARVIS_NAME}: {text}{Style.RESET_ALL}")


def print_user(text: str) -> None:
    """Print the user's input in default colour."""
    print(f"You: {text}")


def print_warn(text: str) -> None:
    """Print a system/warning message in yellow."""
    print(f"{Fore.YELLOW}[!] {text}{Style.RESET_ALL}")


# ───────────────────────────── VOICE INPUT ──────────────────────────────────

def check_voice_available() -> bool:
    """Return True if PyAudio and a microphone are accessible."""
    try:
        import pyaudio  # noqa: F401
        rec = sr.Recognizer()
        with sr.Microphone() as _:
            pass
        return True
    except (ImportError, OSError, AttributeError):
        return False


def listen(recognizer: sr.Recognizer, retries: int = config.MAX_VOICE_RETRIES) -> Optional[str]:
    """
    Listen through the microphone and return recognised text.
    Returns None after exhausting *retries* attempts.
    """
    for attempt in range(1, retries + 1):
        try:
            with sr.Microphone() as source:
                print_warn(f"Listening… (attempt {attempt}/{retries})")
                recognizer.adjust_for_ambient_noise(source, duration=0.8)
                audio = recognizer.listen(source, timeout=6, phrase_time_limit=10)

            text = recognizer.recognize_google(audio)
            print_user(text)
            return text.lower()

        except sr.WaitTimeoutError:
            print_warn("No speech detected. Please speak after the prompt.")
        except sr.UnknownValueError:
            print_warn("Could not understand that. Please try again.")
        except sr.RequestError as exc:
            print_warn(f"Google Speech service error: {exc}")
            break  # Network issue — no point retrying

    return None


# ───────────────────────────── LOCAL COMMANDS ───────────────────────────────

def get_local_response(user_input: str) -> Optional[str]:
    """
    Handle fast deterministic commands locally.
    Returns a response string, or None if the input should go to Claude.
    """
    inp = user_input.strip().lower()

    if any(w in inp for w in ("hello", "hi", "hey")):
        return f"Hello {config.USER_NAME}! Systems online. What do you need?"

    if "time" in inp:
        now = datetime.datetime.now().strftime("%I:%M %p")
        return f"The current time is {now}."

    if "date" in inp:
        today = datetime.datetime.now().strftime("%A, %d %B %Y")
        return f"Today is {today}."

    if "open google" in inp:
        webbrowser.open("https://google.com")
        return "Opening Google for you."

    if "open youtube" in inp:
        webbrowser.open("https://youtube.com")
        return "Opening YouTube. Don't get distracted, Arjun."

    if "open github" in inp:
        webbrowser.open("https://github.com")
        return "Opening GitHub."

    if "open notepad" in inp:
        if sys.platform == "win32":
            os.system("notepad")
            return "Notepad is open."
        return "Notepad is a Windows-only command. Try gedit or nano on Linux."

    if any(w in inp for w in ("your name", "who are you", "what are you")):
        return (
            "I am JARVIS — Just A Rather Very Intelligent System. "
            f"Personal assistant to {config.USER_NAME}, at your service."
        )

    if any(w in inp for w in ("bye", "exit", "quit", "stop", "goodbye")):
        return "__EXIT__"

    return None  # Let Claude handle it


# ───────────────────────────── CLAUDE API ───────────────────────────────────

def get_ai_response(history: list[dict]) -> str:
    """Send the conversation history to Claude and return the reply."""
    if not _ANTHROPIC_AVAILABLE:
        return "The Anthropic library is not installed. Please run: pip install anthropic"

    if config.ANTHROPIC_API_KEY == "your-api-key-here":
        return (
            "I don't have a live API key right now, but I'm still here for local commands. "
            "Set ANTHROPIC_API_KEY in config.py to unlock full AI responses."
        )

    try:
        client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
        response = client.messages.create(
            model=config.CLAUDE_MODEL,
            max_tokens=config.CLAUDE_MAX_TOKENS,
            system=config.SYSTEM_PROMPT,
            messages=history,
        )
        return response.content[0].text
    except anthropic.AuthenticationError:
        return "API authentication failed. Check your key in config.py."
    except anthropic.APIConnectionError:
        return "Could not reach the Anthropic API. Check your internet connection."
    except anthropic.RateLimitError:
        return "Rate limit hit. Give me a moment before the next question."
    except Exception as exc:  # noqa: BLE001
        return f"Unexpected API error: {exc}"


# ───────────────────────────── MAIN LOOP ────────────────────────────────────

def main() -> None:
    print(BANNER)

    engine = init_tts()
    recognizer = sr.Recognizer()
    voice_available = check_voice_available()

    if not voice_available:
        print_warn("No microphone / PyAudio detected — voice mode disabled.")

    greeting = f"Hello {config.USER_NAME}, I am {config.JARVIS_NAME}. How can I assist you today?"
    print_jarvis(greeting)
    speak(engine, greeting)

    log_divider("SESSION STARTED")
    log(config.JARVIS_NAME, greeting)

    conversation_history: list[dict] = []
    message_count: int = 0

    while True:
        # ── Input mode menu ──────────────────────────────────────────────────
        print()
        print(f"{Fore.CYAN}┌─ Select input mode ───────────┐{Style.RESET_ALL}")
        print(f"{Fore.CYAN}│  [1] Text                     │{Style.RESET_ALL}")
        if voice_available:
            print(f"{Fore.CYAN}│  [2] Voice                    │{Style.RESET_ALL}")
        else:
            print(f"{Fore.YELLOW}│  [2] Voice  (unavailable)     │{Style.RESET_ALL}")
        print(f"{Fore.CYAN}│  [3] Exit                     │{Style.RESET_ALL}")
        print(f"{Fore.CYAN}└───────────────────────────────┘{Style.RESET_ALL}")

        choice = input("> ").strip()

        if choice == "3":
            break

        # ── Capture user input ───────────────────────────────────────────────
        user_text: Optional[str] = None

        if choice == "1":
            raw = input("You: ").strip()
            if raw:
                user_text = raw.lower()
                log("User", raw)

        elif choice == "2":
            if not voice_available:
                print_warn("Voice mode is unavailable on this machine.")
                continue
            user_text = listen(recognizer)
            if user_text:
                log("User", user_text)
            else:
                print_warn("Voice input failed. Switching to text for this turn.")
                raw = input("You: ").strip()
                if raw:
                    user_text = raw.lower()
                    log("User", raw)
        else:
            print_warn("Invalid choice. Enter 1, 2, or 3.")
            continue

        if not user_text:
            continue

        # ── Generate response ────────────────────────────────────────────────
        local = get_local_response(user_text)

        if local == "__EXIT__":
            break

        if local:
            response = local
        else:
            # Add user turn to history and call Claude
            conversation_history.append({"role": "user", "content": user_text})
            response = get_ai_response(conversation_history)
            conversation_history.append({"role": "assistant", "content": response})

        # ── Output ───────────────────────────────────────────────────────────
        print_jarvis(response)
        speak(engine, response)
        log(config.JARVIS_NAME, response)
        message_count += 1

    # ── Exit ─────────────────────────────────────────────────────────────────
    plural = "message" if message_count == 1 else "messages"
    farewell = (
        f"Session complete. We exchanged {message_count} {plural}. "
        f"Goodbye, {config.USER_NAME}. Have a productive day."
    )
    print()
    print_jarvis(farewell)
    speak(engine, farewell)
    log(config.JARVIS_NAME, farewell)
    log_divider("SESSION ENDED")


if __name__ == "__main__":
    main()
