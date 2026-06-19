"""JARVIS-style chatbot with text, voice, TTS, logging, and Gemini support."""

import datetime as dt
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import webbrowser
import queue
import time
from typing import Any, Dict, List, Optional

try:
    import msvcrt
except ImportError:
    msvcrt = None

try:
    from colorama import Fore, Style, init
except ImportError:
    class _NoColor:
        """Fallback color constants when colorama is not installed."""

        BLACK = RED = GREEN = YELLOW = BLUE = MAGENTA = CYAN = WHITE = RESET = ""
        BRIGHT = DIM = NORMAL = RESET_ALL = ""

    Fore = Style = _NoColor()

    def init(*args: Any, **kwargs: Any) -> None:
        """Fallback colorama initializer."""
        return None

try:
    import pyttsx3
except ImportError:
    pyttsx3 = None

try:
    import speech_recognition as sr
except ImportError:
    sr = None

try:
    import pyaudio
except ImportError:
    pyaudio = None

try:
    import numpy as np
    import sounddevice as sd
except ImportError:
    np = None
    sd = None

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
    "open youtube, open amazon web, open github, open whatsapp web, open "
    "notepad, open calculator, help, and bye. You can also ask general "
    "questions; Gemini answers them when GEMINI_API_KEY is set."
)

EXIT_TOKEN = "__EXIT__"
CHANGE_MODE_TOKEN = "__CHANGE_MODE__"

WEBSITES = {
    "google": "https://www.google.com",
    "youtube": "https://www.youtube.com",
    "amazon": "https://www.amazon.in",
    "amazon web": "https://www.amazon.in",
    "flipkart": "https://www.flipkart.com",
    "github": "https://github.com",
    "gmail": "https://mail.google.com",
    "instagram": "https://www.instagram.com",
    "instagram web": "https://www.instagram.com",
    "facebook": "https://www.facebook.com",
    "twitter": "https://x.com",
    "x": "https://x.com",
    "linkedin": "https://www.linkedin.com",
    "chatgpt": "https://chatgpt.com",
    "wikipedia": "https://www.wikipedia.org",
    "whatsapp web": "https://web.whatsapp.com",
}

APPS = {
    "notepad": "notepad.exe",
    "calculator": "calc.exe",
    "paint": "mspaint.exe",
    "cmd": "cmd.exe",
    "command prompt": "cmd.exe",
    "powershell": "powershell.exe",
    "task manager": "taskmgr.exe",
    "file explorer": "explorer.exe",
    "explorer": "explorer.exe",
    "control panel": "control.exe",
    "chrome": "chrome.exe",
    "google chrome": "chrome.exe",
    "edge": "msedge.exe",
    "microsoft edge": "msedge.exe",
    "firefox": "firefox.exe",
    "vscode": "code.exe",
    "vs code": "code.exe",
    "visual studio code": "code.exe",
    "word": "winword.exe",
    "microsoft word": "winword.exe",
    "excel": "excel.exe",
    "microsoft excel": "excel.exe",
    "powerpoint": "powerpnt.exe",
    "microsoft powerpoint": "powerpnt.exe",
    "whatsapp": "WhatsApp.exe",
    "discord": "Discord.exe",
    "spotify": "Spotify.exe",
    "telegram": "Telegram.exe",
}

APP_SEARCH_ALIASES = {
    "vscode": ("visual studio code", "vs code", "code"),
    "vs code": ("visual studio code", "code"),
    "visual studio code": ("vs code", "code"),
    "chrome": ("google chrome",),
    "google chrome": ("chrome",),
    "edge": ("microsoft edge",),
    "whatsapp": ("whats app",),
}

OPEN_COMMAND_PREFIXES = ("open", "launch", "start", "go to", "visit")
DANGEROUS_COMMAND_TERMS = (
    "delete",
    "format",
    "shutdown",
    "restart",
    "remove files",
    "remove file",
    "registry edit",
    "regedit",
    "erase",
    "wipe",
    "powershell script",
)


def init_tts() -> Optional[Any]:
    """Initialize and configure the text-to-speech engine."""
    if pyttsx3 is None:
        print_warn("pyttsx3 is not installed. Speech output is disabled.")
        return None

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


def deliver_system_response(engine: Optional[Any], response: str) -> None:
    """Print and speak a system-style response without labeling it as user input."""
    print_jarvis(response)
    speak(engine, response)
    log(config.JARVIS_NAME, response)


