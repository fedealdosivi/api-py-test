import math

import pytest

from api_client.services.beauty_salons import salons_in
from utilities.schema import assert_schema
from utilities.test_data import load_cases


@pytest.mark.smoke
def test_search_matches_schema(api):
    response = api.search(q="Peluquería")

    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith("application/json")
    assert_schema(response.json(), "search_response.json")


@pytest.mark.regression
@pytest.mark.parametrize(("params", "total"), load_cases("search_cases.json", "params", "total"))
def test_search_filters(api, params, total):
    """Cases live in test_data/search_cases.json; totals come from the API's seed data."""
    response = api.search(**params)

    assert response.status_code == 200
    assert response.json()["total"] == total


@pytest.mark.regression
def test_filtered_results_respect_every_filter(api):
    response = api.search(
        city="Mar del Plata", category=2, price_range=3, min_rating=4.5, verified="true", page_size=100
    )

    found = salons_in(response)
    assert found
    for salon in found:
        assert salon["location"]["city"] == "Mar del Plata"
        assert salon["category_id"] == 2
        assert salon["price_range"] == 3
        assert salon["rating"] >= 4.5
        assert salon["is_verified"] is True


@pytest.mark.regression
def test_geo_search_returns_distances_within_the_radius(api):
    response = api.search(lat=-38.0, lon=-57.55, radius=2, sort="distance", page_size=100)

    distances = [result["distance_km"] for result in response.json()["results"]]
    assert distances
    assert all(distance <= 2 for distance in distances)
    assert distances == sorted(distances)


@pytest.mark.regression
def test_sort_by_rating(api):
    ratings = [salon["rating"] for salon in salons_in(api.search(sort="rating", page_size=100))]

    assert ratings == sorted(ratings, reverse=True)


@pytest.mark.regression
@pytest.mark.xfail(
    strict=True,
    reason=(
        "sort=newest returns 500: the query sorts on created_at "
        "(internal/search/elasticsearch.go:486) but the index mapping never defines that field. "
        "The error also leaks the raw Elasticsearch message to the client."
    ),
)
def test_sort_by_newest(api):
    assert api.search(sort="newest").status_code == 200


@pytest.mark.regression
@pytest.mark.parametrize("page_size", [4, 10])
def test_pages_cover_every_salon_once(api, page_size):
    first = api.search(page_size=page_size).json()
    assert first["total_pages"] == math.ceil(first["total"] / page_size)

    ids = []
    for page in range(1, first["total_pages"] + 1):
        body = api.search(page=page, page_size=page_size).json()
        assert body["page"] == page
        assert len(body["results"]) <= page_size
        ids += [result["salon"]["id"] for result in body["results"]]

    assert len(ids) == first["total"]
    assert len(set(ids)) == len(ids), "a salon appeared on more than one page"


@pytest.mark.regression
def test_page_past_the_end_is_empty_but_keeps_the_total(api):
    total = api.search().json()["total"]

    body = api.search(page=99).json()

    assert body["results"] == []
    assert body["total"] == total


@pytest.mark.regression
@pytest.mark.parametrize(
    "params",
    [{"page": -3, "page_size": 0}, {"page": "abc", "page_size": "abc"}],
    ids=["out-of-range", "not-a-number"],
)
def test_invalid_pagination_falls_back_to_defaults(api, params):
    response = api.search(**params)

    assert response.status_code == 200
    assert (response.json()["page"], response.json()["page_size"]) == (1, 10)


@pytest.mark.regression
@pytest.mark.xfail(
    strict=True,
    reason=(
        "Search results embed the category with id 0: the indexed document only keeps the "
        "category name, and results are rebuilt as Category{Name: ...} "
        "(internal/search/elasticsearch.go:725)."
    ),
)
def test_embedded_category_matches_category_id(api):
    mismatched = {
        salon["id"]: (salon["category_id"], salon["category"]["id"])
        for salon in salons_in(api.search(page_size=100))
        if salon["category"]["id"] != salon["category_id"]
    }

    assert not mismatched, f"salon id: (category_id, category.id) -> {mismatched}"
