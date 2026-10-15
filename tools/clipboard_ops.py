"""
tools/clipboard_ops.py
======================
Tools for interacting with the system clipboard.
Very useful for coders (reading copied error messages, writing code snippets).
"""

import pyperclip
from typing import Tuple
from core.logger import get_logger

logger = get_logger(__name__)

def read_clipboard() -> Tuple[bool, str]:
    """Read the current text contents of the user's clipboard."""
    try:
        content = pyperclip.paste()
        if not content:
            return True, "Clipboard is currently empty."
        logger.info("Successfully read from clipboard.")
        return True, f"Clipboard Content:\n```\n{content}\n```"
    except Exception as exc:
        msg = f"❌ Failed to read clipboard: {exc}"
        logger.error(msg)
        return False, msg

def write_clipboard(text: str) -> Tuple[bool, str]:
    """Write text to the user's clipboard."""
    try:
        pyperclip.copy(text)
        logger.info(f"Copied {len(text)} characters to clipboard.")
        return True, f"✅ Successfully copied text to your clipboard!"
    except Exception as exc:
        msg = f"❌ Failed to write to clipboard: {exc}"
        logger.error(msg)
        return False, msg
