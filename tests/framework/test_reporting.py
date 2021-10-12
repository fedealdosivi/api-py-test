"""Checks that reports are produced and that failing tests carry their API calls."""

from pathlib import Path

import pytest

pytest_plugins = ["pytester"]

ROOT = Path(__file__).resolve().parents[2]

FAILING_API_TEST = """
import os

import responses

@responses.activate
def test_user_lookup(client):
    responses.get("https://api.example.com/users/1", json={"error": "not found"}, status=404)
    client.set_token(os.environ["SAMPLE_TOKEN"])

    assert client.get("/users/1").status_code == 200
"""


@pytest.fixture
def project(pytester, monkeypatch):
    for key in ("API_ENV", "API_BASE_URL"):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("SAMPLE_TOKEN", "secret-token")
    pytester.makeconftest((ROOT / "tests" / "conftest.py").read_text())
    pytester.makeini((ROOT / "pytest.ini").read_text().replace("pythonpath = .", f"pythonpath = {ROOT}"))
    return pytester


def test_html_and_junit_reports_are_written(project):
    project.makepyfile("def test_ok(): pass")

    project.runpytest().assert_outcomes(passed=1)

    junit = (project.path / "reports" / "junit.xml").read_text()
    assert (project.path / "reports" / "report.html").exists()
    assert 'name="base_url" value="https://api.example.com"' in junit


def test_failed_test_shows_its_api_calls(project):
    project.makepyfile(FAILING_API_TEST)

    result = project.runpytest()

    result.assert_outcomes(failed=1)
    result.stdout.fnmatch_lines(["*API calls*", "#1 GET https://api.example.com/users/1 -> 404*"])
    junit = (project.path / "reports" / "junit.xml").read_text()
    assert "not found" in junit


def test_tokens_are_masked_in_reports(project):
    project.makepyfile(FAILING_API_TEST)

    result = project.runpytest()

    assert "secret-token" not in result.stdout.str()
    assert "secret-token" not in (project.path / "reports" / "junit.xml").read_text()
    assert "secret-token" not in (project.path / "reports" / "report.html").read_text()
