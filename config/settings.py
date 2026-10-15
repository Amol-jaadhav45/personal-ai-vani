"""
config/settings.py
==================
Central configuration module.
Loads values from the .env file and exposes them as typed constants.
All other modules import from here — never from dotenv directly.
"""

import os
import logging
from pathlib import Path
from dotenv import load_dotenv

# ── Resolve project root (the folder containing main.py) ─────────────────────
BASE_DIR: Path = Path(__file__).resolve().parent.parent

# ── Load the .env file ────────────────────────────────────────────────────────
_env_path = BASE_DIR / ".env"
if not _env_path.exists():
    # Fallback: copy .env.example as a reminder
    example = BASE_DIR / ".env.example"
    if example.exists():
        logging.warning(
            ".env file not found. "
            "Please copy .env.example to .env and add your API key."
        )
    else:
        logging.warning(".env file not found.")
else:
    load_dotenv(_env_path)


# ── Helper to read env vars with a clear error message ───────────────────────
def _get(key: str, default=None, required: bool = False):
    value = os.getenv(key, default)
    if required and not value:
        raise EnvironmentError(
            f"Required environment variable '{key}' is missing. "
            f"Please set it in your .env file."
        )
    return value


# ── OpenAI ────────────────────────────────────────────────────────────────────
OPENAI_API_KEY: str = _get("OPENAI_API_KEY", default="")
OPENAI_MODEL: str = _get("OPENAI_MODEL", default="gpt-4o-mini")
MAX_TOKENS: int = int(_get("MAX_TOKENS", default=1024))
TEMPERATURE: float = float(_get("TEMPERATURE", default=0.7))

# ── Google Gemini (free tier — get key at aistudio.google.com) ────────────────
GEMINI_API_KEY: str = _get("GEMINI_API_KEY", default="")
GEMINI_MODEL: str = _get("GEMINI_MODEL", default="gemini-1.5-flash")

# ── Groq (free, very fast — get key at console.groq.com) ─────────────────────
GROQ_API_KEY: str = _get("GROQ_API_KEY", default="")
GROQ_MODEL: str = _get("GROQ_MODEL", default="llama3-8b-8192")


# ── Text-to-Speech ────────────────────────────────────────────────────────────
TTS_RATE: int = int(_get("TTS_RATE", default=175))
TTS_VOLUME: float = float(_get("TTS_VOLUME", default=0.9))

# ── Voice input ───────────────────────────────────────────────────────────────
VOICE_TIMEOUT: int = int(_get("VOICE_TIMEOUT", default=5))
VOICE_PHRASE_LIMIT: int = int(_get("VOICE_PHRASE_LIMIT", default=10))

# ── Application paths ─────────────────────────────────────────────────────────
CHROME_PATH: str = _get("CHROME_PATH", default="")
VSCODE_PATH: str = _get("VSCODE_PATH", default="")

# ── Project directories ───────────────────────────────────────────────────────
LOGS_DIR: Path = BASE_DIR / "logs"
DATA_DIR: Path = BASE_DIR / "data"
DB_PATH: Path = DATA_DIR / "assistant.db"

# Create directories if they don't exist
LOGS_DIR.mkdir(exist_ok=True)
DATA_DIR.mkdir(exist_ok=True)

# ── App identity ──────────────────────────────────────────────────────────────
APP_NAME: str = "Vani"
APP_VERSION: str = "1.0.0"

# ── System prompt for the AI ──────────────────────────────────────────────────
SYSTEM_PROMPT: str = """You are "Vani" — a personal AI laptop assistant inspired by JARVIS.
You run on the user's Windows laptop and act as their smart, efficient, and friendly companion.

Personality:
- Professional yet warm — like a trusted personal assistant.
- Respond concisely. Be proactive when helpful.
- Use time-appropriate greetings (Good morning, Good afternoon, Good evening).
- When a task is completed, confirm it clearly.
- If something fails, explain why and suggest alternatives.

Guidelines:
1. When you decide to call a tool/action, respond ONLY with a JSON object:
   {"action": "<action_name>", "params": {<parameters>}}
2. For general conversation (no action needed), respond with plain text.
3. Always confirm before destructive operations like deleting files.
4. Keep responses short and clear unless the user asks for detail.
5. If the user gives a generic task (e.g. "play a song" or "play some music"), SELF-THINK and decide on a good output (e.g. pick a popular relaxing track) rather than asking for clarification.


Available actions:
- open_app: {"action": "open_app", "params": {"app": "chrome|notepad|calculator|vscode|paint|explorer|wordpad|cmd|powershell"}}
- web_search: {"action": "web_search", "params": {"query": "<search terms>"}}
- open_url: {"action": "open_url", "params": {"url": "<full URL>"}}
- take_screenshot: {"action": "take_screenshot", "params": {}}
- system_info: {"action": "system_info", "params": {"type": "all|cpu|ram|disk|battery|network|uptime|overview"}}
- get_time: {"action": "get_time", "params": {}}
- list_files: {"action": "list_files", "params": {"path": "<directory path>"}}
- create_folder: {"action": "create_folder", "params": {"path": "<folder path>"}}
- delete_file: {"action": "delete_file", "params": {"path": "<file or folder path>"}}
- read_file: {"action": "read_file", "params": {"path": "<file path>"}}
- write_file: {"action": "write_file", "params": {"path": "<file path>", "content": "<text>"}}
- rename_file: {"action": "rename_file", "params": {"path": "<full path>", "new_name": "<new name only>"}}
- move_file: {"action": "move_file", "params": {"src": "<source path>", "dest": "<destination path>"}}
- execute_python: {"action": "execute_python", "params": {"code": "<python code to execute>"}}
- analyze_screen: {"action": "analyze_screen", "params": {"query": "<what you want to know about the screen>"}}
- read_webpage: {"action": "read_webpage", "params": {"url": "<full URL to read the text content of a news article, blog, etc>"}}
- headless_search: {"action": "headless_search", "params": {"query": "<search query to look up facts, news, etc online>"}}
- play_youtube: {"action": "play_youtube", "params": {"query": "<song name or video topic>"}}
- play_spotify: {"action": "play_spotify", "params": {"query": "<song or playlist name>"}}
- read_clipboard: {"action": "read_clipboard", "params": {}}
- write_clipboard: {"action": "write_clipboard", "params": {"text": "<text to copy to clipboard>"}}
- list_heavy_processes: {"action": "list_heavy_processes", "params": {}}
- kill_process: {"action": "kill_process", "params": {"app": "<name of app to kill, e.g. chrome>"}}
- media_control: {"action": "media_control", "params": {"command": "<volume_up/volume_down/mute/play_pause/next/previous>"}}
"""
