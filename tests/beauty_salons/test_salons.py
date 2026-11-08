import pytest

from api_client.services.beauty_salons import salons_in
from utilities.schema import assert_schema

SHARED_FIELDS = ("name", "slug", "category_id", "price_range", "rating", "is_verified")


@pytest.fixture
def salon_and_search_result(api):
    found = {salon["id"]: salon for salon in salons_in(api.search(page_size=100))}
    return api.salon(2).json(), found[2]


@pytest.mark.smoke
def test_get_salon_by_id(api):
    response = api.salon(2)

    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith("application/json")
    salon = response.json()
    assert_schema(salon, "salon.json")
    assert salon["id"] == 2


@pytest.mark.regression
def test_salon_details_match_its_search_result(salon_and_search_result):
    salon, result = salon_and_search_result

    assert {field: salon[field] for field in SHARED_FIELDS} == {field: result[field] for field in SHARED_FIELDS}


@pytest.mark.regression
@pytest.mark.xfail(
    strict=True,
    reason=(
        "Search results drop location.postal_code: the indexed document never includes it "
        "(internal/search/elasticsearch.go:606), so search and GET /salons/:id return different addresses."
    ),
)
def test_search_result_keeps_the_full_address(salon_and_search_result):
    salon, result = salon_and_search_result

    assert result["location"] == salon["location"]


@pytest.mark.regression
@pytest.mark.xfail(
    strict=True,
    reason=(
        "Salon 1 is found by search but GET /salons/1 returns 404. Its Sunday row has NULL "
        "open_time/close_time and OperatingHours.OpenTime is a plain string "
        "(internal/domain/salon.go:313), so the scan fails; GetSalon then turns every error into 404."
    ),
)
def test_every_salon_found_by_search_can_be_fetched(api):
    ids = [salon["id"] for salon in salons_in(api.search(page_size=100))]

    failing = {salon_id: status for salon_id in ids if (status := api.salon(salon_id).status_code) != 200}

    assert not failing, f"salon id -> status: {failing}"


@pytest.mark.regression
@pytest.mark.parametrize(
    ("salon_id", "status", "error"),
    [("abc", 400, "Invalid salon ID"), (9999, 404, "Salon not found")],
    ids=["not-a-number", "missing"],
)
def test_bad_salon_ids_are_rejected(api, salon_id, status, error):
    response = api.salon(salon_id)

    assert response.status_code == status
    assert response.json() == {"error": error}
