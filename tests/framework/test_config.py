import pytest

from config.config import load_config

INI = """
[DEFAULT]
base_url = https://api.example.com
timeout = 5
retries = 2
verify_ssl = true

[qa]
base_url = https://qa.example.com/
verify_ssl = false
"""


@pytest.fixture
def ini(tmp_path):
    path = tmp_path / "environments.ini"
    path.write_text(INI)
    return path


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    for key in ("API_ENV", "API_BASE_URL", "API_TIMEOUT", "API_RETRIES", "API_VERIFY_SSL"):
        monkeypatch.delenv(key, raising=False)


def test_defaults_used_when_no_env_selected(ini):
    config = load_config(ini)

    assert config.base_url == "https://api.example.com"
    assert config.timeout == 5.0
    assert config.retries == 2
    assert config.verify_ssl is True


