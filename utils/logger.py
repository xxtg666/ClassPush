import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path


def setup_logging():
    log_dir = Path(__file__).parent.parent / "logs"
    os.makedirs(log_dir, exist_ok=True)

    logger = logging.getLogger("classpush")
    logger.setLevel(logging.DEBUG)

    if not logger.handlers:
        file_handler = RotatingFileHandler(
            str(log_dir / "classpush.log"),
            maxBytes=5 * 1024 * 1024,
            backupCount=3,
            encoding="utf-8",
        )
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(
            logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
        )

        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(
            logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
        )

        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    return logger
