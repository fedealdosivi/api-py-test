"""Checks the shared conftest by running a small pytest session against it."""

from pathlib import Path

import pytest

pytest_plugins = ["pytester"]

ROOT = Path(__file__).resolve().parents[2]

INI = """
[DEFAULT]
base_url = https://api.example.com
timeout = 10
retries = 2
verify_ssl = true

[qa]
base_url = https://qa.example.com
"""


@pytest.fixture
def project(pytester, monkeypatch):
    """A throwaway project wired to this repo's conftest and a sample environments.ini."""
    monkeypatch.delenv("API_ENV", raising=False)
    monkeypatch.delenv("API_BASE_URL", raising=False)
    ini = pytester.path / "environments.ini"
    ini.write_text(INI)
    conftest = (ROOT / "tests" / "conftest.py").read_text()
    pytester.makeconftest(conftest.replace("load_config(env=", f"load_config({str(ini)!r}, env="))
    pytester.makeini((ROOT / "pytest.ini").read_text().replace("pythonpath = .", f"pythonpath = {ROOT}"))
    return pytester


def test_env_option_selects_the_section(project):
    project.makepyfile("def test_url(config): assert config.base_url == 'https://qa.example.com'")

    project.runpytest("--env", "qa").assert_outcomes(passed=1)


def test_client_fixture_uses_the_config(project):
    project.makepyfile("def test_url(client): assert client.url('/x') == 'https://api.example.com/x'")

    project.runpytest().assert_outcomes(passed=1)


def test_unknown_markers_are_rejected(project):
    project.makepyfile(
        """
        import pytest

        @pytest.mark.smoek
        def test_typo():
            pass
        """
    )

    result = project.runpytest()

    result.assert_outcomes(errors=1)
    result.stdout.fnmatch_lines(["*'smoek' not found in `markers`*"])


def test_unknown_env_stops_the_run(project):
    project.makepyfile("def test_anything(): pass")

    result = project.runpytest("--env", "staging")

    assert result.ret == pytest.ExitCode.USAGE_ERROR
    result.stderr.fnmatch_lines(["*no [[]staging[]] section*"])
