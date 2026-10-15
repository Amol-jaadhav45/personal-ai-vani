"""
tools/search_engine.py
======================
Headless web search engine for the AI.
Uses DuckDuckGo HTML to fetch search results silently, allowing the AI
to read them and formulate an answer.
"""

import requests
from bs4 import BeautifulSoup
from typing import Tuple
from core.logger import get_logger

logger = get_logger(__name__)

def headless_search(query: str, max_results: int = 5) -> Tuple[bool, str]:
    """
    Perform a headless web search and return a summary of the results.
    """
    logger.info(f"Headless search for: {query}")
    try:
        from duckduckgo_search import DDGS
        
        results = DDGS().text(query, max_results=max_results)
        
        output = []
        for i, res in enumerate(results):
            title = res.get('title', '')
            snippet = res.get('body', '')
            link = res.get('href', '')
            if title and snippet:
                output.append(f"{i+1}. {title}\nURL: {link}\nSnippet: {snippet}")
                
        if not output:
             return True, "No clear results found on the web."
             
        final_text = "\n\n".join(output)
        return True, f"Search Results for '{query}':\n\n{final_text}"
        
    except Exception as e:
        msg = f"❌ Search failed: {e}"
        logger.error(msg)
        return False, msg
