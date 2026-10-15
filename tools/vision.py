"""
tools/vision.py
================
Analyzes the screen using Vision APIs (OpenAI or Gemini).
Takes a screenshot, sends it to the vision model with the user's query,
and returns the analysis.
"""

import os
from typing import Tuple
from pathlib import Path
from tools.screenshot import take_screenshot
from config.settings import OPENAI_API_KEY, GEMINI_API_KEY, OPENAI_MODEL
from core.logger import get_logger

logger = get_logger(__name__)

def analyze_screen(query: str = "Describe what is on the screen in detail.") -> Tuple[bool, str]:
    """
    Takes a screenshot and analyzes it using an available Vision API.
    
    Parameters
    ----------
    query : str
        What to look for on the screen.
        
    Returns
    -------
    (success: bool, result_message: str)
    """
    logger.info("Taking screenshot for vision analysis...")
    success, msg = take_screenshot()
    if not success:
         return False, f"❌ Failed to take screenshot for analysis: {msg}"
    
    # Extract the filepath from the message
    # format: "📸 Screenshot saved to: {filepath}"
    filepath_str = msg.split("saved to: ")[-1].strip()
    
    if not os.path.exists(filepath_str):
        return False, "❌ Screenshot file not found."
        
    # Try Gemini first (usually free and good at vision)
    if GEMINI_API_KEY:
        try:
            logger.info("Using Gemini Vision for screen analysis...")
            import google.generativeai as genai
            from PIL import Image
            genai.configure(api_key=GEMINI_API_KEY)
            model = genai.GenerativeModel('gemini-1.5-flash')
            image = Image.open(filepath_str)
            response = model.generate_content([query, image])
            return True, f"👁️ Vision Analysis:\n{response.text.strip()}"
        except Exception as e:
            logger.error(f"Gemini Vision failed: {e}")
            # fallthrough to try OpenAI
    
    # Try OpenAI next
    if OPENAI_API_KEY:
        try:
            logger.info("Using OpenAI Vision for screen analysis...")
            from openai import OpenAI
            import base64
            
            client = OpenAI(api_key=OPENAI_API_KEY)
            
            # Base64 encode the image
            with open(filepath_str, "rb") as image_file:
                base64_image = base64.b64encode(image_file.read()).decode('utf-8')
                
            response = client.chat.completions.create(
                model="gpt-4o-mini", # Note: gpt-4o-mini supports vision
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": query},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=1024,
            )
            return True, f"👁️ Vision Analysis:\n{response.choices[0].message.content.strip()}"
            
        except Exception as e:
            logger.error(f"OpenAI Vision failed: {e}")
            return False, f"❌ Vision APIs failed. Error: {e}"
            
    return False, "❌ No Vision API keys configured. Set GEMINI_API_KEY or OPENAI_API_KEY in .env"
