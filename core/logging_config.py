"""
core/logging_config.py — Centralized structured logging for BA Agent.
"""
import logging
import sys
from datetime import datetime


_FORMATTER = logging.Formatter(
    fmt="[%(levelname)s] %(asctime)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)


def setup_logging(level: int = logging.INFO) -> None:
    """Call once at application startup to configure the root logger."""
    root = logging.getLogger()
    if root.handlers:
        # Already configured (e.g., Streamlit re-runs)
        return
    root.setLevel(level)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(_FORMATTER)
    root.addHandler(handler)


def get_logger(name: str) -> logging.Logger:
    """
    Return a named logger.  All modules should use this instead of
    calling logging.getLogger() directly.
    """
    return logging.getLogger(name)
