"""Logger padrão do projeto."""

from __future__ import annotations

import logging
import os

_FORMAT = "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s"


def get_logger(name: str) -> logging.Logger:
    """Logger com formato único. Nível via LOG_LEVEL (padrão INFO)."""
    if not logging.getLogger().handlers:
        logging.basicConfig(
            level=os.getenv("LOG_LEVEL", "INFO"), format=_FORMAT, datefmt="%H:%M:%S"
        )
    return logging.getLogger(name)
