"""
tools/browser_web.py
=====================
Web search and URL-opening utilities.
Uses the system default browser — no external dependencies needed.
"""

import webbrowser
import urllib.parse
from typing import Tuple

from core.logger import get_logger

logger = get_logger(__name__)

# Search engine template (easily swappable)
SEARCH_ENGINE_URL = "https://www.google.com/search?q={query}"


def web_search(query: str) -> Tuple[bool, str]:
    """
    Open the default browser with a Google search for `query`.

    Returns (success, message).
    """
    if not query or not query.strip():
        return False, "❌ Please provide a search query."

    encoded = urllib.parse.quote_plus(query.strip())
    url = SEARCH_ENGINE_URL.format(query=encoded)
    logger.info(f"Web search: '{query}' → {url}")

    try:
        webbrowser.open(url)
        return True, f"🔍 Searching for: **{query}**"
    except Exception as exc:
        msg = f"❌ Failed to open browser: {exc}"
        logger.error(msg)
        return False, msg


def open_url(url: str) -> Tuple[bool, str]:
    """
    Open an arbitrary URL in the default browser.

    Returns (success, message).
    """
    if not url or not url.strip():
        return False, "❌ Please provide a URL."

    url = url.strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    logger.info(f"Opening URL: {url}")

    try:
        webbrowser.open(url)
        return True, f"🌐 Opened: {url}"
    except Exception as exc:
        msg = f"❌ Failed to open URL: {exc}"
        logger.error(msg)
        return False, msg
