"""
Central logging configuration for the LTHHC AI Platform.
"""

import logging
from pathlib import Path

from src.core.config import Config


def get_logger(name: str) -> logging.Logger:
    """
    Returns a configured logger instance.

    Parameters
    ----------
    name : str
        Name of the logger.

    Returns
    -------
    logging.Logger
    """

    log_directory = Path(Config.LOG_DIR)
    log_directory.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    logger.setLevel(getattr(logging, Config.LOG_LEVEL.upper()))

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    # Console output
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    # Log file
    file_handler = logging.FileHandler(
        log_directory / "lthhc_ai.log",
        encoding="utf-8"
    )
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger