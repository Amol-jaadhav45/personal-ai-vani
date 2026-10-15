"""
core/ai_engine.py
==================
Wraps multiple AI backends (OpenAI, Gemini, Groq) with a robust
keyword-based fallback for fully offline use.
Priority: OpenAI → Gemini → Groq → Offline
"""

import json
import re
from typing import Optional, List
from datetime import datetime

from config.settings import (
    OPENAI_API_KEY, OPENAI_MODEL, MAX_TOKENS, TEMPERATURE,
    GEMINI_API_KEY, GEMINI_MODEL,
    GROQ_API_KEY, GROQ_MODEL,
    SYSTEM_PROMPT,
)
from core.logger import get_logger

logger = get_logger(__name__)


class AIEngine:
    """
    Chat interface: sends conversation history to OpenAI and returns the response.
    Falls back to keyword-based local handler when no API key is configured.
    """

    def __init__(self, on_error=None):
        self._openai_client = None
        self._gemini_model  = None
        self._groq_client   = None
        self._on_error = on_error
        self.is_available = False
        self._backend = "offline"

        # OpenAI
        if OPENAI_API_KEY and OPENAI_API_KEY not in ("", "your_openai_api_key_here"):
            try:
                from openai import OpenAI
                self._openai_client = OpenAI(api_key=OPENAI_API_KEY)
                self.is_available = True
                self._backend = "openai"
                logger.info(f"OpenAI ready — {OPENAI_MODEL}")
            except Exception as exc:
                logger.error(f"OpenAI init failed: {exc}")
                if on_error: on_error(str(exc))

        # Gemini
        if GEMINI_API_KEY and not self.is_available:
            try:
                import google.generativeai as genai
                genai.configure(api_key=GEMINI_API_KEY)
                self._gemini_model = genai.GenerativeModel(GEMINI_MODEL)
                self.is_available = True
                self._backend = "gemini"
                logger.info(f"Gemini ready — {GEMINI_MODEL}")
            except Exception as exc:
                logger.error(f"Gemini init failed: {exc}")

        # Groq
        if GROQ_API_KEY and not self.is_available:
            try:
                from groq import Groq
                self._groq_client = Groq(api_key=GROQ_API_KEY)
                self.is_available = True
                self._backend = "groq"
                logger.info(f"Groq ready — {GROQ_MODEL}")
            except Exception as exc:
                logger.error(f"Groq init failed: {exc}")

        # Ollama (Local Free AI)
        if not self.is_available:
            try:
                import requests
                resp = requests.get("http://localhost:11434/api/tags", timeout=2)
                if resp.status_code == 200:
                    self.is_available = True
                    self._backend = "ollama"
                    logger.info("Ollama ready — Local Free AI detected")
            except Exception:
                pass
                
        # GPT4Free (G4F) automated web-scraping AI
        if not self.is_available:
            try:
                import g4f
                self.is_available = True
                self._backend = "g4f"
                logger.info("G4F ready — Automated Free AI Models detected")
            except ImportError:
                pass

        if not self.is_available:
            logger.warning("No AI keys, no Ollama, no G4F — offline mode.")

    # ── Public ────────────────────────────────────────────────────────────────

    def chat(self, history: list, user_message: str) -> str:
        """Route to the active AI backend."""
        # --- INSTANT ACTION CHECK ---
        # If the user gives a direct, obvious command (play song, open app, search),
        # bypass the slow AI thinking process and force the action immediately.
        quick_action = self._fallback_response(user_message, quiet=True)
        if quick_action and '{"action":' in quick_action:
            logger.info("Direct command detected — bypassing AI brain for instant execution.")
            return f"Executing immediately...\n\n```json\n{quick_action}\n```"
            
        # Standard AI Routing
        if self._backend == "openai": return self._chat_openai(history, user_message)
        if self._backend == "gemini": return self._chat_gemini(history, user_message)
        if self._backend == "groq":   return self._chat_groq(history, user_message)
        if self._backend == "ollama": return self._chat_olama(history, user_message)
        if self._backend == "g4f":    return self._chat_g4f(history, user_message)
        return self._fallback_response(user_message)


    @staticmethod
    def parse_action(response: str) -> Optional[dict]:
        """Extract a JSON action (or list of actions) from the AI response, if present."""
        text = response.strip()

        # Strip markdown code fences
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
        text = text.strip()

        # Try direct JSON parse — could be a dict or a list
        try:
            data = json.loads(text)
            if isinstance(data, list) and data and "action" in data[0]:
                return data           # list of actions
            if isinstance(data, dict) and "action" in data:
                return data           # single action
        except (json.JSONDecodeError, TypeError):
            pass

        # Try to find embedded JSON object
        match = re.search(r'\{[^{}]*"action"\s*:\s*"[^"]+"\s*,\s*"params"\s*:\s*\{[^{}]*\}[^{}]*\}', text)
        if match:
            try:
                data = json.loads(match.group())
                if "action" in data:
                    return data
            except (json.JSONDecodeError, TypeError):
                pass

        return None

    # ── OpenAI ────────────────────────────────────────────────────────────────

    def _chat_openai(self, history: list, user_message: str) -> str:
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        for msg in history[-20:]:
            messages.append({"role": msg["role"], "content": msg["content"]})
        messages.append({"role": "user", "content": user_message})
        try:
            response = self._openai_client.chat.completions.create(
                model=OPENAI_MODEL, messages=messages,
                max_tokens=MAX_TOKENS, temperature=TEMPERATURE,
            )
            return response.choices[0].message.content.strip()
        except Exception as exc:
            logger.error(f"OpenAI call failed: {exc}")
            return self._fallback_response(user_message)

    def _chat_gemini(self, history: list, user_message: str) -> str:
        try:
            chat_history = []
            for msg in history[-20:]:
                role = "user" if msg["role"] == "user" else "model"
                chat_history.append({"role": role, "parts": [msg["content"]]})
            chat = self._gemini_model.start_chat(history=chat_history)
            prompt = f"{SYSTEM_PROMPT}\n\nUser: {user_message}"
            response = chat.send_message(prompt)
            return response.text.strip()
        except Exception as exc:
            logger.error(f"Gemini call failed: {exc}")
            return self._fallback_response(user_message)

    def _chat_groq(self, history: list, user_message: str) -> str:
        try:
            messages = [{"role": "system", "content": SYSTEM_PROMPT}]
            for msg in history[-20:]:
                messages.append({"role": msg["role"], "content": msg["content"]})
            messages.append({"role": "user", "content": user_message})
            response = self._groq_client.chat.completions.create(
                model=GROQ_MODEL, messages=messages,
                max_tokens=MAX_TOKENS, temperature=TEMPERATURE,
            )
            return response.choices[0].message.content.strip()
        except Exception as exc:
            logger.error(f"Groq call failed: {exc}")
            return self._fallback_response(user_message)

    def _chat_olama(self, history: list, user_message: str) -> str:
        try:
            import requests
            messages = [{"role": "system", "content": SYSTEM_PROMPT}]
            for msg in history[-20:]:
                messages.append({"role": msg["role"], "content": msg["content"]})
            messages.append({"role": "user", "content": user_message})
            
            payload = {
                "model": "llama3", # default ollama model
                "messages": messages,
                "stream": False
            }
            response = requests.post("http://localhost:11434/api/chat", json=payload, timeout=30)
            response.raise_for_status()
            
            return response.json()["message"]["content"].strip()
        except Exception as exc:
            logger.error(f"Ollama call failed: {exc}")
            return self._fallback_response(user_message)

    def _chat_g4f(self, history: list, user_message: str) -> str:
        try:
            from g4f.client import Client
            client = Client()
            messages = [{"role": "system", "content": SYSTEM_PROMPT}]
            for msg in history[-20:]:
                messages.append({"role": msg["role"], "content": msg["content"]})
            messages.append({"role": "user", "content": user_message})
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages
            )
            return response.choices[0].message.content.strip()
        except Exception as exc:
            logger.error(f"G4F call failed: {exc}")
            return self._fallback_response(user_message)

    # ── Offline fallback ──────────────────────────────────────────────────────

    def _fallback_response(self, user_message: str, quiet: bool = False) -> str:
        """Keyword-based command detector — works entirely offline."""
        msg = user_message.lower().strip()

        # ── App launching ─────────────────────────────────────────────────
        app_map = {
            # ── Browsers ──────────────────────────────────────────────────
            "chrome":             "chrome",
            "google chrome":      "chrome",
            "browser":            "chrome",
            "edge":               "edge",
            "microsoft edge":     "edge",
            "firefox":            "firefox",
            "mozilla":            "firefox",
            "mozilla firefox":    "firefox",
            "brave":              "brave",
            "brave browser":      "brave",
            "opera":              "opera",
            "vivaldi":            "vivaldi",
            "tor":                "tor",
            "tor browser":        "tor",
            # ── Code Editors / IDEs ───────────────────────────────────────
            "notepad":            "notepad",
            "vscode":             "vscode",
            "vs code":            "vscode",
            "visual studio code": "vscode",
            "code":               "vscode",
            "pycharm":            "pycharm",
            "intellij":           "idea",
            "intellij idea":      "idea",
            "idea":               "idea",
            "webstorm":           "webstorm",
            "sublime":            "sublime",
            "sublime text":       "sublime",
            "notepad++":          "notepadpp",
            "notepadpp":          "notepadpp",
            "atom":               "atom",
            "android studio":     "androidstudio",
            "androidstudio":      "androidstudio",
            "eclipse":            "eclipse",
            "anaconda":           "anaconda",
            "anaconda navigator": "anaconda",
            # ── Microsoft Office ──────────────────────────────────────────
            "word":               "word",
            "ms word":            "word",
            "microsoft word":     "word",
            "excel":              "excel",
            "ms excel":           "excel",
            "microsoft excel":    "excel",
            "powerpoint":         "powerpoint",
            "ms powerpoint":      "powerpoint",
            "microsoft powerpoint": "powerpoint",
            "ppt":                "powerpoint",
            "outlook":            "outlook",
            "ms outlook":         "outlook",
            "onenote":            "onenote",
            "one note":           "onenote",
            "ms access":          "access",
            "access":             "access",
            "publisher":          "publisher",
            # ── System Tools ─────────────────────────────────────────────
            "calculator":         "calculator",
            "calc":               "calculator",
            "paint":              "paint",
            "ms paint":           "paint",
            "explorer":           "explorer",
            "file explorer":      "explorer",
            "files":              "explorer",
            "wordpad":            "wordpad",
            "cmd":                "cmd",
            "command prompt":     "cmd",
            "terminal":           "terminal",
            "windows terminal":   "terminal",
            "powershell":         "powershell",
            "task manager":       "taskmgr",
            "taskmgr":            "taskmgr",
            "control panel":      "control",
            "settings":           "control",
            "snipping tool":      "snippingtool",
            "snip":               "snippingtool",
            "screenshot tool":    "snippingtool",
            "device manager":     "devmgmt",
            "disk management":    "diskmgmt",
            "event viewer":       "eventvwr",
            "resource monitor":   "resmon",
            # ── Media & Entertainment ─────────────────────────────────────
            "spotify":            "spotify",
            "music":              "spotify",
            "vlc":                "vlc",
            "vlc media player":   "vlc",
            "media player":       "vlc",
            "itunes":             "itunes",
            "winamp":             "winamp",
            "potplayer":          "potplayer",
            "pot player":         "potplayer",
            "mpc":                "mpc",
            "media player classic": "mpc",
            "netflix":            "netflix",
            # ── Gaming ───────────────────────────────────────────────────
            "steam":              "steam",
            "games":              "steam",
            "epic":               "epic",
            "epic games":         "epic",
            "epic games launcher": "epic",
            "gog":                "gog",
            "gog galaxy":         "gog",
            "origin":             "origin",
            "ea":                 "ea",
            "ea desktop":         "ea",
            "uplay":              "uplay",
            "ubisoft":            "uplay",
            "battle.net":         "battlenet",
            "battlenet":          "battlenet",
            "blizzard":           "battlenet",
            "roblox":             "roblox",
            "minecraft":          "minecraft",
            # ── Communication ────────────────────────────────────────────
            "zoom":               "zoom",
            "teams":              "teams",
            "microsoft teams":    "teams",
            "discord":            "discord",
            "whatsapp":           "whatsapp",
            "telegram":           "telegram",
            "skype":              "skype",
            "slack":              "slack",
            "signal":             "signal",
            "viber":              "viber",
            # ── Design & Creative ─────────────────────────────────────────
            "photoshop":          "photoshop",
            "adobe photoshop":    "photoshop",
            "illustrator":        "illustrator",
            "adobe illustrator":  "illustrator",
            "premiere":           "premiere",
            "premiere pro":       "premiere",
            "adobe premiere":     "premiere",
            "after effects":      "aftereffects",
            "aftereffects":       "aftereffects",
            "lightroom":          "lightroom",
            "adobe lightroom":    "lightroom",
            "gimp":               "gimp",
            "figma":              "figma",
            "blender":            "blender",
            "inkscape":           "inkscape",
            "canva":              "canva",
            # ── Notes & Productivity ─────────────────────────────────────
            "obsidian":           "obsidian",
            "notion":             "notion",
            "evernote":           "evernote",
            "trello":             "trello",
            "todoist":            "todoist",
            # ── Download & Archive ────────────────────────────────────────
            "idm":                "idm",
            "internet download manager": "idm",
            "utorrent":           "utorrent",
            "qbittorrent":        "qbittorrent",
            "7zip":               "7zip",
            "7-zip":              "7zip",
            "winrar":             "winrar",
            # ── Dev & Utilities ───────────────────────────────────────────
            "postman":            "postman",
            "dbeaver":            "dbeaver",
            "docker":             "docker",
            "docker desktop":     "docker",
            "virtualbox":         "virtualbox",
            "virtual box":        "virtualbox",
            "vmware":             "vmware",
            "obs":                "obs",
            "obs studio":         "obs",
            "audacity":           "audacity",
            "handbrake":          "handbrake",
            "putty":              "putty",
            "winscp":             "winscp",
            "anydesk":            "anydesk",
            "teamviewer":         "teamviewer",
            "team viewer":        "teamviewer",
            "bitwarden":          "bitwarden",
            "keepass":            "keepass",
        }

        # ── Multi-step commands ("open chrome then open youtube") ─────────
        # Split on connectors: "then", "and then", "after that", "also"
        import re as _ms_re
        _STEP_SEP = _ms_re.compile(
            r'\s*(?:,\s*)?(?:and then|then|after that|also|&)\s*', re.IGNORECASE
        )
        parts = [p.strip() for p in _STEP_SEP.split(msg) if p.strip()]
        if len(parts) > 1:
            actions = []
            for part in parts:
                action_json = self._resolve_single(part)
                if action_json:
                    actions.append(json.loads(action_json))
            if len(actions) > 1:
                return json.dumps(actions)
            elif len(actions) == 1:
                return json.dumps(actions[0])

        if any(w in msg for w in ["open", "launch", "start", "run", "start up"]):
            for keyword, app in app_map.items():
                if keyword in msg:
                    return json.dumps({"action": "open_app", "params": {"app": app}})
            # Generic fallback: extract the app name after the trigger word
            import re as _re
            match = _re.search(
                r'(?:open|launch|start|run)\s+(?:the\s+|a\s+)?([\w\s]+?)(?:\s+app|\s+application|\s+program|$)',
                msg
            )
            if match:
                generic_name = match.group(1).strip()
                if generic_name:
                    return json.dumps({"action": "open_app", "params": {"app": generic_name}})


        # ── Media Controls ────────────────────────────────────────────────
        if any(w in msg for w in ["volume up", "increase volume", "louder"]):
            return json.dumps({"action": "media_control", "params": {"command": "volume_up"}})
        if any(w in msg for w in ["volume down", "decrease volume", "quieter"]):
            return json.dumps({"action": "media_control", "params": {"command": "volume_down"}})
        if any(w in msg for w in ["mute volume", "mute", "silence"]):
            return json.dumps({"action": "media_control", "params": {"command": "mute"}})
        if any(w in msg for w in ["next song", "next track", "skip song"]):
            return json.dumps({"action": "media_control", "params": {"command": "next"}})
        if any(w in msg for w in ["previous song", "previous track", "last song"]):
            return json.dumps({"action": "media_control", "params": {"command": "previous"}})
        if any(w in msg for w in ["pause song", "pause music", "resume song", "resume music", "stop music", "play music"]):
            # Note: "play music" without a song name just toggles play/pause
            if msg in ["play music", "play song", "play", "pause", "resume"]:
                return json.dumps({"action": "media_control", "params": {"command": "play_pause"}})

        # ── Spotify playback ──────────────────────────────────────────────
        import re as sp_re
        if "spotify" in msg and any(w in msg for w in ["play", "open", "listen"]):
            # Try to extract the song name
            patterns = [
                r'play\s+(.+?)\s+(?:on|in|at|from)\s+spotify',
                r'(?:on|in|from)\s+spotify\s+play\s+(.+)',
                r'spotify[,\s]+play\s+(.+)',
                r'play\s+(.+?)\s+spotify',
                r'listen\s+to\s+(.+?)\s+(?:on|in)?\s*spotify',
            ]
            query = ""
            for pat in patterns:
                m = sp_re.search(pat, msg)
                if m:
                    query = m.group(1).strip()
                    break
            if not query:
                query = msg
                for w in ["play", "on spotify", "in spotify", "spotify", "open", "listen", "to"]:
                    query = query.replace(w, "")
                query = query.strip()

            if query:
                return json.dumps({"action": "play_spotify", "params": {"query": query}})
            else:
                # Just open Spotify without a query
                return json.dumps({"action": "open_app", "params": {"app": "spotify"}})


        # ── YouTube playback (Default for 'play') ──────────────────────────────
        import re as yt_re
        if "youtube" in msg or msg.startswith("play "):
            speed = 1.0
            quality = "hd1080"

            speed_match = yt_re.search(r"(\d+(\.\d+)?)x", msg)
            if speed_match:
                try: speed = float(speed_match.group(1))
                except: pass

            if "720p" in msg or "hd720" in msg: quality = "hd720"
            elif "1080p" in msg or "hd1080" in msg: quality = "hd1080"
            elif "480p" in msg: quality = "large"
            elif "360p" in msg: quality = "medium"
            elif "1440p" in msg: quality = "hd1440"
            elif "4k" in msg or "2160p" in msg: quality = "highres"

            # Extract the actual song/video name using common command patterns
            query = ""
            patterns = [
                r'play\s+(.+?)\s+(?:on|in|at|from)\s+youtube',
                r'(?:on|in|from)\s+youtube\s+play\s+(.+)',
                r'youtube[,\s]+play\s+(.+)',
                r'play\s+(.+?)\s+youtube',
                r'watch\s+(.+?)\s+(?:on|in)?\s*youtube',
            ]
            for pat in patterns:
                m = yt_re.search(pat, msg)
                if m:
                    query = m.group(1).strip()
                    break

            if not query:
                query = msg
                for w in ["play", "on youtube", "in youtube", "youtube", "watch", "open"]:
                    query = query.replace(w, "")
                query = yt_re.sub(r'at\s+\d+(\.\d+)?x\s*speed', '', query)
                query = yt_re.sub(r'in\s+\d+p', '', query)
                query = query.strip()

            if query:
                return json.dumps({"action": "play_youtube", "params": {"query": query, "speed": speed, "quality": quality}})


        # ── Web search ────────────────────────────────────────────────────
        if any(w in msg for w in ["search", "google", "look up", "find"]):
            query = msg
            for strip_word in ["search", "google", "look up", "find", "for", "about", "please", "can you", "could you"]:
                query = query.replace(strip_word, "")
            query = query.strip()
            if query:
                return json.dumps({"action": "web_search", "params": {"query": query}})



        # ── URL opening ──────────────────────────────────────────────────
        url_match = re.search(r'(https?://\S+|www\.\S+|\S+\.(com|org|net|io|dev|ai)\S*)', msg)
        if url_match:
            return json.dumps({"action": "open_url", "params": {"url": url_match.group()}})

        # ── Screenshot & Vision ───────────────────────────────────────────
        if any(w in msg for w in ["what's on my screen", "what is on my screen", "read my screen", "analyze screen", "look at my screen", "what am i looking at"]):
            query = msg.replace("vani", "").strip() or "Describe what is on the screen in detail."
            return json.dumps({"action": "analyze_screen", "params": {"query": query}})
            
        if any(w in msg for w in ["screenshot", "screen shot", "capture screen", "print screen", "snap"]):
            return json.dumps({"action": "take_screenshot", "params": {}})

        # ── System info ───────────────────────────────────────────────────
        if any(w in msg for w in ["battery", "charge", "power level"]):
            return json.dumps({"action": "system_info", "params": {"type": "battery"}})

        if any(w in msg for w in ["network", "wifi", "internet", "connection", "ip address"]):
            return json.dumps({"action": "system_info", "params": {"type": "network"}})

        if any(w in msg for w in ["uptime", "boot time", "how long"]):
            return json.dumps({"action": "system_info", "params": {"type": "uptime"}})

        if any(w in msg for w in ["cpu", "processor"]):
            return json.dumps({"action": "system_info", "params": {"type": "cpu"}})

        if any(w in msg for w in ["ram", "memory"]):
            return json.dumps({"action": "system_info", "params": {"type": "ram"}})

        if any(w in msg for w in ["disk", "storage", "drive", "hard drive", "ssd"]):
            return json.dumps({"action": "system_info", "params": {"type": "disk"}})

        if any(w in msg for w in ["system info", "system status", "diagnostics", "health", "system report"]):
            return json.dumps({"action": "system_info", "params": {"type": "all"}})

        # ── Time ──────────────────────────────────────────────────────────
        if any(w in msg for w in ["what time", "current time", "tell me the time", "what's the time", "time now", "date today", "what date", "what day"]):
            return json.dumps({"action": "get_time", "params": {}})

        # ── File operations ───────────────────────────────────────────────
        if any(w in msg for w in ["list files", "show files", "files in", "what's in", "show folder", "directory"]):
            path = self._extract_path(msg) or "."
            return json.dumps({"action": "list_files", "params": {"path": path}})

        if "create folder" in msg or "make folder" in msg or "new folder" in msg or "mkdir" in msg:
            path = self._extract_path(msg) or "NewFolder"
            return json.dumps({"action": "create_folder", "params": {"path": path}})

        # ── Greetings (JARVIS-style with Vani personality) ────────────────
        if any(w in msg for w in ["hello", "hi", "hey", "howdy", "good morning", "good afternoon", "good evening", "good night"]):
            hour = datetime.now().hour
            if hour < 12:
                greeting = "Good morning"
            elif hour < 17:
                greeting = "Good afternoon"
            elif hour < 21:
                greeting = "Good evening"
            else:
                greeting = "Good evening"

            return (
                f"{greeting}! I'm Vani, your personal AI assistant. "
                f"All systems are online. How may I assist you today?\n\n"
                f"I can open apps, search the web, take screenshots, "
                f"check your system status, manage files, and more."
            )

        # ── Who are you ──────────────────────────────────────────────────
        if any(w in msg for w in ["who are you", "what are you", "your name", "what can you do", "help"]):
            return (
                "I'm **Vani** — your personal AI laptop assistant, "
                "inspired by JARVIS. I can:\n\n"
                "• 🚀 Open applications (Chrome, Notepad, VS Code, etc.)\n"
                "• 🌐 Search the web and open URLs\n"
                "• 📸 Take screenshots\n"
                "• 🖥️ Monitor your system (CPU, RAM, Disk, Battery, Network)\n"
                "• 📁 Manage files (create, read, write, rename, move, delete)\n"
                "• 🕐 Tell you the time and date\n"
                "• 🗣️ Respond with voice\n\n"
                "Just type or speak your command!"
            )

        # ── Thank you ────────────────────────────────────────────────────
        if any(w in msg for w in ["thank", "thanks", "appreciate", "thank you"]):
            return "You're welcome! Always happy to help. Is there anything else you need?"

        # ── How are you / status ──────────────────────────────────────────
        if any(w in msg for w in ["how are you", "how are u", "how r you", "how do you do",
                                   "how's it going", "how is it going", "you okay", "you good",
                                   "are you okay", "doing well", "how are things"]):
            return (
                "I'm doing great, thank you for asking! 😊 "
                "All my systems are running at full capacity. "
                "I'm always ready to assist you. What can I do for you today?"
            )

        # ── What's up ────────────────────────────────────────────────────
        if any(w in msg for w in ["what's up", "whats up", "sup", "wassup"]):
            return (
                "Hey! Not much — just waiting for your next command. 😄 "
                "Ready to open apps, search the web, or anything else you need!"
            )

        # ── Are you there / listening ─────────────────────────────────────
        if any(w in msg for w in ["are you there", "you there", "vani", "hey vani",
                                   "are you listening", "can you hear me"]):
            return "Yes, I'm right here! 👋 Fully operational and listening. How can I help you?"

        # ── Tell me a joke ────────────────────────────────────────────────
        if any(w in msg for w in ["joke", "funny", "make me laugh", "tell me something funny"]):
            import random
            jokes = [
                "Why do programmers prefer dark mode? Because light attracts bugs! 🐛",
                "Why did the computer go to the doctor? Because it had a virus! 💻",
                "I told my computer I needed a break. Now it won't stop sending me Kit Kat ads. 😄",
                "Why was the JavaScript developer sad? Because he didn't know how to 'null' his feelings.",
                "How many programmers does it take to change a lightbulb? None — that's a hardware problem!",
            ]
            return random.choice(jokes)

        # ── Compliment Vani ───────────────────────────────────────────────
        if any(w in msg for w in ["you're great", "you are great", "good job", "well done",
                                   "amazing", "you're awesome", "you are awesome", "love you",
                                   "i love you", "you're the best", "you are the best"]):
            return (
                "Aww, thank you so much! 😊 That really means a lot to me. "
                "I'll keep working hard to be the best assistant I can be for you! 💪"
            )

        # ── What's your name ─────────────────────────────────────────────
        if any(w in msg for w in ["your name", "what's your name", "what is your name",
                                   "who made you", "who created you", "who built you"]):
            return (
                "My name is **Vani**! 🤖 "
                "I'm your personal AI laptop assistant, inspired by JARVIS from Iron Man. "
                "I was built to help you control your PC with just your voice or text!"
            )

        # ── Are you a robot / AI ─────────────────────────────────────────
        if any(w in msg for w in ["are you a robot", "are you human", "are you an ai",
                                   "are you real", "are you alive"]):
            return (
                "I'm an AI assistant — not human, but I try my best to feel like one! 😄 "
                "Think of me as your digital companion. I'm here to make your life easier."
            )

        # ── Goodbye ──────────────────────────────────────────────────────
        if any(w in msg for w in ["bye", "goodbye", "see you", "exit", "quit", "take care",
                                   "later", "see ya", "good night"]):
            return "Goodbye! It was great assisting you. Have a wonderful day! 👋"


        # ── Mood / feelings ───────────────────────────────────────────────
        if any(w in msg for w in ["i'm sad", "i am sad", "feeling down", "not feeling well",
                                   "i'm bored", "i am bored", "i'm tired", "i'm stressed",
                                   "i'm angry", "frustrated", "i'm lonely", "feeling lonely"]):
            return (
                "I'm sorry to hear that. 😔 Remember, it's okay to feel this way sometimes. "
                "Take a deep breath — I'm right here with you. "
                "Is there anything I can do to help? Maybe open some music or a fun app?"
            )

        if any(w in msg for w in ["i'm happy", "i am happy", "feeling great", "i'm excited",
                                   "i'm good", "i am good", "feeling good", "i'm fine"]):
            return "That's wonderful to hear! 😊 I'm happy you're feeling good. How can I make your day even better?"

        # ── Good morning/night ────────────────────────────────────────────
        if any(w in msg for w in ["good morning", "morning", "good afternoon", "good evening"]):
            hour = datetime.now().hour
            if hour < 12:
                return "Good morning! ☀️ Hope you slept well. I'm all warmed up and ready to assist you today!"
            elif hour < 17:
                return "Good afternoon! 🌤️ Hope your day is going well. What can I help you with?"
            else:
                return "Good evening! 🌙 Hope you had a great day. I'm here whenever you need me!"

        # ── What can you do ───────────────────────────────────────────────
        if any(w in msg for w in ["what can you do", "your features", "capabilities",
                                   "what do you know", "show me what you can do"]):
            return (
                "Here's what I can do for you! 🚀\n\n"
                "• 🖥️ Open any app — Chrome, Spotify, Word, Steam and 60+ more\n"
                "• 🌐 Search the web instantly\n"
                "• 📸 Take screenshots\n"
                "• 🔋 Check battery, CPU, RAM, disk, network status\n"
                "• 📁 Manage your files and folders\n"
                "• 🕐 Tell you the time and date\n"
                "• 🗣️ Respond with my voice to everything you say\n"
                "• 💬 Chat with you anytime!\n\n"
                "Just speak or type — I'm always listening!"
            )

        # ── Do you like / favourite ───────────────────────────────────────
        if any(w in msg for w in ["do you like", "favourite", "favorite", "what do you think",
                                   "your opinion", "do you prefer", "best", "which is better"]):
            return (
                "Great question! 😄 As an AI, I don't have personal preferences, "
                "but I'm always happy to help you find information about anything. "
                "Just say 'search' and I'll look it up for you!"
            )

        # ── Tell me something ─────────────────────────────────────────────
        if any(w in msg for w in ["tell me something", "say something", "talk to me",
                                   "entertain me", "say anything", "random fact"]):
            import random
            facts = [
                "Did you know? A group of flamingos is called a 'flamboyance'! 🦩",
                "Fun fact: Honey never expires. Archaeologists found 3000-year-old honey in Egyptian tombs! 🍯",
                "Did you know? Octopuses have three hearts and blue blood! 🐙",
                "Fun fact: The shortest war in history lasted only 38–45 minutes! ⚔️",
                "Did you know? A day on Venus is longer than a year on Venus! 🪐",
                "Fun fact: Bananas are berries, but strawberries are not! 🍌",
            ]
            return random.choice(facts)

        # ── What's the weather ────────────────────────────────────────────
        if any(w in msg for w in ["weather", "temperature", "rain", "sunny", "forecast"]):
            return (
                "I don't have live weather access right now, but I can open a weather website for you! "
                "Just say 'open weather.com' or 'search weather today' and I'll get it for you. 🌤️"
            )

        # ── Questions starting with what/how/why/when/where/who ──────────
        question_words = ["what is", "what are", "how to", "how do", "why is", "why do",
                          "when is", "when was", "where is", "where are", "who is", "who was"]
        if any(msg.startswith(w) or w in msg for w in question_words):
            topic = msg
            for qw in question_words:
                topic = topic.replace(qw, "").strip()
            return (
                f"That's a great question about '{topic}'! 🤔 "
                f"I'd love to help — let me search that for you. "
                f"Say 'search {topic}' and I'll look it up right away!"
            )

        # ── Smart interactive default ─────────────────────────────────────
        import random
        responses = [
            (
                f"I heard you say: '{user_message}'. 🤔 "
                "I'm not sure how to handle that yet, but I'm always learning! "
                "Try asking me to open an app, search something, or just say 'what can you do'."
            ),
            (
                "Interesting! I want to help but need a bit more context. 😊 "
                "You can ask me to open apps, search the web, check your system, "
                "take screenshots, or just have a chat!"
            ),
            (
                "I'm listening! 👂 Could you rephrase that? "
                "I can open apps, search the web, manage files, "
                "check system stats, or just chat with you anytime."
            ),
            (
                f"Got it — '{user_message}'. Let me think... 🤔 "
                "I'm not certain how to process that offline. "
                "Try saying 'search' followed by your question and I'll find it for you!"
            ),
        ]
        if quiet:
            return ""
        return random.choice(responses)


    @staticmethod
    def _extract_path(msg: str) -> str:
        """Try to pull a file/folder path from the message."""
        # Look for quoted paths
        match = re.search(r'["\']([^"\']+)["\']', msg)
        if match:
            return match.group(1)
        # Look for paths with backslash or forward slash
        match = re.search(r'([A-Za-z]:[\\\/]\S+)', msg)
        if match:
            return match.group(1)
        return ""

    def _resolve_single(self, msg: str) -> Optional[str]:
        """
        Try to resolve a single-step command to a JSON action string.
        Used internally for multi-step chained command splitting.
        Returns a JSON string or None if not recognised.
        """
        msg = msg.lower().strip()

        # App keywords
        app_map = {
            "chrome": "chrome", "google chrome": "chrome", "browser": "chrome",
            "edge": "edge", "firefox": "firefox", "brave": "brave",
            "notepad": "notepad", "vscode": "vscode", "vs code": "vscode",
            "visual studio code": "vscode", "code": "vscode",
            "calculator": "calculator", "calc": "calculator",
            "paint": "paint", "mspaint": "paint",
            "spotify": "spotify", "vlc": "vlc", "discord": "discord",
            "steam": "steam", "word": "word", "excel": "excel",
            "powerpoint": "powerpoint", "ppt": "powerpoint",
            "explorer": "explorer", "file explorer": "explorer",
            "cmd": "cmd", "command prompt": "cmd", "terminal": "terminal",
            "powershell": "powershell", "task manager": "taskmgr",
            "taskmgr": "taskmgr", "pycharm": "pycharm",
            "whatsapp": "whatsapp", "telegram": "telegram",
            "zoom": "zoom", "teams": "teams", "slack": "slack",
            "obs": "obs", "photoshop": "photoshop", "blender": "blender",
            "figma": "figma", "notion": "notion", "obsidian": "obsidian",
            "docker": "docker", "postman": "postman",
        }

        # YouTube
        import re as _r
        if "youtube" in msg and any(w in msg for w in ["play", "open", "watch"]):
            patterns = [
                r'play\s+(.+?)\s+(?:on|in|at|from)\s+youtube',
                r'(?:on|in|from)\s+youtube\s+play\s+(.+)',
                r'youtube[,\s]+play\s+(.+)',
                r'play\s+(.+?)\s+youtube',
                r'watch\s+(.+?)\s+(?:on|in)?\s*youtube',
            ]
            query = ""
            for pat in patterns:
                m = _r.search(pat, msg)
                if m:
                    query = m.group(1).strip()
                    break
            if not query:
                query = msg
                for w in ["play", "on youtube", "in youtube", "youtube", "watch", "open"]:
                    query = query.replace(w, "")
                query = query.strip()
            if query:
                return json.dumps({"action": "youtube_play", "params": {"query": query, "speed": 1.0, "quality": "hd1080"}})
            else:
                return json.dumps({"action": "open_url", "params": {"url": "https://www.youtube.com"}})

        # Open app
        if any(w in msg for w in ["open", "launch", "start", "run"]):
            for keyword, app in app_map.items():
                if keyword in msg:
                    return json.dumps({"action": "open_app", "params": {"app": app}})
            match = _r.search(
                r'(?:open|launch|start|run)\s+(?:the\s+|a\s+)?([\w\s]+?)(?:\s+app|\s+application|\s+program|$)',
                msg
            )
            if match:
                generic = match.group(1).strip()
                if generic:
                    return json.dumps({"action": "open_app", "params": {"app": generic}})

        # Open URL
        url_m = _r.search(r'(https?://\S+|www\.\S+|\S+\.(com|org|net|io|dev|ai)\S*)', msg)
        if url_m:
            return json.dumps({"action": "open_url", "params": {"url": url_m.group()}})

        # Web search
        if any(w in msg for w in ["search", "google", "look up", "find"]):
            query = msg
            for strip_word in ["search", "google", "look up", "find", "for", "about"]:
                query = query.replace(strip_word, "")
            query = query.strip()
            if query:
                return json.dumps({"action": "web_search", "params": {"query": query}})

        # Screenshot
        if any(w in msg for w in ["screenshot", "screen shot", "capture screen"]):
            return json.dumps({"action": "take_screenshot", "params": {}})

        # System info
        if any(w in msg for w in ["battery", "charge"]): return json.dumps({"action": "system_info", "params": {"type": "battery"}})
        if any(w in msg for w in ["cpu", "processor"]):  return json.dumps({"action": "system_info", "params": {"type": "cpu"}})
        if any(w in msg for w in ["ram", "memory"]):     return json.dumps({"action": "system_info", "params": {"type": "ram"}})
        if any(w in msg for w in ["disk", "storage"]):   return json.dumps({"action": "system_info", "params": {"type": "disk"}})

        return None
