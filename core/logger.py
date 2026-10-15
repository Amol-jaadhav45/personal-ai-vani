"""
core/logger.py
==============
Provides a pre-configured logger used by every module.
Writes to both the console (INFO level) and a rotating log file (DEBUG level).
"""

import logging
import sys
from logging.handlers import RotatingFileHandler
from config.settings import LOGS_DIR, APP_NAME


def get_logger(name: str) -> logging.Logger:
    """
    Return a named logger with console + rotating-file handlers.

    Usage:
        from core.logger import get_logger
        logger = get_logger(__name__)
        logger.info("Hello")
    """
    logger = logging.getLogger(name)

    # Avoid adding duplicate handlers when the function is called multiple times
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)

    # ── Formatter ─────────────────────────────────────────────────────────────
    fmt = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # ── Console handler (INFO and above) ──────────────────────────────────────
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(fmt)

    # ── Rotating file handler (DEBUG and above, max 5 MB × 3 backups) ─────────
    log_file = LOGS_DIR / f"{APP_NAME.replace(' ', '_').lower()}.log"
    file_handler = RotatingFileHandler(
        filename=log_file,
        maxBytes=5 * 1024 * 1024,  # 5 MB
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(fmt)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger
