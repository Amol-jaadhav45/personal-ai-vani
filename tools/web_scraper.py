"""
tools/web_scraper.py
====================
Allows Vani to autonomously scrape and read the contents of webpages
so it can answer questions using live data from the internet.
"""

import requests
from typing import Tuple
from core.logger import get_logger

logger = get_logger(__name__)

def read_webpage(url: str) -> Tuple[bool, str]:
    """
    Downloads and extracts the text content from a given URL.
    """
    try:
        from bs4 import BeautifulSoup
    except ImportError:
         return False, "❌ BeautifulSoup4 is not installed. Please run: pip install beautifulsoup4"
         
    try:
        logger.info(f"Reading webpage: {url}")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Remove scripts, styles, etc.
        for element in soup(["script", "style", "nav", "footer", "header"]):
            element.decompose()
            
        text = soup.get_text(separator=' ', strip=True)
        
        # Truncate to avoid context window explosion (give the AI the first 8000 chars)
        max_chars = 8000
        if len(text) > max_chars:
            text = text[:max_chars] + "... [Content Truncated]"
            
        return True, f"📄 Successfully read {url}:\n\n{text}"

    except Exception as e:
        msg = f"❌ Failed to read {url}: {e}"
        logger.error(msg)
        return False, msg
