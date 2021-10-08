"""Logging setup shared by the whole framework.
"""

import logging
import os
from pathlib import Path

LOG_FORMAT = "%(asctime)s %(levelname)-7s %(name)s: %(message)s"
DEFAULT_LOG_FILE = Path("logs") / "test_run.log"


def setup_logging(log_file: Path = DEFAULT_LOG_FILE) -> None:
    level = os.getenv("API_LOG_LEVEL", "INFO").upper()
    log_file.parent.mkdir(parents=True, exist_ok=True)

    root = logging.getLogger()
    root.setLevel(level)
    for handler in list(root.handlers):
        if getattr(handler, "_framework", False):
            root.removeHandler(handler)
            handler.close()

    for handler in (logging.StreamHandler(), logging.FileHandler(log_file, encoding="utf-8")):
        handler.setFormatter(logging.Formatter(LOG_FORMAT))
        handler._framework = True
        root.addHandler(handler)