def get_microphone_device_index() -> Optional[int]:
    """Return a preferred input microphone device index, if one is found."""
    if sr is None or (pyaudio is None and sd is None):
        return None

    configured_index = parse_microphone_index(config.MIC_DEVICE_INDEX)
    if configured_index is not None and can_open_microphone(configured_index):
        return configured_index

    input_devices = list_input_devices()
    for device in sort_microphone_devices(input_devices):
        device_index = int(device["index"])
        if can_open_microphone(device_index):
            return device_index

    if can_open_microphone(None):
        return None

    return None


def microphone_available() -> bool:
    """Return True when a microphone input device is available."""
    microphone_index = get_microphone_device_index()
    return check_voice_available(microphone_index)


def check_voice_available(device_index: Optional[int]) -> bool:
    """Return True if the app can access a microphone."""
    if sr is None:
        return False

    if device_index is None and list_input_devices():
        return can_open_microphone(None)

    return device_index is not None and can_open_microphone(device_index)


def can_open_microphone(device_index: Optional[int]) -> bool:
    """Return True when a microphone device can be opened."""
    if sr is None:
        return False

    if pyaudio is None:
        return can_open_sounddevice_microphone(device_index)

    try:
        with sr.Microphone(device_index=device_index):
            return True
    except (ImportError, OSError, AttributeError):
        return can_open_sounddevice_microphone(device_index)


def can_open_sounddevice_microphone(device_index: Optional[int]) -> bool:
    """Return True when sounddevice can access an input device."""
    if sd is None:
        return False

    try:
        sample_rate = get_sounddevice_sample_rate(device_index)
        sd.check_input_settings(
            device=device_index,
            channels=1,
            samplerate=sample_rate,
            dtype="int16",
        )
        return True
    except (sd.PortAudioError, TypeError, ValueError):
        return False


def parse_microphone_index(raw_value: str) -> Optional[int]:
    """Parse an optional microphone device index from configuration."""
    if not raw_value.strip():
        return None

    try:
        return int(raw_value)
    except ValueError:
        print_warn(f"Ignoring invalid MIC_DEVICE_INDEX value: {raw_value}")
        return None


def list_input_devices() -> List[Dict[str, Any]]:
    """List input-capable audio devices."""
    if pyaudio is None:
        return list_sounddevice_input_devices()

    audio = pyaudio.PyAudio()
    devices: List[Dict[str, Any]] = []

    try:
        for index in range(audio.get_device_count()):
            info = audio.get_device_info_by_index(index)
            if int(info.get("maxInputChannels", 0)) > 0:
                devices.append(
                    {
                        "index": index,
                        "name": str(info.get("name", "")),
                        "channels": int(info.get("maxInputChannels", 0)),
                    }
                )
    finally:
        audio.terminate()

    return devices


def show_available_microphones() -> None:
    """Print available microphone/input devices for debugging."""
    devices = sort_microphone_devices(list_input_devices())
    print_warn("Available microphones:")
    if not devices:
        print_warn("  No microphone input devices found.")
        return

    for device in devices:
        print_warn(
            f"  [{device['index']}] {device['name']} "
            f"({device['channels']} input channel(s))"
        )


def list_sounddevice_input_devices() -> List[Dict[str, Any]]:
    """List input-capable sounddevice devices."""
    if sd is None:
        return []

    devices: List[Dict[str, Any]] = []
    for index, info in enumerate(sd.query_devices()):
        if int(info.get("max_input_channels", 0)) > 0:
            devices.append(
                {
                    "index": index,
                    "name": str(info.get("name", "")),
                    "channels": int(info.get("max_input_channels", 0)),
                }
            )
    return devices


