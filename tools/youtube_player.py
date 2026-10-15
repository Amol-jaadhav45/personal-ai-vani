"""
tools/youtube_player.py
=======================
Handles YouTube playback, including setting speed and quality.
Uses Selenium to search YouTube and click + play the first result.
"""

import time
import urllib.parse
from typing import Tuple

from core.logger import get_logger

logger = get_logger(__name__)


def play_youtube_video(query: str, speed: float = 1.0, quality: str = 'hd1080') -> Tuple[bool, str]:
    """
    Search YouTube for a query using Selenium and play the first result.

    Parameters:
    - query: The song / video title to search for.
    - speed: Playback speed (1.0 = normal, 1.5 = faster, etc.)
    - quality: Quality string (e.g. 'hd1080', 'hd720', 'large' for 480p)

    Returns:
    (success: bool, message: str)
    """
    if not query or not query.strip():
        return False, "❌ Please provide a YouTube search query."

    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.service import Service as ChromeService
        from webdriver_manager.chrome import ChromeDriverManager
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
    except ImportError:
        msg = "❌ Selenium or webdriver-manager is not installed. Run: pip install selenium webdriver-manager"
        logger.error(msg)
        return False, msg

    logger.info(f"Searching YouTube for: '{query}'")

    search_url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}"

    try:
        # ── Launch Chrome ─────────────────────────────────────────────────
        options = webdriver.ChromeOptions()
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)
        # Keep the browser open after script exits
        options.add_experimental_option("detach", True)

        service = ChromeService(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)

        # ── Navigate to YouTube search results ────────────────────────────
        driver.get(search_url)

        # ── Wait for the first video thumbnail to appear and click it ─────
        wait = WebDriverWait(driver, 15)
        first_video = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "ytd-video-renderer #video-title"))
        )
        video_title = first_video.get_attribute("title") or query
        logger.info(f"Clicking first result: {video_title}")
        first_video.click()

        # ── Wait for the video player to appear ───────────────────────────
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "video")))
        time.sleep(2)   # give YouTube player time to initialise fully

        # ── Set playback speed & quality via JS ───────────────────────────
        js_script = f"""
            var video = document.getElementsByTagName('video')[0];
            if (video) {{
                video.playbackRate = {speed};
                // Unmute and ensure playback
                video.muted = false;
                if (video.paused) {{ video.play(); }}
            }}
            var player = document.getElementById('movie_player');
            if (player && player.setPlaybackQualityRange) {{
                player.setPlaybackQualityRange('{quality}', '{quality}');
            }}
        """
        driver.execute_script(js_script)

        msg = f"▶️ Now playing **{video_title}** on YouTube (Speed: {speed}x, Quality: {quality})"
        logger.info(msg)
        return True, msg

    except Exception as e:
        logger.error(f"Failed to play YouTube video: {e}")
        try:
            driver.quit()
        except Exception:
            pass
        return False, f"❌ Failed to play video: {e}"
