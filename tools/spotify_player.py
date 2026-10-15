"""
tools/spotify_player.py
========================
Search and play songs directly in Spotify using the spotify: URI scheme.

How it works:
  1. Opens the Spotify app (via start command)
  2. Constructs a Spotify search URI and opens it directly in Spotify
     -> spotify:search:<query>
     This causes Spotify to open its search with the query and play the top result.
"""

import subprocess
import time
import urllib.parse
from typing import Tuple

from core.logger import get_logger

logger = get_logger(__name__)


def play_spotify_song(query: str) -> Tuple[bool, str]:
    """
    Search and play a song in Spotify using the spotify: URI protocol.

    Parameters:
    - query: The song name / artist to search for.

    Returns:
    (success: bool, message: str)
    """
    if not query or not query.strip():
        return False, "❌ Please provide a song name to play."

    try:
        # Step 1: Find the exact track URI via web search
        import urllib.request
        search_url = "https://lite.duckduckgo.com/lite/?q=" + urllib.parse.quote(f"site:open.spotify.com/track {query}")
        req = urllib.request.Request(search_url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        
        try:
            html = urllib.request.urlopen(req, timeout=5).read().decode('utf-8')
            import re
            match = re.search(r'open\.spotify\.com/track/([a-zA-Z0-9]+)', html)
            if match:
                track_id = match.group(1)
                spotify_uri = f"spotify:track:{track_id}"
            else:
                # Fallback to general search if track not found
                spotify_uri = f"spotify:search:{urllib.parse.quote(query)}"
        except Exception as e:
            logger.warning(f"Failed to scrape track ID: {e}")
            spotify_uri = f"spotify:search:{urllib.parse.quote(query)}"

        logger.info(f"Opening Spotify with URI: {spotify_uri}")

        # Step 2: Open Spotify
        subprocess.Popen(
            ["cmd", "/c", "start", "", spotify_uri],
            shell=False,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )

        logger.info("Waiting for Spotify to load track...")
        is_direct_track = "spotify:track:" in spotify_uri
        
        # Give a robust 4 seconds for Spotify to become fully responsive
        time.sleep(4.0)

        # Step 3: Simulate 'Space' to play the track
        try:
            import pyautogui
            if is_direct_track:
                # When a track is launched via URI, it becomes the active item.
                # 'Space' or 'Enter' will initiate playback.
                pyautogui.press('enter')
                time.sleep(0.5)
                # Sometimes Enter just opens it without playing; Space toggles play.
                # However, if Enter worked, Space would pause. 
                # On Windows Spotify, Enter on a Track URI plays it directly. 
                # Tab + Enter is a fallback if the play button needs focus.
                pyautogui.press('tab')
                pyautogui.press('enter')
                
                # As a final brute-force, send the global Windows Media "Play" key
                time.sleep(1.0)
                pyautogui.press('playpause')
            else:
                pyautogui.press('tab', presses=2, interval=0.2)
                time.sleep(0.5)
                pyautogui.press('enter')
                time.sleep(1.0)
                pyautogui.press('enter')
        except ImportError:
            logger.warning("pyautogui not installed; unable to simulate 'Play'.")

        msg = f"🎵 Playing **{query}** on Spotify"
        logger.info(msg)
        return True, msg

    except Exception as e:
        logger.error(f"Failed to play Spotify song: {e}")
        return False, f"❌ Failed to open Spotify: {e}"
