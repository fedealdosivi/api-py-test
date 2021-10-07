import pytest
import responses

from api_client.base_client import BaseClient
from config.config import Config


@pytest.fixture
def client():
    config = Config(base_url="https://api.example.com", timeout=5, retries=3, verify_ssl=True)
    return BaseClient(config)


@responses.activate
def test_paths_are_resolved_against_base_url(client):
    responses.get("https://api.example.com/users/1", json={"id": 1})

    response = client.get("/users/1")

    assert response.status_code == 200
    assert response.json() == {"id": 1}


@responses.activate
def test_token_is_sent_on_every_request(client):
    responses.get("https://api.example.com/me", json={})
    client.set_token("abc123")

    client.get("me")

    assert responses.calls[0].request.headers["Authorization"] == "Bearer abc123"


def test_retries_come_from_config(client):
    adapter = client.session.get_adapter("https://api.example.com")

    assert adapter.max_retries.total == 3
    assert 503 in adapter.max_retries.status_forcelist
