"""
voice/speech_to_text.py
========================
Speech-to-Text using sounddevice with smart VAD (Voice Activity Detection).

Strategy:
  1. Record in small chunks while listening
  2. Detect when speech STARTS (volume rises above threshold)
  3. Stop recording automatically after speech ENDS (silence for SILENCE_LIMIT seconds)
  4. Send audio to Google STT for transcription

Falls back to PyAudio if sounddevice is unavailable.
"""

import io
import threading
import wave
import time
import numpy as np
from typing import Callable, Optional

from config.settings import VOICE_TIMEOUT, VOICE_PHRASE_LIMIT
from core.logger import get_logger

logger = get_logger(__name__)

SAMPLE_RATE      = 16000    # Hz
CHANNELS         = 1
DTYPE            = "int16"
CHUNK_SIZE       = 1024     # samples per chunk (~64ms at 16kHz)

# --- VAD Tuning Parameters ---
SPEECH_THRESH    = 30       # Extremely low threshold for quiet mics
SILENCE_LIMIT    = 1.5      # seconds of silence AFTER speech ends → stop recording
MAX_RECORD_S     = 15       # hard cap on recording length (seconds)
MIN_SPEECH_S     = 0.1      # minimum speech duration to attempt recognition (lowered to catch quick phrases)
PRE_ROLL_CHUNKS  = 10       # number of chunks to keep before speech starts (buffer)


