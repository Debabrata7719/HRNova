"""
Centralized logging configuration for NovaHR.
Import `get_logger` in any module instead of using print().

Usage:
    from src.logger import get_logger
    logger = get_logger(__name__)
    logger.info("Something happened")
    logger.error("Something failed: %s", error)
"""

import logging
import sys


def get_logger(name: str) -> logging.Logger:
    """
    Return a logger for the given module name.
    Configures a StreamHandler on first call.
    """
    logger = logging.getLogger(name)

    # Only add handler if none exist (avoid duplicate handlers on reload)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(
            logging.Formatter(
                fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
        logger.addHandler(handler)

    logger.setLevel(logging.INFO)
    logger.propagate = False
    return logger
