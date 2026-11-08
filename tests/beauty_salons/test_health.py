import pytest

from utilities.schema import assert_schema

pytestmark = pytest.mark.smoke


def test_health_reports_ok(api):
    response = api.health()

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_categories_match_schema(api):
    response = api.categories()

    assert response.status_code == 200
    categories = response.json()
    assert categories, "expected at least one category"
    for category in categories:
        assert_schema(category, "category.json")
    slugs = [category["slug"] for category in categories]
    assert len(slugs) == len(set(slugs)), f"duplicate slugs: {slugs}"


def test_unknown_route_returns_404(api):
    assert api.client.get("/api/v1/does-not-exist").status_code == 404
