"""
gui/sidebar.py
===============
JARVIS-style sidebar with:
  - Animated branding (Vani logo + tagline)
  - Live system stats (CPU, RAM, Battery)
  - Quick action buttons
  - Chat history list
"""

import threading
import customtkinter as ctk
from typing import Callable, Optional

from gui.styles import COLORS, FONTS, SIZES
from core.logger import get_logger

logger = get_logger(__name__)


class Sidebar(ctk.CTkFrame):
    """Left sidebar panel — JARVIS-style dark theme."""

    def __init__(
        self,
        parent,
        on_new_chat:       Optional[Callable] = None,
        on_clear_chat:     Optional[Callable] = None,
        on_session_select: Optional[Callable] = None,
    ):
        super().__init__(
            parent,
            width=SIZES["sidebar_w"],
            fg_color=COLORS["bg_panel"],
            corner_radius=0,
        )
        self.pack_propagate(False)

        self._on_new_chat       = on_new_chat
        self._on_clear_chat     = on_clear_chat
        self._on_session_select = on_session_select

        self._build()
        self._start_stats_loop()

    # ── Build ─────────────────────────────────────────────────────────────────

    def _build(self):
        # ── Branding ──────────────────────────────────────────────────────
        brand = ctk.CTkFrame(self, fg_color="transparent")
        brand.pack(fill="x", padx=16, pady=(20, 4))

        # Vani logo line
        logo_frame = ctk.CTkFrame(brand, fg_color="transparent")
        logo_frame.pack(fill="x")

        ctk.CTkLabel(
            logo_frame,
            text="⚡",
            font=ctk.CTkFont("Segoe UI Emoji", 28),
            text_color=COLORS["accent"],
        ).pack(side="left", padx=(0, 8))

        ctk.CTkLabel(
            logo_frame,
            text="VANI",
            font=ctk.CTkFont(*FONTS["title"]),
            text_color=COLORS["accent"],
        ).pack(side="left")

        ctk.CTkLabel(
            brand,
            text="AI Laptop Assistant",
            font=ctk.CTkFont(*FONTS["small"]),
            text_color=COLORS["text_secondary"],
        ).pack(anchor="w", padx=2)

        # Divider
        ctk.CTkFrame(self, height=1, fg_color=COLORS["accent_dim"]).pack(
            fill="x", padx=16, pady=(12, 8)
        )

        # ── System Status Panel ───────────────────────────────────────────
        status_header = ctk.CTkFrame(self, fg_color="transparent")
        status_header.pack(fill="x", padx=16, pady=(4, 2))
        ctk.CTkLabel(
            status_header,
            text="📊  SYSTEM STATUS",
            font=ctk.CTkFont(*FONTS["mono_small"]),
            text_color=COLORS["accent"],
        ).pack(anchor="w")

        self._stats_frame = ctk.CTkFrame(
            self, fg_color=COLORS["bg_card"], corner_radius=8
        )
        self._stats_frame.pack(fill="x", padx=16, pady=(4, 8))

        # CPU row
        self._cpu_label = self._stat_row(self._stats_frame, "🧠 CPU", "Loading…")
        # RAM row
        self._ram_label = self._stat_row(self._stats_frame, "💾 RAM", "Loading…")
        # Battery row
        self._bat_label = self._stat_row(self._stats_frame, "🔋 BAT", "Loading…")
        # Network row
        self._net_label = self._stat_row(self._stats_frame, "🌐 NET", "Loading…")

        # ── Quick Actions ─────────────────────────────────────────────────
        ctk.CTkFrame(self, height=1, fg_color=COLORS["accent_dim"]).pack(
            fill="x", padx=16, pady=(4, 8)
        )

        actions_header = ctk.CTkFrame(self, fg_color="transparent")
        actions_header.pack(fill="x", padx=16, pady=(0, 4))
        ctk.CTkLabel(
            actions_header,
            text="⚡  QUICK ACTIONS",
            font=ctk.CTkFont(*FONTS["mono_small"]),
            text_color=COLORS["accent"],
        ).pack(anchor="w")

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=16, pady=(0, 4))

        ctk.CTkButton(
            btn_frame,
            text="➕  New Chat",
            height=34,
            corner_radius=8,
            fg_color=COLORS["accent_dim"],
            hover_color=COLORS["accent"],
            font=ctk.CTkFont(*FONTS["body"]),
            text_color=COLORS["text_primary"],
            command=self._on_new_chat,
        ).pack(fill="x", pady=2)

        ctk.CTkButton(
            btn_frame,
            text="🗑️  Clear Chat",
            height=34,
            corner_radius=8,
            fg_color=COLORS["bg_card"],
            hover_color=COLORS["accent_red"],
            font=ctk.CTkFont(*FONTS["body"]),
            text_color=COLORS["text_secondary"],
            command=self._on_clear_chat,
        ).pack(fill="x", pady=2)

        # ── Chat History ──────────────────────────────────────────────────
        ctk.CTkFrame(self, height=1, fg_color=COLORS["accent_dim"]).pack(
            fill="x", padx=16, pady=(8, 6)
        )

        history_header = ctk.CTkFrame(self, fg_color="transparent")
        history_header.pack(fill="x", padx=16, pady=(0, 4))
        ctk.CTkLabel(
            history_header,
            text="💬  HISTORY",
            font=ctk.CTkFont(*FONTS["mono_small"]),
            text_color=COLORS["accent"],
        ).pack(anchor="w")

        self._history_scroll = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            scrollbar_button_color=COLORS["accent_dim"],
        )
        self._history_scroll.pack(fill="both", expand=True, padx=8, pady=(0, 12))

    # ── Stat row helper ───────────────────────────────────────────────────────

    def _stat_row(self, parent, icon_text: str, initial_value: str):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=10, pady=3)

        ctk.CTkLabel(
            row,
            text=icon_text,
            font=ctk.CTkFont(*FONTS["mono_small"]),
            text_color=COLORS["text_secondary"],
            width=60,
            anchor="w",
        ).pack(side="left")

        val_label = ctk.CTkLabel(
            row,
            text=initial_value,
            font=ctk.CTkFont(*FONTS["mono_small"]),
            text_color=COLORS["text_primary"],
            anchor="e",
        )
        val_label.pack(side="right")
        return val_label

    # ── Live stats ────────────────────────────────────────────────────────────

    def _start_stats_loop(self):
        self._update_stats()

    def _update_stats(self):
        threading.Thread(
            target=self._fetch_stats, daemon=True, name="Stats-Thread"
        ).start()
        self.after(3000, self._update_stats)   # refresh every 3s

    def _fetch_stats(self):
        try:
            import psutil
            import socket

            cpu = psutil.cpu_percent(interval=0.3)
            ram = psutil.virtual_memory().percent

            # Battery
            bat = psutil.sensors_battery()
            if bat:
                bat_str = f"{bat.percent}% {'⚡' if bat.power_plugged else '🔋'}"
            else:
                bat_str = "AC Power"

            # Network
            try:
                socket.create_connection(("8.8.8.8", 53), timeout=1)
                net_str = "Online 🟢"
            except OSError:
                net_str = "Offline 🔴"

            # Color coding based on usage
            cpu_color = COLORS["accent_green"] if cpu < 60 else (COLORS["accent_yellow"] if cpu < 85 else COLORS["accent_red"])
            ram_color = COLORS["accent_green"] if ram < 60 else (COLORS["accent_yellow"] if ram < 85 else COLORS["accent_red"])

            self.after(0, lambda: self._cpu_label.configure(text=f"{cpu:.0f}%", text_color=cpu_color))
            self.after(0, lambda: self._ram_label.configure(text=f"{ram:.0f}%", text_color=ram_color))
            self.after(0, lambda: self._bat_label.configure(text=bat_str))
            self.after(0, lambda: self._net_label.configure(text=net_str))

        except Exception as exc:
            logger.debug(f"Stats fetch error: {exc}")

    # ── History ───────────────────────────────────────────────────────────────

    def load_history(self, sessions: list):
        for widget in self._history_scroll.winfo_children():
            widget.destroy()

        if not sessions:
            ctk.CTkLabel(
                self._history_scroll,
                text="No conversations yet",
                font=ctk.CTkFont(*FONTS["small"]),
                text_color=COLORS["text_muted"],
            ).pack(pady=8)
            return

        for session in sessions[:15]:
            sid   = session["id"]
            title = session.get("title", "Untitled")[:30]

            btn = ctk.CTkButton(
                self._history_scroll,
                text=f"  💬 {title}",
                height=30,
                corner_radius=6,
                fg_color="transparent",
                hover_color=COLORS["accent_dim"],
                font=ctk.CTkFont(*FONTS["small"]),
                text_color=COLORS["text_secondary"],
                anchor="w",
                command=lambda s=sid: self._on_session_select(s),
            )
            btn.pack(fill="x", pady=1)
