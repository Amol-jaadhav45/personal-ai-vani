"""
tools/media_controls.py
========================
System-wide multimedia controls (Volume, Play/Pause, Next Track).
"""

import pyautogui
from typing import Tuple
from core.logger import get_logger

logger = get_logger(__name__)

def media_control(action: str) -> Tuple[bool, str]:
    """Execute a global system media control action."""
    action = action.lower().strip()
    
    key_map = {
        "volume_up": "volumeup",
        "volume_down": "volumedown",
        "mute": "volumemute",
        "play_pause": "playpause",
        "next": "nexttrack",
        "previous": "prevtrack"
    }
    
    if action not in key_map:
        return False, f"❌ Unknown media action: {action}"
        
    try:
        # For volume, press it multiple times to make a noticeable difference
        if action == "volume_up":
            pyautogui.press(key_map[action], presses=5)
            logger.info("Volume increased.")
            return True, "🔊 Volume turned up."
        elif action == "volume_down":
            pyautogui.press(key_map[action], presses=5)
            logger.info("Volume decreased.")
            return True, "🔉 Volume turned down."
        else:
            pyautogui.press(key_map[action])
            logger.info(f"Media action executed: {action}")
            
            messages = {
                "mute": "🔇 System muted.",
                "play_pause": "⏯️ Media toggled.",
                "next": "⏭️ Playing next track.",
                "previous": "⏮️ Playing previous track."
            }
            return True, messages[action]
            
    except Exception as e:
        logger.error(f"Failed to execute media control: {e}")
        return False, f"❌ Failed media control: {e}"
