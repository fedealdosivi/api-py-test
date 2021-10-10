"""Shared pytest setup for every test in the project.

- ``--env`` picks the section of ``config/environments.ini`` to use
- ``config`` and ``client`` fixtures give any test a ready-to-use API client.
"""

from pathlib import Path

import pytest

from api_client.base_client import BaseClient
from config.config import load_config
from utilities.logger import setup_logging

FRAMEWORK_TESTS = Path(__file__).parent / "framework"


def pytest_addoption(parser):
    parser.addoption(
        "--env",
        action="store",
        default=None,
        help="Environment section of config/environments.ini to run against",
    )


def pytest_configure(config):
    setup_logging()
    env = config.getoption("--env")
    try:
        config.api_config = load_config(env=env)
    except KeyError:
        raise pytest.UsageError(f"--env {env}: no [{env}] section in config/environments.ini")


def pytest_report_header(config):
    return f"api: {config.api_config.base_url} (env: {config.getoption('--env') or 'default'})"


def pytest_collection_modifyitems(items):
    for item in items:
        if FRAMEWORK_TESTS in Path(item.path).parents:
            item.add_marker(pytest.mark.framework)


@pytest.fixture(scope="session")
def config(request):
    return request.config.api_config


@pytest.fixture
def client(config):
    """A fresh client per test, so a token set in one test never leaks into another."""
    api = BaseClient(config)
    yield api
    api.session.close()
