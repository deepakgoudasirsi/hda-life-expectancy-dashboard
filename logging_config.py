"""Central logging configuration for the NXP health dashboard project."""

from __future__ import annotations

import logging
from typing import Final

DEFAULT_LOG_FORMAT: Final[str] = (
    "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
)
DEFAULT_DATE_FORMAT: Final[str] = "%Y-%m-%d %H:%M:%S"


def configure_logging(level: int = logging.INFO) -> None:
    """Configure root logging once for CLI scripts and batch jobs."""
    root_logger = logging.getLogger()
    if root_logger.handlers:
        root_logger.setLevel(level)
        return

    logging.basicConfig(
        level=level,
        format=DEFAULT_LOG_FORMAT,
        datefmt=DEFAULT_DATE_FORMAT,
    )


def get_logger(name: str) -> logging.Logger:
    """Return a module logger with consistent naming."""
    return logging.getLogger(name)
