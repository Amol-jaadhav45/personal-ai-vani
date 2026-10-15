"""
gui/main_window.py  (v2 — enhanced)
=====================================
Root application window with:
  - Sidebar: branding, live system stats, chat history
  - Chat panel: styled message bubbles
  - Input bar: text entry + mic button + send button (with listening indicator)
  - Settings tab: theme toggle, TTS rate/volume, voice on/off
  - Activity log tab: real-time tool/action log
  - AI processing indicator
"""

import threading
import customtkinter as ctk
from tkinter import messagebox

from gui.styles import COLORS, FONTS, SIZES
from gui.chat_panel import ChatPanel
from gui.sidebar import Sidebar

from core.ai_engine import AIEngine
from core.command_dispatcher import CommandDispatcher
from core.memory import Memory
from voice.text_to_speech import TextToSpeech
from voice.speech_to_text import SpeechToText
from config.settings import APP_NAME, APP_VERSION
from core.logger import get_logger

logger = get_logger(__name__)

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class MainWindow(ctk.CTk):
    """Top-level application window."""

    def __init__(self):
        super().__init__()
        logger.info("Initialising MainWindow…")

        # ── Window ────────────────────────────────────────────────────────────
        self.title(f"{APP_NAME} v{APP_VERSION}")
        self.geometry("1200x740")
        self.minsize(SIZES["window_min_w"], SIZES["window_min_h"])
        self.configure(fg_color=COLORS["bg_darkest"])

        # ── Core services ─────────────────────────────────────────────────────
        self._memory     = Memory()
        self._ai         = AIEngine(on_error=self._on_ai_error)
        self._dispatcher = CommandDispatcher(confirm_callback=self._confirm_dialog)
        self._tts        = TextToSpeech()
        self._stt        = SpeechToText()

        # ── State ─────────────────────────────────────────────────────────────
        self._session_id: str = self._memory.new_session("Welcome Chat")
        self._processing = False
        self._mic_active = False
        self._tts_enabled = True      # master TTS on/off
        self._voice_only_tts = False  # False = always speak; True = speak only on mic input
        self._continuous_voice_active = False # True = loop mic after TTS
        self._wake_word_active = False        # True = listen passively for "Hey Vani"
        self._vani_sleeping = False           # True if currently waiting for wake word
        self._voice_triggered = False # True when last input came from mic
        self._current_tab = "chat"    # "chat" | "settings" | "log"
        self._activity_log_lines: list = []

        self._build_layout()
        self._start_session()

        self.protocol("WM_DELETE_WINDOW", self._on_close)
        
        # ── Autostart Wake Word ───────────────────────────────────────────────
        self.after(500, self._autostart_wake_word)
        
        logger.info("MainWindow ready.")

    def _autostart_wake_word(self):
        """Automatically turn on 'Hey Vani' when the app boots."""
        try:
            self._wake_word_switch.select()
            self._toggle_wake_word()
            # self._display_assistant_message("Listening for 'Hey Vani' automatically...", spoken="I am online and listening.")
        except Exception as e:
            logger.error(f"Failed to autostart wake word: {e}")

    # =========================================================================
    # Layout
    # =========================================================================

    def _build_layout(self):
        self._main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._main_frame.pack(fill="both", expand=True)

        # ── Sidebar ───────────────────────────────────────────────────────────
        self._sidebar = Sidebar(
            self._main_frame,
            on_new_chat=self._new_chat,
            on_clear_chat=self._clear_chat,
            on_session_select=self._load_session,
        )
        self._sidebar.pack(side="left", fill="y")

        # ── Content area ──────────────────────────────────────────────────────
        content = ctk.CTkFrame(self._main_frame, fg_color="transparent")
        content.pack(side="left", fill="both", expand=True)

        self._build_header(content)
        self._build_tab_bar(content)
        self._build_main_area(content)
        self._switch_tab("chat")     # activate after tabs + content are both built
        self._build_input_bar(content)

    # ── Header ────────────────────────────────────────────────────────────────

    def _build_header(self, parent):
        header = ctk.CTkFrame(
            parent, fg_color=COLORS["bg_dark"], height=52, corner_radius=0
        )
        header.pack(fill="x")
        header.pack_propagate(False)

        self._title_lbl = ctk.CTkLabel(
            header,
            text="💬  New Conversation",
            font=ctk.CTkFont(*FONTS["body_bold"]),
            text_color=COLORS["text_primary"],
        )
        self._title_lbl.pack(side="left", padx=20)

        # Processing spinner label
        self._status_lbl = ctk.CTkLabel(
            header,
            text="",
            font=ctk.CTkFont(*FONTS["small"]),
            text_color=COLORS["accent_yellow"],
        )
        self._status_lbl.pack(side="right", padx=8)

        # AI availability badge
        ai_status = "🟢 AI Connected" if self._ai.is_available else "🟡 Offline Mode"
        ai_color  = COLORS["accent_green"] if self._ai.is_available else COLORS["accent_yellow"]
        ctk.CTkLabel(
            header,
            text=ai_status,
            font=ctk.CTkFont(*FONTS["small"]),
            text_color=ai_color,
        ).pack(side="right", padx=12)

    # ── Tab bar ───────────────────────────────────────────────────────────────

    def _build_tab_bar(self, parent):
        bar = ctk.CTkFrame(parent, fg_color=COLORS["bg_dark"], height=40, corner_radius=0)
        bar.pack(fill="x")
        bar.pack_propagate(False)

        tab_cfg = [
            ("💬  Chat",     "chat"),
            ("⚙️  Settings", "settings"),
            ("📋  Activity", "log"),
        ]
        self._tab_buttons: dict = {}

        for label, name in tab_cfg:
            btn = ctk.CTkButton(
                bar,
                text=label,
                width=120,
                height=36,
                corner_radius=0,
                fg_color="transparent",
                hover_color=COLORS["bg_panel"],
                font=ctk.CTkFont(*FONTS["body"]),
                text_color=COLORS["text_secondary"],
                command=lambda n=name: self._switch_tab(n),
            )
            btn.pack(side="left", padx=2)
            self._tab_buttons[name] = btn

        # Note: _switch_tab("chat") is called AFTER _build_main_area in _build_layout

    # ── Tabbed content area ───────────────────────────────────────────────────

    def _build_main_area(self, parent):
        self._tab_container = ctk.CTkFrame(parent, fg_color="transparent")
        self._tab_container.pack(fill="both", expand=True)

        # ── Chat tab ──────────────────────────────────────────────────────────
        self._tab_chat = ctk.CTkFrame(self._tab_container, fg_color="transparent")
        self._chat = ChatPanel(self._tab_chat)
        self._chat.pack(fill="both", expand=True, padx=12, pady=6)

        # ── Settings tab ──────────────────────────────────────────────────────
        self._tab_settings = ctk.CTkFrame(
            self._tab_container, fg_color=COLORS["bg_panel"], corner_radius=12
        )
        self._build_settings_content(self._tab_settings)

        # ── Activity log tab ──────────────────────────────────────────────────
        self._tab_log = ctk.CTkFrame(self._tab_container, fg_color="transparent")
        self._build_log_content(self._tab_log)

    def _build_settings_content(self, parent):
        scroll = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=24, pady=16)

        def section(title):
            ctk.CTkLabel(
                scroll,
                text=title,
                font=ctk.CTkFont(*FONTS["body_bold"]),
                text_color=COLORS["accent"],
            ).pack(anchor="w", pady=(16, 4))
            ctk.CTkFrame(scroll, height=1, fg_color=COLORS["border"]).pack(
                fill="x", pady=(0, 8)
            )

        def row(label, widget_fn):
            row_f = ctk.CTkFrame(scroll, fg_color="transparent")
            row_f.pack(fill="x", pady=4)
            ctk.CTkLabel(
                row_f,
                text=label,
                font=ctk.CTkFont(*FONTS["body"]),
                text_color=COLORS["text_primary"],
                width=200,
                anchor="w",
            ).pack(side="left")
            widget_fn(row_f)

        # ── Appearance ────────────────────────────────────────────────────────
        section("🎨  Appearance")

        def _theme_toggle(row_f):
            self._theme_switch = ctk.CTkSwitch(
                row_f,
                text="Dark Mode",
                font=ctk.CTkFont(*FONTS["body"]),
                onvalue="dark",
                offvalue="light",
                command=self._toggle_theme,
            )
            self._theme_switch.select()   # default dark
            self._theme_switch.pack(side="left")

        row("Theme", _theme_toggle)

        # ── Voice / TTS ───────────────────────────────────────────────────────
        section("🔊  Voice & Speech")

        def _tts_toggle(row_f):
            self._tts_switch = ctk.CTkSwitch(
                row_f,
                text="Text-to-Speech",
                font=ctk.CTkFont(*FONTS["body"]),
                command=self._toggle_tts,
            )
            self._tts_switch.select()
            self._tts_switch.pack(side="left")

        row("Enable TTS", _tts_toggle)

        def _voice_only_toggle(row_f):
            self._voice_only_switch = ctk.CTkSwitch(
                row_f,
                text="Mic input only",
                font=ctk.CTkFont(*FONTS["body"]),
                command=self._toggle_voice_only,
            )
            # default OFF = always speak
            self._voice_only_switch.pack(side="left")

        row("Speak on mic input only", _voice_only_toggle)

        def _continuous_voice_toggle(row_f):
            self._continuous_voice_switch = ctk.CTkSwitch(
                row_f,
                text="Enable real-time conversation",
                font=ctk.CTkFont(*FONTS["body"]),
                command=self._toggle_continuous_voice,
            )
            self._continuous_voice_switch.pack(side="left")

        row("Continuous Voice Mode", _continuous_voice_toggle)

        def _wake_word_toggle(row_f):
            self._wake_word_switch = ctk.CTkSwitch(
                row_f,
                text="Enable \"Hey Vani\" tracking",
                font=ctk.CTkFont(*FONTS["body"]),
                command=self._toggle_wake_word,
            )
            self._wake_word_switch.pack(side="left")

        row("Wake Word Mode", _wake_word_toggle)

        def _rate_slider(row_f):
            self._rate_lbl = ctk.CTkLabel(
                row_f,
                text="175 wpm",
                font=ctk.CTkFont(*FONTS["small"]),
                text_color=COLORS["text_muted"],
                width=70,
            )
            slider = ctk.CTkSlider(
                row_f,
                from_=80,
                to=280,
                number_of_steps=40,
                command=self._on_rate_change,
                width=200,
            )
            slider.set(175)
            slider.pack(side="left", padx=(0, 8))
            self._rate_lbl.pack(side="left")

        row("Speech Rate", _rate_slider)

        def _vol_slider(row_f):
            self._vol_lbl = ctk.CTkLabel(
                row_f,
                text="90%",
                font=ctk.CTkFont(*FONTS["small"]),
                text_color=COLORS["text_muted"],
                width=40,
            )
            slider = ctk.CTkSlider(
                row_f,
                from_=0,
                to=1,
                number_of_steps=20,
                command=self._on_vol_change,
                width=200,
            )
            slider.set(0.9)
            slider.pack(side="left", padx=(0, 8))
            self._vol_lbl.pack(side="left")

        row("Volume", _vol_slider)

        # ── AI ────────────────────────────────────────────────────────────────
        section("🧠  AI Engine")

        def _model_info(row_f):
            from config.settings import OPENAI_MODEL
            ctk.CTkLabel(
                row_f,
                text=OPENAI_MODEL if self._ai.is_available else "Offline (no API key)",
                font=ctk.CTkFont(*FONTS["body"]),
                text_color=COLORS["accent_green"] if self._ai.is_available else COLORS["accent_yellow"],
            ).pack(side="left")

        row("Active Model", _model_info)

        def _api_status(row_f):
            status = "Connected ✅" if self._ai.is_available else "Not configured ⚠️"
            ctk.CTkLabel(
                row_f,
                text=status,
                font=ctk.CTkFont(*FONTS["body"]),
                text_color=COLORS["text_primary"],
            ).pack(side="left")

        row("API Status", _api_status)

        # ── About ─────────────────────────────────────────────────────────────
        section("ℹ️  About")

        from config.settings import APP_NAME as N, APP_VERSION as V
        ctk.CTkLabel(
            scroll,
            text=f"{N}  v{V}\n\nBuilt with Python · CustomTkinter · OpenAI",
            font=ctk.CTkFont(*FONTS["body"]),
            text_color=COLORS["text_secondary"],
            justify="left",
        ).pack(anchor="w", pady=4)

    def _build_log_content(self, parent):
        header = ctk.CTkFrame(parent, fg_color="transparent")
        header.pack(fill="x", padx=12, pady=(8, 4))

        ctk.CTkLabel(
            header,
            text="📋  Tool & Activity Log",
            font=ctk.CTkFont(*FONTS["body_bold"]),
            text_color=COLORS["text_primary"],
        ).pack(side="left")

        ctk.CTkButton(
            header,
            text="Clear Log",
            width=90,
            height=28,
            fg_color=COLORS["bg_card"],
            hover_color=COLORS["accent_red"],
            font=ctk.CTkFont(*FONTS["small"]),
            command=self._clear_log,
        ).pack(side="right")

        self._log_box = ctk.CTkTextbox(
            parent,
            fg_color=COLORS["bg_dark"],
            text_color=COLORS["text_primary"],
            font=ctk.CTkFont(*FONTS["mono"]),
            corner_radius=8,
            state="disabled",
        )
        self._log_box.pack(fill="both", expand=True, padx=12, pady=(0, 8))

    # ── Input bar ─────────────────────────────────────────────────────────────

    def _build_input_bar(self, parent):
        bar = ctk.CTkFrame(parent, fg_color=COLORS["bg_dark"], corner_radius=0)
        bar.pack(fill="x")

        inner = ctk.CTkFrame(bar, fg_color="transparent")
        inner.pack(fill="x", padx=16, pady=12)

        self._input_entry = ctk.CTkEntry(
            inner,
            placeholder_text="Type a command or ask anything…",
            height=SIZES["input_height"],
            corner_radius=SIZES["corner_radius"],
            font=ctk.CTkFont(*FONTS["body"]),
            fg_color=COLORS["bg_input"],
            border_color=COLORS["border"],
            text_color=COLORS["text_primary"],
            placeholder_text_color=COLORS["text_muted"],
        )
        self._input_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self._input_entry.bind("<Return>", lambda _: self._send_message())
        self._input_entry.bind("<FocusIn>",  lambda _: self._input_entry.configure(border_color=COLORS["border_focus"]))
        self._input_entry.bind("<FocusOut>", lambda _: self._input_entry.configure(border_color=COLORS["border"]))

        # Mic button
        self._mic_btn = ctk.CTkButton(
            inner,
            text="🎤",
            width=SIZES["input_height"],
            height=SIZES["input_height"],
            corner_radius=SIZES["corner_radius"],
            fg_color=COLORS["bg_card"],
            hover_color=COLORS["accent"],
            font=ctk.CTkFont("Segoe UI Emoji", 18),
            command=self._toggle_mic,
        )
        self._mic_btn.pack(side="left", padx=(0, 8))

        # Send button
        self._send_btn = ctk.CTkButton(
            inner,
            text="Send  ➤",
            height=SIZES["input_height"],
            corner_radius=SIZES["corner_radius"],
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            font=ctk.CTkFont(*FONTS["body_bold"]),
            command=self._send_message,
        )
        self._send_btn.pack(side="left")

    # =========================================================================
    # Tab switching
    # =========================================================================

    def _switch_tab(self, name: str):
        """Show the selected tab, hide others."""
        # Unpack all tabs
        for tab in (self._tab_chat, self._tab_settings, self._tab_log):
            tab.pack_forget()

        # Update button highlight
        for n, btn in self._tab_buttons.items():
            if n == name:
                btn.configure(
                    fg_color=COLORS["bg_panel"],
                    text_color=COLORS["accent"],
                )
            else:
                btn.configure(
                    fg_color="transparent",
                    text_color=COLORS["text_secondary"],
                )

        # Pack the selected tab
        tab_map = {
            "chat":     self._tab_chat,
            "settings": self._tab_settings,
            "log":      self._tab_log,
        }
        tab_map[name].pack(fill="both", expand=True)
        self._current_tab = name

    # =========================================================================
    # Settings handlers
    # =========================================================================

    def _toggle_theme(self):
        mode = self._theme_switch.get()
        ctk.set_appearance_mode(mode)
        logger.info(f"Theme changed to: {mode}")

    def _toggle_tts(self):
        self._tts_enabled = bool(self._tts_switch.get())
        if not self._tts_enabled:
            self._tts.stop()
        logger.info(f"TTS enabled: {self._tts_enabled}")

    def _toggle_voice_only(self):
        self._voice_only_tts = bool(self._voice_only_switch.get())
        mode = "mic-only" if self._voice_only_tts else "always"
        logger.info(f"TTS mode: {mode}")

    def _toggle_continuous_voice(self):
        self._continuous_voice_active = bool(self._continuous_voice_switch.get())
        if self._continuous_voice_active and getattr(self, "_wake_word_active", False):
            self._wake_word_switch.deselect()
            self._toggle_wake_word()
        logger.info(f"Continuous voice mode: {self._continuous_voice_active}")

    def _toggle_wake_word(self):
        self._wake_word_active = bool(self._wake_word_switch.get())
        if self._wake_word_active:
            if getattr(self, "_continuous_voice_active", False):
                self._continuous_voice_switch.deselect()
                self._toggle_continuous_voice()
            self._vani_sleeping = True
            logger.info("Wake word mode ON. Vani is sleeping.")
            if not self._stt.is_listening:
                self._start_passive_listening()
        else:
            self._vani_sleeping = False
            logger.info("Wake word mode OFF.")
        
    def _start_passive_listening(self):
        """Starts STT in background for wake word, no overt GUI changes"""
        if self._stt.is_listening:
            return
        logger.info("VOICE: Started passive listening for wake word.")
        self._stt.listen(
            on_result=self._on_voice_result,
            on_error=self._on_voice_error_passive,
            on_start=self._on_mic_start_passive,
            on_stop=self._on_mic_stop_passive,
            on_level=None, # hide levels in passive mode
        )

    def _on_rate_change(self, val):
        rate = int(val)
        self._rate_lbl.configure(text=f"{rate} wpm")
        self._tts.set_rate(rate)

    def _on_vol_change(self, val):
        vol = round(float(val), 2)
        self._vol_lbl.configure(text=f"{int(vol * 100)}%")
        self._tts.set_volume(vol)

    # =========================================================================
    # Activity log
    # =========================================================================

    def _log_activity(self, message: str):
        """Append a timestamped line to the activity log."""
        from datetime import datetime
        ts = datetime.now().strftime("%H:%M:%S")
        line = f"[{ts}]  {message}\n"
        self._activity_log_lines.append(line)

        def _update():
            self._log_box.configure(state="normal")
            self._log_box.insert("end", line)
            self._log_box.yview_moveto(1.0)
            self._log_box.configure(state="disabled")

        self.after(0, _update)

    def _clear_log(self):
        self._log_box.configure(state="normal")
        self._log_box.delete("1.0", "end")
        self._log_box.configure(state="disabled")
        self._activity_log_lines.clear()

    # =========================================================================
    # Core interaction
    # =========================================================================

    def _start_session(self):
        from datetime import datetime
        hour = datetime.now().hour
        if hour < 12:
            greeting = "Good morning"
        elif hour < 17:
            greeting = "Good afternoon"
        elif hour < 21:
            greeting = "Good evening"
        else:
            greeting = "Good evening"

        welcome = (
            f"⚡ **{greeting}! I'm Vani** — your personal AI assistant.\n\n"
            f"All systems are online. Here's what I can do:\n\n"
            f"🚀 **Apps** — Open Chrome, Notepad, VS Code, Calculator\n"
            f"🌐 **Web** — Search Google, open any URL\n"
            f"📸 **Screenshot** — Capture your screen instantly\n"
            f"🖥️ **System** — CPU, RAM, Disk, Battery, Network status\n"
            f"📁 **Files** — Create, read, write, rename, move, delete\n"
            f"🕐 **Time** — Current date and time\n"
            f"🗣️ **Voice** — Click 🎤 to speak commands\n\n"
            f"Type or speak a command to begin."
        )
        if not self._ai.is_available:
            welcome += (
                "\n\n⚠️  **Offline Mode** — Running without API key.\n"
                "Core features work fully. Add OpenAI key to .env for AI conversations."
            )
        self._chat.add_message("assistant", welcome)
        # Only speak greeting if NOT in voice-only mode (greeting is typed-side)
        if not self._voice_only_tts:
            self._speak(f"{greeting}! I'm Vani, your personal AI assistant. All systems are online. How may I assist you?")
        self._refresh_history()
        self._log_activity("Session started — Vani ready.")

    def _send_message(self, voice: bool = False):
        text = self._input_entry.get().strip()
        if not text or self._processing:
            return
        self._input_entry.delete(0, "end")
        self._voice_triggered = voice   # track how this input arrived
        # Switch to chat tab if on another tab
        if self._current_tab != "chat":
            self._switch_tab("chat")
        self._display_user_message(text)
        self._process_input(text)

    def _display_user_message(self, text: str):
        self._chat.add_message("user", text)
        self._memory.save_message(self._session_id, "user", text)
        self._log_activity(f"USER: {text}")

    def _process_input(self, user_text: str):
        self._set_processing(True)
        threading.Thread(
            target=self._pipeline,
            args=(user_text,),
            daemon=True,
            name="AI-Pipeline",
        ).start()

    def _pipeline(self, user_text: str):
        try:
            # ── Check for stop voice loop command ────────────────────────────
            clean_input = user_text.lower().strip()
            if self._continuous_voice_active and any(w in clean_input for w in ["stop listening", "stop voice", "mute mic", "disable mic"]):
                self._continuous_voice_switch.deselect()
                self._toggle_continuous_voice()
                self._display_assistant_message("Continuous voice mode disabled.", spoken="I will stop listening now.")
                return
            if getattr(self, "_wake_word_active", False) and self._voice_triggered:
                if any(w in clean_input for w in ["stop listening", "go to sleep", "sleep"]):
                    self._vani_sleeping = True
                    self._display_assistant_message("Sleeping.", spoken="I'll be listening. Just say Hey Vani.")
                    self.after(1000, self._start_passive_listening)
                    return
                if any(w in clean_input for w in ["stop wake word", "disable wake word"]):
                    self._wake_word_switch.deselect()
                    self._toggle_wake_word()
                    self._display_assistant_message("Wake word tracking disabled.", spoken="Wake word disabled.")
                    return

            history = self._memory.get_messages(self._session_id, limit=20)
            
            # Fetch RAG Context
            rag_context = self._memory.search_rag(user_text)
            enriched_prompt = user_text
            if rag_context:
                enriched_prompt = f"{rag_context}\n\n[USER INPUT]: {user_text}"
                self._log_activity(f"RAG Context retrieved for query.")
                
            # ── Agentic Thinking Loop ─────────────────────────────────────────
            loops = 0
            MAX_LOOPS = 4
            current_prompt = enriched_prompt
            
            while loops < MAX_LOOPS:
                loops += 1
                history = self._memory.get_messages(self._session_id, limit=20)
                ai_response = self._ai.chat(history, current_prompt)
                action = AIEngine.parse_action(ai_response)
                
                # ── Handle multi-step actions (No looping for these) ─────────
                if isinstance(action, list):
                    results = []
                    for i, sub_action in enumerate(action):
                        action_name = sub_action.get("action", "unknown")
                        params      = sub_action.get("params", {})
                        self._log_activity(f"STEP {i+1} → {action_name}  params={params}")
    
                        success, result_msg = self._dispatcher.dispatch(sub_action)
                        spoken_line = self._action_to_speech(action_name, params, success, result_msg)
    
                        status = "✅" if success else "❌"
                        self._log_activity(f"STEP {i+1} RESULT {status}: {result_msg[:60]}")
                        results.append(f"{status} {result_msg}")
    
                        self._speak(spoken_line)
                        import time; time.sleep(1.5)
    
                    combined = "\n".join(results)
                    self._memory.save_message(self._session_id, "assistant", combined)
                    break # exit loop
    
                # ── Handle single action ──────────────────────────────────────
                if action:
                    action_name = action.get("action", "unknown")
                    params      = action.get("params", {})
                    self._log_activity(f"TOOL CALL → {action_name}  params={params}")
    
                    success, result_msg = self._dispatcher.dispatch(action)
                    status = "✅" if success else "❌"
                    self._log_activity(f"TOOL RESULT {status}: {result_msg[:80]}")
                    
                    # Agentic Loop condition: Information tools feed back to AI!
                    info_tools = ["headless_search", "read_webpage", "analyze_screen", "execute_python"]
                    if action_name in info_tools:
                        self._log_activity(f"Agentic loop: Thinking about {action_name} results...")
                        
                        # Save the AI's internal thought (its tool call) to memory
                        self._memory.save_message(self._session_id, "assistant", f"I used {action_name} to check.")
                        self._memory.save_message(self._session_id, "user", f"Tool output:\n{result_msg}")
                        
                        # Set prompt to trigger next loop
                        current_prompt = "Based on this, what is the answer?"
                        continue # Loop again!
                    
                    # For normal tools, just finish
                    spoken = self._action_to_speech(action_name, params, success, result_msg)
                    display_text = result_msg
                    self._memory.save_message(self._session_id, "assistant", display_text)
                    self.after(0, lambda dt=display_text, sp=spoken: self._display_assistant_message(dt, sp, on_finish=None))
                    break # exit loop
                
                # ── Plain text response ───────────────────────────────────────
                else:
                    display_text = ai_response
                    self._log_activity(f"AI TEXT: {ai_response[:80]}")
                    self._memory.save_message(self._session_id, "assistant", display_text)
                    
                    # Callbacks for voice mode loops
                    on_finish = None
                    if getattr(self, "_wake_word_active", False) and self._voice_triggered:
                        on_finish = lambda: self._put_to_sleep()
                    elif getattr(self, "_continuous_voice_active", False) and self._voice_triggered:
                        on_finish = lambda: self.after(500, self._toggle_mic)
                        
                    self.after(0, lambda dt=display_text: self._display_assistant_message(dt, None, on_finish=on_finish))
                    break # exit loop

        except Exception as exc:
            err = f"❌ Error: {exc}"
            logger.error(err, exc_info=True)
            self._log_activity(f"ERROR: {exc}")
            
            on_finish = None
            if getattr(self, "_wake_word_active", False) and self._voice_triggered:
                on_finish = lambda: self._put_to_sleep()
            elif getattr(self, "_continuous_voice_active", False) and self._voice_triggered:
                on_finish = lambda: self.after(500, self._toggle_mic)
                
            self.after(0, lambda: self._display_assistant_message(err, "Sorry, something went wrong.", on_finish=on_finish))
        finally:
            self.after(0, lambda: self._set_processing(False))
    
    def _put_to_sleep(self):
        """Put Vani back in passive wake word mode"""
        self._vani_sleeping = True
        self.after(500, self._start_passive_listening)


    def _display_assistant_message(self, text: str, spoken: str = None, on_finish: callable = None):
        """Show a chat bubble and optionally speak the result."""
        self._chat.add_message("assistant", text)

        # ── Decide whether to speak ──────────────────────────────────────────
        # voice-only mode  → speak only when input came from mic
        # TTS-always mode  → always speak
        should_speak = self._tts_enabled and (
            not self._voice_only_tts or self._voice_triggered
        )
        if not should_speak:
            if on_finish:
                on_finish()
            return

        if spoken:
            self._speak(spoken, on_finish=on_finish)
        else:
            clean = (
                text.replace("**", "").replace("*", "")
                    .replace("#", "").replace("_", "")
                    .replace("❌", "Error:").replace("✅", "")
                    .strip()
            )
            if len(clean) <= 400:
                self._speak(clean, on_finish=on_finish)
            else:
                first = clean.split(".")[0].strip()
                if first:
                    self._speak(first + ".", on_finish=on_finish)
                else:
                    if on_finish: on_finish()

    @staticmethod
    def _action_to_speech(action: str, params: dict, success: bool, result_msg: str) -> str:
        """
        Convert a tool action result into a natural spoken sentence.
        Called from the background thread; must not touch any GUI widgets.
        """
        if not success:
            # Strip emoji from error message for clean TTS
            clean = result_msg.replace("❌", "").strip()
            return f"Sorry, I couldn’t complete that. {clean}"

        app_names = {
            "chrome":     "Google Chrome",
            "notepad":    "Notepad",
            "calculator": "Calculator",
            "vscode":     "Visual Studio Code",
            "paint":      "Paint",
            "explorer":   "File Explorer",
            "wordpad":    "WordPad",
            "cmd":        "Command Prompt",
            "powershell": "PowerShell",
        }

        import random
        if action == "open_app":
            app = params.get("app", "the application")
            name = app_names.get(app.lower(), app.capitalize())
            choices = [
                f"{name} is now open.",
                f"Right away. Opening {name}.",
                f"Sure thing, I've launched {name} for you.",
                f"{name} is ready.",
                f"I have opened {name}."
            ]
            return random.choice(choices)

        elif action == "web_search":
            query = params.get("query", "your search")
            choices = [
                f"Searching the web for {query}.",
                f"I'm looking that up for you now: {query}.",
                f"Let me find that for you. Searching for {query}.",
                f"Checking the web for {query}."
            ]
            return random.choice(choices)

        elif action == "open_url":
            url = params.get("url", "the website")
            choices = [
                f"Opening {url} in your browser.",
                f"Navigating to {url} right now.",
                f"Taking you to {url}."
            ]
            return random.choice(choices)

        elif action == "take_screenshot":
            choices = [
                "Screenshot taken and saved to your Desktop.",
                "I've captured your screen and saved it.",
                "Snap! Screenshot saved to the Desktop."
            ]
            return random.choice(choices)

        elif action == "system_info":
            info_type = params.get("type", "all")
            speech_map = {
                "cpu":      ["Here is your CPU usage.", "Checking your processor now.", "Here's the data on your CPU."],
                "ram":      ["Here is your RAM usage.", "Checking your memory status.", "Memory stats retrieved."],
                "disk":     ["Here is your disk usage.", "Checking storage space.", "Here is your hard drive status."],
                "battery":  ["Here is your battery status.", "Checking power level.", "Here is the current battery level."],
                "network":  ["Here is your network status.", "Checking internet connection.", "Network stats are ready."],
                "uptime":   ["Here is your system uptime.", "Here's how long the system has been running."],
                "overview": ["Here is your system overview.", "System summary is ready."],
                "all":      ["Here is your complete system report.", "Gathering all system diagnostic data now."]
            }
            options = speech_map.get(info_type, ["Here is your system information."])
            return random.choice(options)

        elif action == "get_time":
            return result_msg.replace("🕕", "").replace("Current date and time:", "The current time is").strip()

        elif action == "create_folder":
            path = params.get("path", "the folder")
            choices = [
                f"Folder created at {path}.",
                f"I've made a new folder called {path}.",
                f"Done. The directory {path} has been created."
            ]
            return random.choice(choices)

        elif action == "write_file":
            path = params.get("path", "the file")
            choices = [
                f"File saved at {path}.",
                f"I've successfully written to {path}.",
                f"Done. The file {path} is saved."
            ]
            return random.choice(choices)

        elif action == "read_file":
            path = params.get("path", "the file")
            choices = [
                f"Here are the contents of {path}.",
                f"I've read the file {path}."
            ]
            return random.choice(choices)

        elif action == "list_files":
            path = params.get("path", "the folder")
            return f"Here are the files in {path}."

        elif action == "delete_file":
            path = params.get("path", "the item")
            return f"Deleted {path}."

        elif action == "rename_file":
            old = params.get("path", "the file")
            new = params.get("new_name", "")
            return f"Renamed to {new}."

        elif action == "move_file":
            dest = params.get("dest", "the destination")
            return f"File moved to {dest}."

        # Generic fallback
        return result_msg.replace("✅", "").replace("❌", "").strip()

    def _speak(self, text: str, on_finish: callable = None):
        if self._tts_enabled:
            self._tts.speak(text, on_finish=on_finish)
        else:
            if on_finish:
                on_finish()

    # =========================================================================
    # Microphone / STT
    # =========================================================================

    def _toggle_mic(self):
        if self._mic_active:
            return

        if not self._stt.is_available:
            messagebox.showwarning(
                "Voice Unavailable",
                "Audio backend not found.\n"
                "Run: pip install sounddevice soundfile SpeechRecognition",
            )
            return

        self._log_activity("VOICE: Microphone opened.")
        self._stt.listen(
            on_result=self._on_voice_result,
            on_error=self._on_voice_error,
            on_start=self._on_mic_start,
            on_stop=self._on_mic_stop,
            on_level=self._on_mic_level,
        )

    def _on_mic_start(self):
        self._mic_active = True
        self.after(0, lambda: self._mic_btn.configure(
            text="🔴", fg_color=COLORS["accent_red"]
        ))
        self.after(0, lambda: self._input_entry.configure(
            placeholder_text="🎤 Listening… speak now!"
        ))
        self.after(0, lambda: self._status_lbl.configure(text="🎙️ Listening…"))

    def _on_mic_stop(self):
        self._mic_active = False
        self.after(0, lambda: self._mic_btn.configure(
            text="🎤", fg_color=COLORS["bg_card"]
        ))
        self.after(0, lambda: self._input_entry.configure(
            placeholder_text="Type a command or ask anything…"
        ))
        self.after(0, lambda: self._status_lbl.configure(text=""))

    def _on_mic_level(self, level: float):
        """Called repeatedly with mic volume 0.0–1.0. Shows audio bars on button."""
        # Pick a bar indicator based on level
        if level < 0.05:
            icon = "🎤"
        elif level < 0.25:
            icon = "🔈"
        elif level < 0.6:
            icon = "🔉"
        else:
            icon = "🔊"
        self.after(0, lambda i=icon: self._mic_btn.configure(text=i))

    def _on_voice_result(self, text: str):
        self._log_activity(f"VOICE RECOGNISED: {text}")
        self.after(0, lambda: self._on_voice_result_gui(text))

    def _on_voice_result_gui(self, text: str):
        if getattr(self, "_wake_word_active", False) and self._vani_sleeping:
            clean = text.lower().strip()
            # Catch variations of "Vani"
            wake_words = [
                "vani", "hey vani", "funny", "bonnie", "fannie", "bunny", "honey", "money", "dani",
                "bhiwani", "avani", "shivani", "himani", "deewani", "sherwani", "bhawani", "devani",
                "hawani", "jawani", "pawani", "nani"
            ]
            if any(w in clean for w in wake_words):
                # Awaken! Play sound.
                import platform
                if platform.system() == "Windows":
                    import winsound
                    # Play pleasant chime
                    try: winsound.MessageBeep(winsound.MB_ICONASTERISK)
                    except: pass
                
                self._vani_sleeping = False
                self.after(0, lambda: self._status_lbl.configure(text=""))
                self.after(0, lambda: self._mic_btn.configure(text="🎤", fg_color=COLORS["bg_card"]))
                
                # Check if there is command text after the wake word
                command = ""
                for wv in wake_words:
                    if wv in clean:
                        command = clean.split(wv, 1)[-1].strip()
                        break
                
                # if there is a command immediately following, execute it!
                if command and len(command) > 2:
                    self._input_entry.insert("end", text) # log original phrase
                    self._send_message(voice=True)
                else:
                    self._display_assistant_message("Yes? How can I help?", spoken="Yes?")
                    # now awake, so automatically listen for actual command
                    self.after(800, self._toggle_mic)
                return
            else:
                # ignored background noise, stay asleep
                self.after(100, self._start_passive_listening)
                return

        self._input_entry.insert("end", text)
        self._send_message(voice=True)  # mark as voice-triggered so TTS responds

    def _start_passive_listening(self):
        if not self._stt.is_available or self._mic_active:
            return
        
        self._log_activity("VOICE: Passive wake word listening started.")
        self._stt.listen(
            on_result=self._on_voice_result,
            on_error=self._on_voice_error_passive,
            on_start=self._on_mic_start_passive,
            on_stop=self._on_mic_stop_passive,
            on_level=None
        )

    def _on_mic_start_passive(self):
        self._mic_active = True
        self.after(0, lambda: self._status_lbl.configure(text="💤 Sleeping (Listening for 'Hey Vani')"))
        self.after(0, lambda: self._mic_btn.configure(text="💭", fg_color=COLORS["accent_yellow"]))

    def _on_mic_stop_passive(self):
        self._mic_active = False

    def _on_voice_error_passive(self, message: str):
        # In passive mode, just quietly restart if we timed out
        if self._wake_word_active and self._vani_sleeping:
            self.after(200, self._start_passive_listening)


    def _on_voice_error(self, message: str):
        self._log_activity(f"VOICE ERROR: {message}")
        # Show in chat AND speak the error so the user knows what happened
        self.after(0, lambda: self._chat.add_message("assistant", message))
        clean = message.replace("❌", "").replace("⏱️", "").replace("🤔", "").strip()
        self._speak(clean)

    # =========================================================================
    # Session management
    # =========================================================================

    def _new_chat(self):
        self._session_id = self._memory.new_session("New Conversation")
        self._chat.clear()
        self._chat.add_system_message("New conversation started")
        self._start_session()
        self._title_lbl.configure(text="💬  New Conversation")
        self._log_activity("New conversation session created.")

    def _clear_chat(self):
        if messagebox.askyesno("Clear Chat", "Clear all messages from this chat?"):
            self._chat.clear()
            self._chat.add_system_message("Chat cleared")
            self._log_activity("Chat cleared by user.")

    def _load_session(self, session_id: str):
        messages = self._memory.get_messages(session_id, limit=50)
        self._session_id = session_id
        self._chat.clear()
        self._chat.add_system_message("Loaded previous conversation")
        for msg in messages:
            self._chat.add_message(msg["role"], msg["content"])
        self._switch_tab("chat")
        self._log_activity(f"Loaded session: {session_id[:8]}…")

    def _refresh_history(self):
        sessions = self._memory.get_all_sessions()
        self._sidebar.load_history(sessions)

    # =========================================================================
    # UI helpers
    # =========================================================================

    def _set_processing(self, busy: bool):
        self._processing = busy
        state = "disabled" if busy else "normal"
        self._send_btn.configure(
            text="⏳ Thinking…" if busy else "Send  ➤",
            state=state,
        )
        self._input_entry.configure(state=state)
        self._status_lbl.configure(
            text="⏳ Processing…" if busy else ""
        )

    def _confirm_dialog(self, message: str) -> bool:
        return messagebox.askyesno("⚠️ Confirm Action", message)

    def _on_ai_error(self, error_msg: str):
        logger.error(f"AI error: {error_msg}")
        self._log_activity(f"AI ERROR: {error_msg}")

    def _on_close(self):
        logger.info("Application closing…")
        self._tts.shutdown()
        self.destroy()
