"""JARVIS-style chatbot with text, voice, TTS, logging, and Gemini support."""

import datetime as dt
import os
import re
import sys
import webbrowser
from typing import Any, Dict, List, Optional

from colorama import Fore, Style, init
import pyttsx3
import speech_recognition as sr

import config


ConversationHistory = List[Dict[str, str]]

BANNER = rf"""
{Fore.CYAN}     ██╗ █████╗ ██████╗ ██╗   ██╗██╗███████╗
     ██║██╔══██╗██╔══██╗██║   ██║██║██╔════╝
     ██║███████║██████╔╝██║   ██║██║███████╗
██   ██║██╔══██║██╔══██╗╚██╗ ██╔╝██║╚════██║
╚█████╔╝██║  ██║██║  ██║ ╚████╔╝ ██║███████║
 ╚════╝ ╚═╝  ╚═╝╚═╝  ╚═╝  ╚═══╝  ╚═╝╚══════╝
{Style.DIM}         Just A Rather Very Intelligent System
{Style.RESET_ALL}"""

HELP_TEXT = (
    "Available commands: hello, what is your name, time, date, open google, "
    "open youtube, open github, open notepad, help, and bye. You can also ask "
    "general questions; Gemini answers them when GEMINI_API_KEY is set."
)

EXIT_TOKEN = "__EXIT__"


def init_tts() -> Optional[Any]:
    """Initialize and configure the text-to-speech engine."""
    try:
        engine = pyttsx3.init()
        engine.setProperty("rate", config.TTS_RATE)
        engine.setProperty("volume", config.TTS_VOLUME)

        voices = engine.getProperty("voices")
        for voice in voices:
            voice_name = getattr(voice, "name", "").lower()
            if "male" in voice_name or "david" in voice_name:
                engine.setProperty("voice", voice.id)
                break

        return engine
    except (ImportError, RuntimeError, OSError, AttributeError) as error:
        print_warn(f"Text-to-speech is unavailable: {error}")
        return None


def speak(engine: Optional[Any], text: str) -> None:
    """Speak text aloud when the TTS engine is available."""
    if engine is None:
        return

    try:
        engine.say(text)
        engine.runAndWait()
    except (RuntimeError, OSError, AttributeError) as error:
        print_warn(f"Text-to-speech failed: {error}")


def log(speaker: str, message: str) -> None:
    """Append a timestamped message to the conversation log file."""
    timestamp = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(config.LOG_FILE, "a", encoding="utf-8") as log_file:
        log_file.write(f"[{timestamp}] {speaker}: {message}\n")


def log_divider(label: str) -> None:
    """Append a timestamped session divider to the conversation log file."""
    timestamp = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(config.LOG_FILE, "a", encoding="utf-8") as log_file:
        log_file.write(f"[{timestamp}] --- {label} ---\n")


def print_jarvis(text: str) -> None:
    """Print a JARVIS response in cyan."""
    print(f"{Fore.CYAN}{config.JARVIS_NAME}: {text}{Style.RESET_ALL}")


def print_user(text: str) -> None:
    """Print user text in the default console color."""
    print(f"{Fore.WHITE}You: {text}{Style.RESET_ALL}")


def print_warn(text: str) -> None:
    """Print system warnings in yellow."""
    print(f"{Fore.YELLOW}[!] {text}{Style.RESET_ALL}")


