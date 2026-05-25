from __future__ import annotations

import logging
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path


def configure_logging(debug: bool = False) -> logging.Logger:
    log_dir = Path.home() / "Library" / "Logs" / "Parrot Studio"
    log_dir.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("parrot")
    logger.setLevel(logging.DEBUG if debug else logging.INFO)
    if not logger.handlers:
        handler = TimedRotatingFileHandler(log_dir / "parrot_studio.log", when="midnight", backupCount=7)
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
        logger.addHandler(handler)
    return logger