class SpeechToText:
    """
    Captures microphone audio and transcribes it using Google STT.

    Uses sounddevice with proper VAD:
    - Stays idle until speech is detected (above threshold)
    - Records until silence for SILENCE_LIMIT seconds
    - Rejects recordings that are too short / too quiet
    """

    def __init__(self):
        self._backend: str = "none"
        self._is_listening = False
        self._detect_backend()

    # ── Backend detection ─────────────────────────────────────────────────────

    def _detect_backend(self):
        try:
            import sounddevice as sd
            import soundfile        # noqa: F401
            import speech_recognition as sr  # noqa: F401

            devices    = sd.query_devices()  # noqa: F841
            default_in = sd.default.device[0]
            logger.info(f"STT backend: sounddevice | default input device: {default_in}")
            logger.info(f"Input device info: {sd.query_devices(default_in, 'input')}")

            self._backend = "sounddevice"
            return
        except Exception as e:
            logger.warning(f"sounddevice backend failed: {e}")

        try:
            import pyaudio          # noqa: F401
            import speech_recognition as sr
            self._recognizer = sr.Recognizer()
            self._recognizer.energy_threshold = 300
            self._recognizer.dynamic_energy_threshold = True
            self._backend = "pyaudio"
            logger.info("STT backend: pyaudio")
            return
        except ImportError:
            pass

        logger.warning("No audio backend found. Voice input disabled.")
        self._backend = "none"

    # ── Public API ────────────────────────────────────────────────────────────

    @property
    def is_available(self) -> bool:
        return self._backend != "none"

    @property
    def is_listening(self) -> bool:
        return self._is_listening

    def listen(
        self,
        on_result: Callable[[str], None],
        on_error:  Optional[Callable[[str], None]] = None,
        on_start:  Optional[Callable[[], None]]    = None,
        on_stop:   Optional[Callable[[], None]]    = None,
        on_level:  Optional[Callable[[float], None]] = None,  # mic level 0.0-1.0
    ):
        if not self.is_available:
            if on_error:
                on_error("⚠️  Voice input unavailable. Run: pip install sounddevice soundfile")
            return

        if self._is_listening:
            return

        target = (
            self._listen_sounddevice
            if self._backend == "sounddevice"
            else self._listen_pyaudio
        )

        threading.Thread(
            target=target,
            args=(on_result, on_error, on_start, on_stop, on_level),
            daemon=True,
            name="STT-Thread",
        ).start()

    # ── sounddevice VAD backend ───────────────────────────────────────────────

    def _listen_sounddevice(self, on_result, on_error, on_start, on_stop, on_level):
        import sounddevice as sd
        import speech_recognition as sr

        self._is_listening = True
        if on_start:
            on_start()

        try:
            logger.info("VAD listening — waiting for speech...")

            # Rolling pre-roll buffer so we don't clip the start of speech
            pre_roll   = []
            frames_all = []

            speech_started  = False
            silence_chunks  = 0
            speech_chunks   = 0

            max_frames      = int(MAX_RECORD_S * SAMPLE_RATE / CHUNK_SIZE)
            silence_limit_chunks = int(SILENCE_LIMIT * SAMPLE_RATE / CHUNK_SIZE)
            min_speech_chunks    = int(MIN_SPEECH_S  * SAMPLE_RATE / CHUNK_SIZE)

            with sd.InputStream(
                samplerate=SAMPLE_RATE,
                channels=CHANNELS,
                dtype=DTYPE,
                blocksize=CHUNK_SIZE,
            ) as stream:

                while self._is_listening:
                    chunk, _ = stream.read(CHUNK_SIZE)
                    rms = float(np.sqrt(np.mean(chunk.astype(np.float32) ** 2)))

                    # Always update the mic level bar (scaled for lower volumes)
                    if on_level:
                        on_level(min(rms / 200.0, 1.0))

                    is_speech = rms > SPEECH_THRESH

                    if not speech_started:
                        # Keep a rolling pre-roll buffer
                        pre_roll.append(chunk.copy())
                        if len(pre_roll) > PRE_ROLL_CHUNKS:
                            pre_roll.pop(0)

                        if is_speech:
                            logger.info("Speech detected — recording...")
                            speech_started = True
                            # Prepend the pre-roll so we don't miss the first syllable
                            frames_all = list(pre_roll)
                            frames_all.append(chunk.copy())
                            speech_chunks = 1
                            silence_chunks = 0
                    else:
                        frames_all.append(chunk.copy())
                        if is_speech:
                            speech_chunks  += 1
                            silence_chunks  = 0
                        else:
                            silence_chunks += 1

                        # Hard cap
                        if len(frames_all) >= max_frames:
                            logger.info("Max recording length reached.")
                            break

                        # Stop after sustained silence
                        if silence_chunks >= silence_limit_chunks:
                            logger.info(f"Silence detected after {speech_chunks} speech chunks — stopping.")
                            break

            # ── Transcription ──────────────────────────────────────────────
            if not frames_all or speech_chunks < min_speech_chunks:
                if on_error:
                    on_error("🤔 No speech detected. Please try again.")
                return

            audio_np   = np.concatenate(frames_all, axis=0)
            duration_s = len(audio_np) / SAMPLE_RATE
            logger.info(f"Recorded {duration_s:.2f}s of speech audio ({speech_chunks} speech chunks)")

            wav_buffer = io.BytesIO()
            with wave.open(wav_buffer, "wb") as wf:
                wf.setnchannels(CHANNELS)
                wf.setsampwidth(2)
                wf.setframerate(SAMPLE_RATE)
                wf.writeframes(audio_np.tobytes())
            wav_buffer.seek(0)

            recognizer = sr.Recognizer()
            with sr.AudioFile(wav_buffer) as source:
                audio_data = recognizer.record(source)

            # Try Groq API first (Lightning fast AI Ear)
            from config.settings import GROQ_API_KEY
            text = None
            
            if GROQ_API_KEY:
                try:
                    from groq import Groq
                    client = Groq(api_key=GROQ_API_KEY)
                    with open("temp_audio.wav", "wb") as f:
                        f.write(wav_buffer.getvalue())
                    with open("temp_audio.wav", "rb") as file:
                        transcription = client.audio.transcriptions.create(
                            file=("temp_audio.wav", file.read()),
                            model="whisper-large-v3",
                        )
                    text = transcription.text.strip()
                except Exception as e:
                    logger.warning(f"Groq Whisper failed: {e}. Falling back...")
            
            if not text:
                try:
                    # Attempt Local AI Whisper if installed
                    text = recognizer.recognize_whisper(audio_data, model="base").strip()
                except ImportError:
                    # Fallback to free Google Ears
                    text = recognizer.recognize_google(audio_data).strip()

            logger.info(f"Recognised: '{text}'")
            if on_result and text:
                on_result(text)

        except Exception as exc:
            import speech_recognition as sr
            if isinstance(exc, sr.UnknownValueError):
                msg = "Hmm, I heard you speak but couldn't quite make out the words. Could you repeat that?"
                logger.warning(msg)
                if on_error:
                    on_error(msg)
            elif isinstance(exc, sr.RequestError):
                msg = f"❌ Google STT service error: {exc}"
                logger.error(msg)
                if on_error:
                    on_error(msg)
            else:
                msg = f"❌ Voice error: {exc}"
                logger.error(msg, exc_info=True)
                if on_error:
                    on_error(msg)
        finally:
            self._is_listening = False
            if on_level:
                on_level(0.0)
            if on_stop:
                on_stop()

    # ── PyAudio fallback ──────────────────────────────────────────────────────

    def _listen_pyaudio(self, on_result, on_error, on_start, on_stop, on_level):
        import speech_recognition as sr

        self._is_listening = True
        if on_start:
            on_start()

        try:
            with sr.Microphone() as source:
                logger.info("Adjusting for ambient noise…")
                self._recognizer.adjust_for_ambient_noise(source, duration=0.5)
                logger.info("Listening (PyAudio)…")
                audio = self._recognizer.listen(
                    source,
                    timeout=VOICE_TIMEOUT,
                    phrase_time_limit=VOICE_PHRASE_LIMIT,
                )

            text = self._recognizer.recognize_google(audio)
            logger.info(f"Recognised: '{text}'")
            if on_result:
                on_result(text)

        except sr.WaitTimeoutError:
            msg = "⏱️  No speech detected. Please try again."
            if on_error:
                on_error(msg)
        except sr.UnknownValueError:
            msg = "🤔 Couldn't understand. Please speak clearly."
            if on_error:
                on_error(msg)
        except sr.RequestError as exc:
            msg = f"❌ STT service error: {exc}"
            if on_error:
                on_error(msg)
        except Exception as exc:
            msg = f"❌ Unexpected voice error: {exc}"
            logger.error(msg, exc_info=True)
            if on_error:
                on_error(msg)
        finally:
            self._is_listening = False
            if on_stop:
                on_stop()
