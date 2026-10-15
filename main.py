"""
main.py
=======
Entry point for the AI Laptop Assistant.

Run this file to start the application:
    python main.py
"""

import sys
import os

# ── Ensure the project root is on sys.path ────────────────────────────────────
# This allows `from config.settings import ...` to work no matter where
# the script is launched from.
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# ── Imports ───────────────────────────────────────────────────────────────────
from core.logger import get_logger

logger = get_logger("main")


def check_dependencies() -> bool:
    """
    Check that critical packages are importable and warn the user
    about optional ones that are missing.
    Returns True if the app can start, False if a critical dep is missing.
    """
    critical = {
        "customtkinter": "pip install customtkinter",
        "dotenv":        "pip install python-dotenv",
    }
    optional = {
        "pyttsx3":             "pip install pyttsx3  (text-to-speech)",
        "speech_recognition":  "pip install SpeechRecognition PyAudio  (voice input)",
        "pyautogui":           "pip install pyautogui  (screenshots)",
        "psutil":              "pip install psutil  (system info)",
    }

    # Check critical
    for pkg, install_cmd in critical.items():
        try:
            __import__(pkg)
        except ImportError:
            logger.critical(
                f"Critical package '{pkg}' is missing!\n"
                f"Please run: {install_cmd}"
            )
            return False

    # Warn about optional
    for pkg, note in optional.items():
        try:
            __import__(pkg)
        except ImportError:
            logger.warning(f"Optional package missing — {note}")

    return True


def main():
    logger.info("=" * 60)
    logger.info("  AI Laptop Assistant starting…")
    logger.info("=" * 60)

    if not check_dependencies():
        print(
            "\n❌  A required package is missing.\n"
            "    Please install all dependencies:\n\n"
            "        pip install -r requirements.txt\n"
        )
        sys.exit(1)

    # Import GUI only after dep check (avoids confusing import errors)
    from gui.main_window import MainWindow

    app = MainWindow()
    logger.info("Entering tkinter main loop…")
    app.mainloop()
    logger.info("Application exited cleanly.")


if __name__ == "__main__":
    main()
