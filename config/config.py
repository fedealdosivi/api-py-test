"""Configuration loader.

Reads ``environments.ini`` and returns its ``[DEFAULT]`` values, or a named
section when ``env`` or ``API_ENV`` is set (sections inherit ``[DEFAULT]``). Any value can
be overridden with an ``API_<KEY>`` environment variable, which is how CI/CD
changes settings without editing the file.
"""

import configparser
import os
from dataclasses import dataclass
from pathlib import Path

INI_PATH = Path(__file__).with_name("environments.ini")


@dataclass(frozen=True)
class Config:
    base_url: str
    timeout: float
    retries: int
    verify_ssl: bool


def load_config(ini_path: Path = INI_PATH, env: str | None = None) -> Config:
    parser = configparser.ConfigParser()
    parser.read(ini_path, encoding="utf-8")

    env = env or os.getenv("API_ENV")
    section = parser[env] if env else parser.defaults()
    values = {key: os.getenv(f"API_{key.upper()}", value) for key, value in section.items()}

    return Config(
        base_url=values["base_url"].rstrip("/"),
        timeout=float(values["timeout"]),
        retries=int(values["retries"]),
        verify_ssl=values["verify_ssl"].lower() == "true",
    )
