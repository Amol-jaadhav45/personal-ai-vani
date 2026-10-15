"""
voice/text_to_speech.py
========================
Text-to-Speech (TTS) using pyttsx3 (offline, no API calls).

IMPORTANT: pyttsx3 must be initialised AND used on the SAME thread.
This module creates a dedicated TTS worker thread with its own event loop
so that speech never blocks the GUI and always works reliably.
"""

import queue
import threading
from typing import Optional, Callable

from config.settings import TTS_RATE, TTS_VOLUME
from core.logger import get_logger

logger = get_logger(__name__)

# Sentinel to tell the worker thread to shut down
_SHUTDOWN = "__SHUTDOWN__"


class TextToSpeech:
    """
    Thread-safe TTS wrapper.

    A dedicated worker thread owns the pyttsx3 engine.
    speak() puts text on a queue; the worker picks it up and speaks it.

    Usage:
        tts = TextToSpeech()
        tts.speak("Hello, I am Vani!")
        tts.stop()
    """

    def __init__(self):
        self._available = False
        self._queue: queue.Queue = queue.Queue()
        self._rate = TTS_RATE
        self._volume = TTS_VOLUME
        self._worker: Optional[threading.Thread] = None
        self._start_worker()

    # ── Worker thread ─────────────────────────────────────────────────────────

    def _start_worker(self):
        """Start the dedicated TTS thread that owns the pyttsx3 engine."""
        self._worker = threading.Thread(
            target=self._worker_loop,
            daemon=True,
            name="TTS-Worker",
        )
        self._worker.start()

    def _worker_loop(self):
        """Runs on the worker thread — creates engine HERE so it's thread-local."""
        try:
            import pyttsx3
            engine = pyttsx3.init()
            engine.setProperty("rate", self._rate)
            engine.setProperty("volume", self._volume)

            # Try to pick a nice voice (female / Zira on Windows)
            voices = engine.getProperty("voices")
            for v in voices:
                if "female" in v.name.lower() or "zira" in v.name.lower():
                    engine.setProperty("voice", v.id)
                    logger.info(f"Offline TTS voice: {v.name}")
                    break

            self._engine_ref = engine   # for set_rate / set_volume
            self._available = True
            logger.info("TTS worker ready.")

        except ImportError:
            logger.warning("pyttsx3 not installed — offline TTS disabled.")
        except Exception as exc:
            logger.error(f"TTS init error: {exc}")

        from config.settings import OPENAI_API_KEY
        import tempfile
        import os
        import winsound

        # ── Main loop: wait for text on the queue, speak it ───────────────
        while True:
            try:
                item = self._queue.get()
                if item == _SHUTDOWN:
                    logger.info("TTS worker shutting down.")
                    break
                
                if isinstance(item, tuple):
                    text, on_finish = item
                else:
                    text, on_finish = item, None

                if text:
                    # Try Human OpenAI TTS first if api key is available
                    played_human = False
                    if OPENAI_API_KEY:
                        try:
                            from openai import OpenAI
                            client = OpenAI(api_key=OPENAI_API_KEY)
                            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
                                tmp_path = tmp_file.name
                            
                            response = client.audio.speech.create(
                                model="tts-1",
                                voice="nova",
                                response_format="wav",
                                input=text
                            )
                            response.stream_to_file(tmp_path)
                            winsound.PlaySound(tmp_path, winsound.SND_FILENAME)
                            try:
                                os.unlink(tmp_path)
                            except:
                                pass
                            played_human = True
                        except Exception as ai_exc:
                            logger.error(f"OpenAI TTS failed: {ai_exc}. Falling back to pyttsx3...")
                    
                    if not played_human and self._available:
                        engine.say(text)
                        engine.runAndWait()
                        
                    if on_finish:
                        try:
                            on_finish()
                        except Exception as cb_exc:
                            logger.error(f"TTS on_finish callback error: {cb_exc}")
            except Exception as exc:
                logger.error(f"TTS speak error: {exc}")

    # ── Public API ────────────────────────────────────────────────────────────

    @property
    def is_available(self) -> bool:
        return self._available

    def speak(self, text: str, on_finish: Optional[Callable] = None):
        """Queue text to be spoken. Non-blocking."""
        if not self._available or not text:
            if on_finish:
                try:
                    on_finish()
                except:
                    pass
            return
        # Clear pending items so we always speak the LATEST message
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
            except queue.Empty:
                break
        self._queue.put((text, on_finish))

    def stop(self):
        """Stop current speech and clear pending queue."""
        if not self._available:
            return
        # Clear queue
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
            except queue.Empty:
                break
        # Try to interrupt current speech
        try:
            if hasattr(self, "_engine_ref") and self._engine_ref:
                self._engine_ref.stop()
        except Exception:
            pass

    def set_rate(self, rate: int):
        """Change speech speed at runtime."""
        self._rate = rate
        if hasattr(self, "_engine_ref") and self._engine_ref:
            try:
                self._engine_ref.setProperty("rate", rate)
            except Exception:
                pass

    def set_volume(self, volume: float):
        """Change volume (0.0–1.0) at runtime."""
        self._volume = max(0.0, min(1.0, volume))
        if hasattr(self, "_engine_ref") and self._engine_ref:
            try:
                self._engine_ref.setProperty("volume", self._volume)
            except Exception:
                pass

    def shutdown(self):
        """Cleanly shut down the worker thread."""
        self._queue.put(_SHUTDOWN)
