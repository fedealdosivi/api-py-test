"""Fixtures for the beauty-salons API tests.

These tests expect the API to run with the seed data from the beauty-salons
repo (migrations/002_seed_data.sql) already synced to Elasticsearch.
"""

import pytest

from api_client.services.beauty_salons import BeautySalonsApi


@pytest.fixture
def api(client):
    return BeautySalonsApi(client)
