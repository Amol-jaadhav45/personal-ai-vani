"""
gui/chat_panel.py
=================
The scrollable chat area that displays user and assistant messages
as styled "bubbles" inside a CustomTkinter scrollable frame.
"""

import customtkinter as ctk
from datetime import datetime

from gui.styles import COLORS, FONTS, SIZES
from core.logger import get_logger

logger = get_logger(__name__)


class ChatMessage(ctk.CTkFrame):
    """
    A single chat message bubble.

    Parameters
    ----------
    parent : widget
        The parent container.
    role : str
        'user' or 'assistant'
    text : str
        The message content (supports basic markdown-like formatting).
    """

    def __init__(self, parent, role: str, text: str, **kwargs):
        is_user = role == "user"

        bg = COLORS["bg_user"] if is_user else COLORS["bg_card"]
        super().__init__(
            parent,
            fg_color=bg,
            corner_radius=SIZES["corner_radius"],
            **kwargs,
        )

        # ── Avatar / name label ───────────────────────────────────────────────
        avatar = "👤" if is_user else "🤖"
        name   = "You" if is_user else "Vani"

        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=SIZES["msg_pad_x"], pady=(8, 2))

        ctk.CTkLabel(
            header_frame,
            text=f"{avatar} {name}",
            font=ctk.CTkFont(*FONTS["body_bold"]),
            text_color=COLORS["accent"] if not is_user else COLORS["accent_green"],
        ).pack(side="left")

        # Timestamp
        ts = datetime.now().strftime("%H:%M")
        ctk.CTkLabel(
            header_frame,
            text=ts,
            font=ctk.CTkFont(*FONTS["small"]),
            text_color=COLORS["text_muted"],
        ).pack(side="right")

        # ── Message text ──────────────────────────────────────────────────────
        ctk.CTkLabel(
            self,
            text=text,
            font=ctk.CTkFont(*FONTS["body"]),
            text_color=COLORS["text_primary"],
            wraplength=560,
            justify="left",
            anchor="w",
        ).pack(
            fill="x",
            padx=SIZES["msg_pad_x"],
            pady=(2, SIZES["msg_pad_y"]),
        )


class ChatPanel(ctk.CTkScrollableFrame):
    """
    Scrollable container that holds all ChatMessage widgets.
    Automatically scrolls to the bottom when a new message is added.
    """

    def __init__(self, parent, **kwargs):
        super().__init__(
            parent,
            fg_color=COLORS["bg_panel"],
            scrollbar_button_color=COLORS["border"],
            scrollbar_button_hover_color=COLORS["accent"],
            **kwargs,
        )
        self._messages: list = []

    def add_message(self, role: str, text: str):
        """Add a message bubble and scroll to the bottom."""
        logger.debug(f"Chat panel message [{role}]: {text[:60]}")

        bubble = ChatMessage(self, role=role, text=text)
        bubble.pack(fill="x", padx=12, pady=6)
        self._messages.append(bubble)

        # Scroll to the newest message
        self.after(50, self._scroll_bottom)

    def _scroll_bottom(self):
        """Force the scrollable frame to show the last message."""
        try:
            self._parent_canvas.yview_moveto(1.0)
        except AttributeError:
            # Fallback for different CustomTkinter versions
            try:
                self._scrollbar.set(1.0, 1.0)
            except Exception:
                pass

    def clear(self):
        """Remove all messages from the chat panel."""
        for widget in self._messages:
            widget.destroy()
        self._messages.clear()

    def add_system_message(self, text: str):
        """Add a centered system/status message (e.g. 'New conversation started')."""
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.pack(fill="x", pady=4)

        ctk.CTkLabel(
            frame,
            text=f"─── {text} ───",
            font=ctk.CTkFont(*FONTS["small"]),
            text_color=COLORS["text_muted"],
        ).pack()
