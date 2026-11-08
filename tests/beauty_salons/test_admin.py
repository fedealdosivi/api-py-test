import pytest

pytestmark = pytest.mark.regression


def test_sync_makes_every_synced_salon_searchable(api):
    response = api.sync()

    assert response.status_code == 200
    assert response.json()["count"] == api.search().json()["total"]


def test_cluster_health_is_usable(api):
    response = api.cluster_health()

    assert response.status_code == 200
    assert response.json()["status"] in {"green", "yellow"}