def sort_microphone_devices(devices: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Sort input devices so likely microphones are tried first."""
    preferred_keywords = config.PREFERRED_MICROPHONE_KEYWORDS

    def priority(device: Dict[str, Any]) -> tuple:
        name = str(device["name"]).lower()
        keyword_rank = next(
            (
                rank
                for rank, keyword in enumerate(preferred_keywords)
                if keyword in name
            ),
            len(preferred_keywords),
        )
        return (keyword_rank, int(device["index"]))

    return sorted(devices, key=priority)


def get_microphone_label(device_index: Optional[int]) -> str:
    """Return a readable microphone label for status output."""
    if device_index is None:
        return "system default microphone"

    for device in list_input_devices():
        if int(device["index"]) == device_index:
            return f"{device['name']} (index {device_index})"

    return f"microphone index {device_index}"


def listen_to_voice(
    recognizer: Any,
    device_index: Optional[int],
) -> Optional[str]:
    """Capture one push-to-talk voice input and return recognized text."""
    return listen(recognizer, device_index, 0)


def listen(
    recognizer: Any,
    device_index: Optional[int],
    retries: int = config.MAX_VOICE_RETRIES,
) -> Optional[str]:
    """Listen through the microphone and return recognized text."""
    if sr is None:
        print_warn("SpeechRecognition is not installed. Voice input is disabled.")
        return None

    if pyaudio is None:
        return listen_with_sounddevice(recognizer, device_index, retries)

    attempts = retries + 1

    for attempt in range(1, attempts + 1):
        try:
            with sr.Microphone(device_index=device_index) as source:
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
            print_warn(
                "Speech recognition service is unavailable. Please check your "
                "internet connection or use text mode."
            )
            print_warn(f"Speech recognition detail: {error}")
            return None
        except (OSError, AttributeError) as error:
            print_warn(
                "Microphone error detected. Please check Windows microphone "
                "permission and input device settings."
            )
            print_warn(
                "Open Windows Settings > Privacy & security > Microphone and "
                "allow microphone access for desktop apps."
            )
            print_warn(f"PyAudio detail: {error}")
            return listen_with_sounddevice(recognizer, device_index, retries)

    return None


def listen_with_sounddevice(
    recognizer: Any,
    device_index: Optional[int],
    retries: int,
) -> Optional[str]:
    """Record audio with sounddevice and recognize it with SpeechRecognition."""
    if sr is None or sd is None or np is None:
        print_warn("Sounddevice voice input is unavailable.")
        return None

    attempts = retries + 1

    for attempt in range(1, attempts + 1):
        try:
            sample_rate = get_sounddevice_sample_rate(device_index)
            print_warn(
                "Listening... speak now. Press 3 to exit, 4 for menu, or q/Esc "
                "to cancel "
                f"({config.VOICE_RECORD_SECONDS} seconds)."
            )
            recording, control_action = record_with_cancel(device_index, sample_rate)
            if control_action == EXIT_TOKEN:
                return EXIT_TOKEN

            if control_action == CHANGE_MODE_TOKEN:
                return CHANGE_MODE_TOKEN

            if recording is None:
                print_warn("Voice recording cancelled.")
                return None

            audio_data = sr.AudioData(recording.tobytes(), sample_rate, 2)
            text = recognizer.recognize_google(audio_data)
            print_user(text)
            return text.strip()

        except sr.UnknownValueError:
            print_warn("Sorry, I could not understand that. Please try again.")
        except sr.RequestError as error:
            print_warn(
                "Speech recognition service is unavailable. Please check your "
                "internet connection or use text mode."
            )
            print_warn(f"Speech recognition detail: {error}")
            return None
        except (sd.PortAudioError, OSError, ValueError, TypeError) as error:
            print_warn(
                "Microphone error detected. Please check Windows microphone "
                "permission and input device settings."
            )
            print_warn(
                "Open Windows Settings > Privacy & security > Microphone and "
                "allow microphone access for desktop apps."
            )
            print_warn(f"Sounddevice detail: {error}")
            return None

    return None


def record_with_cancel(
    device_index: Optional[int],
    sample_rate: int,
) -> tuple[Optional[Any], Optional[str]]:
    """Record microphone audio, allowing keyboard cancellation on Windows."""
    if sd is None:
        return None, None

    audio_queue: queue.Queue[Any] = queue.Queue()

    def audio_callback(indata: Any, frames: int, time_info: Any, status: Any) -> None:
        if status:
            print_warn(f"Audio input status: {status}")
        audio_queue.put(indata.copy())

    started_at = time.monotonic()
    chunks: List[Any] = []

    with sd.InputStream(
        samplerate=sample_rate,
        channels=1,
        dtype="int16",
        device=device_index,
        callback=audio_callback,
    ):
        while time.monotonic() - started_at < config.VOICE_RECORD_SECONDS:
            control_action = get_keyboard_recording_action()
            if control_action is not None:
                return None, control_action

            try:
                chunks.append(audio_queue.get(timeout=0.1))
            except queue.Empty:
                continue

    if not chunks:
        return None, None

    return np.concatenate(chunks, axis=0), None


def get_keyboard_recording_action() -> Optional[str]:
    """Return a control action if the user pressed a key during recording."""
    if msvcrt is None:
        return None

    if not msvcrt.kbhit():
        return None

    key = msvcrt.getwch().lower()
    if key in {"\x00", "\xe0"}:
        return None

    if key == "3":
        return EXIT_TOKEN

    if key == "4":
        return CHANGE_MODE_TOKEN

    if key in {"q", "x", "\x1b"}:
        return "cancel"

    return None


def get_sounddevice_sample_rate(device_index: Optional[int]) -> int:
    """Return the preferred sample rate for a sounddevice input device."""
    if sd is None:
        return 44100

    try:
        if device_index is None:
            device_index = sd.default.device[0]

        info = sd.query_devices(device_index)
        return int(info.get("default_samplerate", 44100))
    except (sd.PortAudioError, TypeError, ValueError):
        return 44100


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

    open_response = handle_open_command(user_input)
    if open_response:
        return open_response

    if "open google" in text:
        return open_website("https://google.com", "Opening Google for you, Arjun.")

    if "open youtube" in text:
        return open_website("https://youtube.com", "Opening YouTube for you, Arjun.")

    if "open github" in text:
        return open_website("https://github.com", "Opening GitHub for you, Arjun.")

    if "open notepad" in text:
        return open_notepad()

    return None


def handle_open_command(user_input: str) -> Optional[str]:
    """Open requested apps or websites for safe open/launch/start commands."""
    normalized = normalize_command_text(user_input)
    if not has_open_intent(normalized):
        return None

    if is_dangerous_open_command(normalized):
        return "For safety, I cannot run destructive system commands."

    target = extract_open_target(normalized)
    if not target:
        return "Tell me what app or website you want me to open, Arjun."

    website_url = get_website_url(target)
    if website_url:
        browser_name = open_url_in_chrome(website_url)
        display_name = get_display_name(target)
        return f"Opening {display_name} in {browser_name}."

    app_response = open_installed_app(target)
    if app_response:
        return app_response

    if looks_like_unknown_website(target) or has_browser_intent(normalized):
        url = build_unknown_website_url(target)
        browser_name = open_url_in_chrome(url)
        return f"Opening {get_domain_display(url)} in {browser_name}."

    return (
        "I could not find that app on this computer. Try opening it manually "
        "once or use the exact app name."
    )


def normalize_command_text(text: str) -> str:
    """Normalize a command for intent and target matching."""
    cleaned = text.strip().lower()
    cleaned = cleaned.replace("’", "'")
    cleaned = re.sub(r"[!?]", "", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned


def has_open_intent(text: str) -> bool:
    """Return True when text asks to open, launch, start, visit, or go to."""
    return any(re.search(rf"\b{re.escape(prefix)}\b", text) for prefix in OPEN_COMMAND_PREFIXES)


def has_browser_intent(text: str) -> bool:
    """Return True when the command wording implies website navigation."""
    return bool(re.search(r"\b(go to|visit)\b", text))


def is_dangerous_open_command(text: str) -> bool:
    """Return True when the requested command looks destructive."""
    return any(term in text for term in DANGEROUS_COMMAND_TERMS)


def extract_open_target(text: str) -> str:
    """Extract the app or website name from an open-style command."""
    for prefix in sorted(OPEN_COMMAND_PREFIXES, key=len, reverse=True):
        match = re.search(rf"\b{re.escape(prefix)}\b", text)
        if match:
            target = text[match.end():].strip()
            return clean_open_target(target)
    return ""


def clean_open_target(target: str) -> str:
    """Clean filler words from an extracted open target."""
    target = re.sub(r"^(the|my|a|an)\s+", "", target)
    target = re.sub(r"\s+(please|app|application|website|site)$", "", target)
    target = target.strip(" .,/\\")
    return target


def get_website_url(target: str) -> Optional[str]:
    """Return a known website URL for a target name."""
    target = normalize_website_target(target)
    if target in WEBSITES:
        return WEBSITES[target]

    no_web_target = strip_web_suffix(target)
    if no_web_target in WEBSITES:
        return WEBSITES[no_web_target]

    if "." in target:
        return ensure_https_url(target)

    return None


def normalize_website_target(target: str) -> str:
    """Normalize website target names for dictionary lookup."""
    return re.sub(r"\s+", " ", target.strip().lower())


def strip_web_suffix(target: str) -> str:
    """Remove web/site suffixes from unknown website commands."""
    return re.sub(r"\s+(web|website|site)$", "", target).strip()


def looks_like_unknown_website(target: str) -> bool:
    """Return True when a target should be treated as an unknown website."""
    return target.endswith(" web") or target.endswith(" website") or target.endswith(" site")


def build_unknown_website_url(target: str) -> str:
    """Build a likely URL for an unknown website target."""
    domain_name = strip_web_suffix(target).replace(" ", "")
    return f"https://www.{domain_name}.com"


def ensure_https_url(target: str) -> str:
    """Return target as an HTTPS URL."""
    if target.startswith(("http://", "https://")):
        return target
    return f"https://{target}"


def open_url_in_chrome(url: str) -> str:
    """Open a URL in Chrome when available, otherwise use the default browser."""
    chrome_paths = [
        Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
        Path(r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"),
        Path(os.environ.get("LOCALAPPDATA", "")) / r"Google\Chrome\Application\chrome.exe",
    ]

    chrome_from_path = shutil.which("chrome") or shutil.which("chrome.exe")
    if chrome_from_path:
        chrome_paths.insert(0, Path(chrome_from_path))

    for chrome_path in chrome_paths:
        if chrome_path.exists():
            try:
                subprocess.Popen([str(chrome_path), url])
                return "Chrome"
            except OSError:
                break

    webbrowser.open(url)
    return "your default browser"


def open_installed_app(target: str) -> Optional[str]:
    """Open a known or discovered installed Windows app."""
    normalized_target = normalize_app_target(target)
    command = APPS.get(normalized_target)
    display_name = get_display_name(normalized_target)

    if command and launch_app_command(command):
        return f"Opening {display_name}."

    for search_name in get_app_search_names(normalized_target):
        discovered_app = find_installed_app(search_name)
        if discovered_app and launch_path(discovered_app):
            return f"Opening {display_name}."

    return None


def normalize_app_target(target: str) -> str:
    """Normalize an app target name for app lookup."""
    target = re.sub(r"\s+", " ", target.strip().lower())
    return re.sub(r"\s+(app|application)$", "", target).strip()


def launch_app_command(command: str) -> bool:
    """Launch an app command safely without invoking a command shell."""
    command_path = shutil.which(command)
    try:
        if command_path:
            subprocess.Popen([command_path])
        else:
            subprocess.Popen([command])
        return True
    except (FileNotFoundError, OSError):
        return False


def get_app_search_names(app_name: str) -> List[str]:
    """Return app names and aliases to use while searching installed apps."""
    aliases = APP_SEARCH_ALIASES.get(app_name, ())
    return [app_name, *aliases]


def launch_path(path: Path) -> bool:
    """Open a discovered executable or shortcut path safely."""
    try:
        if path.suffix.lower() == ".lnk" and hasattr(os, "startfile"):
            os.startfile(str(path))
        else:
            subprocess.Popen([str(path)])
        return True
    except (OSError, FileNotFoundError):
        return False


def find_installed_app(app_name: str) -> Optional[Path]:
    """Search common Windows locations for a matching app shortcut or executable."""
    if os.name != "nt":
        return None

    search_roots = get_app_search_roots()
    app_terms = [term for term in re.split(r"\s+", app_name.lower()) if term]
    if not app_terms:
        return None

    for root in search_roots:
        match = find_app_in_root(root, app_terms)
        if match:
            return match

    return None


def get_app_search_roots() -> List[Path]:
    """Return bounded Windows locations for installed app discovery."""
    user_profile = Path(os.environ.get("USERPROFILE", ""))
    app_data = Path(os.environ.get("APPDATA", ""))
    local_app_data = Path(os.environ.get("LOCALAPPDATA", ""))

    roots = [
        Path(r"C:\ProgramData\Microsoft\Windows\Start Menu\Programs"),
        app_data / r"Microsoft\Windows\Start Menu\Programs",
        Path(os.environ.get("ProgramFiles", r"C:\Program Files")),
        Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")),
        local_app_data / "Programs",
        user_profile / r"AppData\Local\Programs",
    ]
    return [root for root in roots if root.exists()]


def find_app_in_root(root: Path, app_terms: List[str], max_depth: int = 4) -> Optional[Path]:
    """Find a likely app shortcut or executable under one root with bounded depth."""
    root_depth = len(root.parts)

    try:
        for current_root, dirs, files in os.walk(root):
            current_path = Path(current_root)
            if len(current_path.parts) - root_depth >= max_depth:
                dirs[:] = []

            for file_name in files:
                candidate = current_path / file_name
                if candidate.suffix.lower() not in {".lnk", ".exe"}:
                    continue

                if app_terms_match(candidate.stem, app_terms):
                    return candidate
    except (OSError, PermissionError):
        return None

    return None


def app_terms_match(candidate_name: str, app_terms: List[str]) -> bool:
    """Return True when every requested app term appears in the candidate name."""
    candidate = candidate_name.lower()
    return all(term in candidate for term in app_terms)


def get_display_name(target: str) -> str:
    """Return a clean display name for a website or app target."""
    target = strip_web_suffix(target)
    if "." in target:
        return get_domain_display(ensure_https_url(target))

    special_names = {
        "amazon": "Amazon",
        "vs code": "VS Code",
        "vscode": "VS Code",
        "github": "GitHub",
        "gmail": "Gmail",
        "chatgpt": "ChatGPT",
        "youtube": "YouTube",
        "whatsapp": "WhatsApp",
        "instagram": "Instagram",
        "facebook": "Facebook",
        "linkedin": "LinkedIn",
        "flipkart": "Flipkart",
        "x": "X",
    }
    return special_names.get(target, target.title())


def get_domain_display(url: str) -> str:
    """Return the display domain from a generated URL."""
    domain = re.sub(r"^https?://", "", url)
    domain = domain.removeprefix("www.")
    return domain.rstrip("/")


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


def show_main_menu() -> str:
    """Display the main mode menu and return the user's choice."""
    print()
    print(f"{Fore.CYAN}┌─ Select input mode ───────────┐{Style.RESET_ALL}")
    print(f"{Fore.CYAN}│  [1] Text Chat                │{Style.RESET_ALL}")
    print(f"{Fore.CYAN}│  [2] Voice Chat               │{Style.RESET_ALL}")
    print(f"{Fore.CYAN}│  [3] Exit                     │{Style.RESET_ALL}")
    print(f"{Fore.CYAN}└───────────────────────────────┘{Style.RESET_ALL}")
    return input("> ").strip()


def read_text_turn() -> Optional[str]:
    """Read a keyboard input turn."""
    raw = input("You: ").strip()
    return raw or None


def text_chat_loop(
    engine: Optional[Any],
    conversation_history: ConversationHistory,
    message_counter: List[int],
) -> str:
    """Run continuous text chat until the user changes mode or exits."""
    deliver_system_response(
        engine,
        "Text chat mode activated. Type 4 to change mode or type exit to quit.",
    )

    while True:
        user_text = read_text_turn()
        if not user_text:
            print_warn("No input detected. Please try again.")
            continue

        normalized = user_text.strip().lower()
        if normalized == "4":
            log_user_turn(user_text, message_counter)
            deliver_system_response(engine, "Returning to mode menu.")
            return CHANGE_MODE_TOKEN

        if normalized == "3":
            log_user_turn(user_text, message_counter)
            return EXIT_TOKEN

        result = handle_user_message(
            user_text,
            engine,
            conversation_history,
            message_counter,
        )
        if result == EXIT_TOKEN:
            return EXIT_TOKEN


def voice_chat_loop(
    engine: Optional[Any],
    recognizer: Optional[Any],
    conversation_history: ConversationHistory,
    message_counter: List[int],
) -> str:
    """Run push-to-talk voice chat until the user changes mode or exits."""
    show_available_microphones()
    microphone_index = get_microphone_device_index()

    if recognizer is None or not check_voice_available(microphone_index):
        no_microphone_message = (
            "No microphone input device was found. Please connect/enable a "
            "microphone or use text mode."
        )
        deliver_system_response(engine, no_microphone_message)
        deliver_system_response(
            engine,
            "Open Windows Settings > Privacy & security > Microphone and allow "
            "microphone access for desktop apps.",
        )
        return CHANGE_MODE_TOKEN

    deliver_system_response(
        engine,
        "Voice chat mode activated. Press Enter to push and talk, type 4 to "
        "change mode, or type exit to quit.",
    )
    print_warn(f"Using microphone: {get_microphone_label(microphone_index)}")

    while True:
        voice_action = read_voice_chat_action()
        if is_change_mode_command(voice_action):
            deliver_system_response(engine, "Returning to mode menu.")
            return CHANGE_MODE_TOKEN

        if is_exit_command(voice_action):
            return EXIT_TOKEN

        if voice_action:
            print_warn("Invalid voice chat option. Press Enter, type 4, or type exit.")
            continue

        user_text = listen_to_voice(recognizer, microphone_index)
        if not user_text:
            continue

        if user_text == EXIT_TOKEN:
            return EXIT_TOKEN

        if user_text == CHANGE_MODE_TOKEN:
            deliver_system_response(engine, "Returning to mode menu.")
            return CHANGE_MODE_TOKEN

        normalized = user_text.strip().lower()
        if is_change_mode_command(normalized):
            log_user_turn(user_text, message_counter)
            deliver_system_response(engine, "Returning to mode menu.")
            return CHANGE_MODE_TOKEN

        result = handle_user_message(
            user_text,
            engine,
            conversation_history,
            message_counter,
        )
        if result == EXIT_TOKEN:
            return EXIT_TOKEN


def read_voice_chat_action() -> str:
    """Read the push-to-talk voice chat control command."""
    print()
    print(f"{Fore.CYAN}Voice controls:{Style.RESET_ALL}")
    print(f"{Fore.CYAN}  [Enter] Push to talk{Style.RESET_ALL}")
    print(f"{Fore.CYAN}  [4] Change mode{Style.RESET_ALL}")
    print(f"{Fore.CYAN}  [3] Exit{Style.RESET_ALL}")
    return input("Voice> ").strip().lower()


def handle_user_message(
    user_input: str,
    engine: Optional[Any],
    conversation_history: ConversationHistory,
    message_counter: List[int],
) -> str:
    """Generate, print, speak, and log the chatbot response for one user input."""
    log_user_turn(user_input, message_counter)

    local_response = get_local_response(user_input)
    if local_response == EXIT_TOKEN:
        return EXIT_TOKEN

    conversation_history.append({"role": "user", "content": user_input})

    if local_response:
        response = local_response
    else:
        response = get_ai_response(conversation_history)

    conversation_history.append({"role": "assistant", "content": response})
    deliver_response(engine, response)
    return "continue"


def log_user_turn(user_input: str, message_counter: List[int]) -> None:
    """Log one user turn and update the message counter."""
    log("User", user_input)
    message_counter[0] += 1


def is_change_mode_command(text: str) -> bool:
    """Return True when a voice/text command asks to return to the mode menu."""
    return text in {"4", "four", "change mode", "switch mode"} or (
        "change mode" in text or "switch mode" in text
    )


def is_exit_command(text: str) -> bool:
    """Return True when a command asks to exit the program."""
    return text in {"3", "exit", "quit", "bye", "goodbye", "stop"}


def _contains_word(text: str, words: tuple) -> bool:
    """Return True when text contains any whole word from words."""
    return any(re.search(rf"\b{re.escape(word)}\b", text) for word in words)


def main() -> None:
    """Run the JARVIS chatbot."""
    configure_console()
    init(autoreset=True)
    print(BANNER)

    engine = init_tts()
    recognizer = sr.Recognizer() if sr is not None else None

    greeting = (
        f"Hello {config.USER_NAME}, I am {config.JARVIS_NAME}. "
        "How can I assist you today?"
    )
    log_divider("SESSION STARTED")
    deliver_response(engine, greeting)

    conversation_history: ConversationHistory = []
    message_counter = [0]

    while True:
        choice = show_main_menu()

        if choice == "3":
            break

        if choice == "1":
            result = text_chat_loop(engine, conversation_history, message_counter)
        elif choice == "2":
            result = voice_chat_loop(
                engine,
                recognizer,
                conversation_history,
                message_counter,
            )
        else:
            deliver_system_response(engine, "Invalid option. Choose 1, 2, or 3.")
            continue

        if result == EXIT_TOKEN:
            break

    farewell = (
        f"Session complete. We exchanged {message_counter[0]} messages. "
        f"Goodbye, {config.USER_NAME}. Have a productive day."
    )
    print()
    deliver_response(engine, farewell)
    log_divider("SESSION ENDED")


if __name__ == "__main__":
    main()