def configure_console() -> None:
    """Use UTF-8 console output when Python exposes stream reconfiguration."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is None:
            continue

        try:
            reconfigure(encoding="utf-8", errors="replace")
        except (OSError, ValueError):
            continue


def deliver_response(engine: Optional[Any], response: str) -> None:
    """Print, speak, and log one JARVIS response."""
    print_jarvis(response)
    speak(engine, response)
    log(config.JARVIS_NAME, response)


def check_voice_available() -> bool:
    """Return True if SpeechRecognition can access a microphone."""
    try:
        microphone_names = sr.Microphone.list_microphone_names()
        if not microphone_names:
            return False

        with sr.Microphone():
            return True
    except (ImportError, OSError, AttributeError):
        return False


def listen(
    recognizer: sr.Recognizer,
    retries: int = config.MAX_VOICE_RETRIES,
) -> Optional[str]:
    """Listen through the microphone and return recognized text."""
    attempts = retries + 1

    for attempt in range(1, attempts + 1):
        try:
            with sr.Microphone() as source:
                print_warn(f"Calibrating microphone... attempt {attempt}/{attempts}")
                recognizer.adjust_for_ambient_noise(
                    source,
                    duration=config.AMBIENT_NOISE_DURATION,
                )
                print_warn("Listening...")
                audio = recognizer.listen(
                    source,
                    timeout=config.VOICE_TIMEOUT,
                    phrase_time_limit=config.VOICE_PHRASE_TIME_LIMIT,
                )

            text = recognizer.recognize_google(audio)
            print_user(text)
            return text.strip()

        except sr.WaitTimeoutError:
            print_warn("No speech detected. Please try again.")
        except sr.UnknownValueError:
            print_warn("Sorry, I could not understand that. Please try again.")
        except sr.RequestError as error:
            print_warn(f"Speech recognition service failed: {error}")
            return None
        except (OSError, AttributeError) as error:
            print_warn(f"Microphone failed: {error}")
            return None

    return None


def get_local_response(user_input: str) -> Optional[str]:
    """Handle local commands and return None for general AI questions."""
    text = user_input.strip().lower()

    if _contains_word(text, ("exit", "quit", "bye", "goodbye", "stop")):
        return EXIT_TOKEN

    if _contains_word(text, ("hello", "hi", "hey")):
        return f"Hello {config.USER_NAME}! Systems online. What do you need?"

    if "help" in text:
        return HELP_TEXT

    if "what is your name" in text or "your name" in text or "who are you" in text:
        return (
            f"I am {config.JARVIS_NAME}, your JARVIS-style assistant for this "
            "chatbot demo."
        )

    if "time" in text:
        current_time = dt.datetime.now().strftime("%I:%M %p")
        return f"The current time is {current_time}."

    if "date" in text or "today's date" in text or "today’s date" in text:
        current_date = dt.datetime.now().strftime("%A, %d %B %Y")
        return f"Today is {current_date}."

    if "open google" in text:
        return open_website("https://google.com", "Opening Google for you, Arjun.")

    if "open youtube" in text:
        return open_website("https://youtube.com", "Opening YouTube for you, Arjun.")

    if "open github" in text:
        return open_website("https://github.com", "Opening GitHub for you, Arjun.")

    if "open notepad" in text:
        return open_notepad()

    return None


def get_ai_response(history: ConversationHistory) -> str:
    """Return a Gemini answer, or a useful offline fallback when unavailable."""
    if not config.GEMINI_API_KEY:
        return config.OFFLINE_FALLBACK_RESPONSE

    try:
        from google import genai
        from google.genai import errors, types
        import httpx
        import requests
    except ImportError:
        return config.GEMINI_PACKAGE_MISSING_RESPONSE

    api_error_types = (
        errors.APIError,
        httpx.HTTPError,
        requests.RequestException,
        RuntimeError,
        ValueError,
        OSError,
        TimeoutError,
    )

    try:
        client = genai.Client(api_key=config.GEMINI_API_KEY)
        contents = build_gemini_contents(history, types)
        response = client.models.generate_content(
            model=config.GEMINI_MODEL,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=config.SYSTEM_PROMPT,
                max_output_tokens=config.GEMINI_MAX_OUTPUT_TOKENS,
                temperature=config.GEMINI_TEMPERATURE,
            ),
        )
        response_text = getattr(response, "text", "").strip()
        return response_text or config.GEMINI_EMPTY_RESPONSE
    except api_error_types as error:
        print_warn(f"Gemini request failed: {error}")
        return config.GEMINI_API_ERROR_RESPONSE
    finally:
        client_to_close = locals().get("client")
        if client_to_close is not None:
            close_client(client_to_close)


def build_gemini_contents(history: ConversationHistory, types_module: Any) -> List[Any]:
    """Convert local conversation history into Gemini content objects."""
    contents: List[Any] = []
    recent_history = history[-12:]

    for message in recent_history:
        role = "model" if message["role"] == "assistant" else "user"
        contents.append(
            types_module.Content(
                role=role,
                parts=[types_module.Part.from_text(text=message["content"])],
            )
        )

    return contents


def close_client(client: Any) -> None:
    """Close a Gemini client when the SDK exposes a close method."""
    close_method = getattr(client, "close", None)
    if close_method is None:
        return

    try:
        close_method()
    except (RuntimeError, OSError, AttributeError):
        return


def open_website(url: str, success_message: str) -> str:
    """Open a website and return a friendly status message."""
    try:
        webbrowser.open(url)
        return success_message
    except webbrowser.Error as error:
        print_warn(f"Could not open browser: {error}")
        return "I could not open that website from this environment, Arjun."


def open_notepad() -> str:
    """Open Windows Notepad when available."""
    if sys.platform != "win32":
        return "Notepad is only available from this demo on Windows."

    try:
        os.system("notepad")
        return "Opening Notepad for you, Arjun."
    except OSError as error:
        print_warn(f"Could not open Notepad: {error}")
        return "I could not open Notepad from this environment, Arjun."


def print_menu(voice_available: bool) -> None:
    """Print the input mode menu."""
    print()
    print(f"{Fore.CYAN}┌─ Select input mode ───────────┐{Style.RESET_ALL}")
    print(f"{Fore.CYAN}│  [1] Text                     │{Style.RESET_ALL}")
    if voice_available:
        print(f"{Fore.CYAN}│  [2] Voice                    │{Style.RESET_ALL}")
    else:
        print(f"{Fore.YELLOW}│  [2] Voice  (unavailable)     │{Style.RESET_ALL}")
    print(f"{Fore.CYAN}│  [3] Exit                     │{Style.RESET_ALL}")
    print(f"{Fore.CYAN}└───────────────────────────────┘{Style.RESET_ALL}")


def read_text_turn() -> Optional[str]:
    """Read a keyboard input turn."""
    raw = input("You: ").strip()
    return raw or None


def read_user_turn(
    choice: str,
    recognizer: sr.Recognizer,
    voice_available: bool,
) -> Optional[str]:
    """Read one user turn from the selected input mode."""
    if choice == "1":
        return read_text_turn()

    if choice == "2":
        if not voice_available:
            print_warn("Voice mode is unavailable on this machine.")
            return None

        voice_text = listen(recognizer)
        if voice_text:
            return voice_text

        print_warn("Voice input failed. Please type your request instead.")
        return read_text_turn()

    print_warn("Invalid choice. Enter 1, 2, or 3.")
    return None


def _contains_word(text: str, words: tuple) -> bool:
    """Return True when text contains any whole word from words."""
    return any(re.search(rf"\b{re.escape(word)}\b", text) for word in words)


def main() -> None:
    """Run the JARVIS chatbot."""
    configure_console()
    init(autoreset=True)
    print(BANNER)

    engine = init_tts()
    recognizer = sr.Recognizer()
    voice_available = check_voice_available()

    if not voice_available:
        print_warn("No microphone or PyAudio detected. Voice mode is disabled.")

    greeting = (
        f"Hello {config.USER_NAME}, I am {config.JARVIS_NAME}. "
        "How can I assist you today?"
    )
    log_divider("SESSION STARTED")
    deliver_response(engine, greeting)

    conversation_history: ConversationHistory = []
    message_count = 0

    while True:
        print_menu(voice_available)
        choice = input("> ").strip()

        if choice == "3":
            break

        user_text = read_user_turn(choice, recognizer, voice_available)
        if not user_text:
            print_warn("No input detected. Please try again.")
            continue

        log("User", user_text)
        message_count += 1

        local_response = get_local_response(user_text)
        if local_response == EXIT_TOKEN:
            break

        conversation_history.append({"role": "user", "content": user_text})

        if local_response:
            response = local_response
        else:
            response = get_ai_response(conversation_history)

        conversation_history.append({"role": "assistant", "content": response})
        deliver_response(engine, response)

    farewell = (
        f"Session complete. We exchanged {message_count} messages. "
        f"Goodbye, {config.USER_NAME}. Have a productive day."
    )
    print()
    deliver_response(engine, farewell)
    log_divider("SESSION ENDED")


if __name__ == "__main__":
    main()
