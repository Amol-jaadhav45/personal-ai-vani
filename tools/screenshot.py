"""
tools/screenshot.py
====================
Captures a screenshot of the entire screen and saves it to the
user's Desktop (or a custom path) with a timestamped filename.
"""

import os
from datetime import datetime
from pathlib import Path
from typing import Tuple

from core.logger import get_logger

logger = get_logger(__name__)


def _get_save_dir() -> Path:
    """Return the Desktop path for the current user."""
    desktop = Path.home() / "Desktop"
    desktop.mkdir(parents=True, exist_ok=True)
    return desktop


def take_screenshot(save_dir: str = "") -> Tuple[bool, str]:
    """
    Capture a screenshot and save it as a PNG file.

    Parameters
    ----------
    save_dir : str, optional
        Directory to save the screenshot. Defaults to the user's Desktop.

    Returns
    -------
    (success: bool, message: str)
        message includes the saved file path on success.
    """
    try:
        import pyautogui  # lazy import — only needed here
    except ImportError:
        msg = "❌ pyautogui is not installed. Run: pip install pyautogui"
        logger.error(msg)
        return False, msg

    # Determine save directory
    if save_dir:
        directory = Path(save_dir)
    else:
        directory = _get_save_dir()

    directory.mkdir(parents=True, exist_ok=True)

    # Build timestamped filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"screenshot_{timestamp}.png"
    filepath = directory / filename

    try:
        screenshot = pyautogui.screenshot()
        screenshot.save(str(filepath))
        msg = f"📸 Screenshot saved to: {filepath}"
        logger.info(msg)
        return True, msg
    except Exception as exc:
        msg = f"❌ Failed to take screenshot: {exc}"
        logger.error(msg)
        return False, msg
