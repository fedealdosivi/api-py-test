import pytest
import responses

from api_client.base_client import BaseClient
from api_client.request_builder import (
    AuthenticatedRequestBuilder,
    JsonRequestBuilder,
    RequestBuilder,
    RequestDirector,
)
from config.config import Config


def test_builder_assembles_a_request_step_by_step():
    request = RequestBuilder().get("/products/search").query(q="phone", limit=5).header("X-Trace", "1").build()

    assert request.method == "GET"
    assert request.path == "/products/search"
    assert dict(request.params) == {"q": "phone", "limit": 5}
    assert dict(request.headers) == {"X-Trace": "1"}


def test_built_request_cannot_be_changed():
    request = RequestBuilder().get("/users").build()

    with pytest.raises(TypeError):
        request.headers["Authorization"] = "Bearer stolen"


def test_query_skips_values_left_as_none():
    request = RequestBuilder().get("/users").query(limit=10, skip=None).build()

    assert dict(request.params) == {"limit": 10}


@pytest.mark.parametrize(
    "builder, message",
    [
        (RequestBuilder().path("/users"), "method and a path"),
        (RequestBuilder().get("/users").json({"a": 1}), "should not have a body"),
    ],
)
def test_invalid_requests_fail_at_build_time(builder, message):
    with pytest.raises(ValueError, match=message):
        builder.build()


def test_concrete_builders_start_from_their_presets():
    json_request = JsonRequestBuilder().get("/users").build()
    auth_request = AuthenticatedRequestBuilder("abc").get("/auth/me").build()

    assert json_request.headers["Content-Type"] == "application/json"
    assert "Authorization" not in json_request.headers
    assert auth_request.headers["Authorization"] == "Bearer abc"
    assert auth_request.headers["Content-Type"] == "application/json"


def test_director_builds_common_recipes():
    director = RequestDirector()

    page = director.paginated_list(JsonRequestBuilder(), "/products", limit=10, offset=20)
    search = director.search(JsonRequestBuilder(), "/products/search", "phone")
    create = director.create(JsonRequestBuilder(), "/products/add", {"title": "Phone"})

    assert dict(page.params) == {"limit": 10, "skip": 20}
    assert dict(search.params) == {"q": "phone"}
    assert (create.method, create.body) == ("POST", {"title": "Phone"})


def test_director_supports_other_pagination_names():
    request = RequestDirector(limit_param="per_page", offset_param="page").paginated_list(
        RequestBuilder(), "/users", limit=50, offset=2
    )

    assert dict(request.params) == {"per_page": 50, "page": 2}


@responses.activate
def test_client_sends_a_built_request():
    responses.post(
        "https://api.example.com/products/add",
        match=[
            responses.matchers.query_param_matcher({"draft": "true"}),
            responses.matchers.json_params_matcher({"title": "Phone"}),
            responses.matchers.header_matcher({"Authorization": "Bearer abc"}),
        ],
        json={"id": 195},
        status=201,
    )
    client = BaseClient(Config(base_url="https://api.example.com", timeout=5, retries=0, verify_ssl=True))
    request = AuthenticatedRequestBuilder("abc").post("/products/add").query(draft="true").json({"title": "Phone"}).build()

    response = client.send(request)

    assert response.status_code == 201
    assert response.json() == {"id": 195}
