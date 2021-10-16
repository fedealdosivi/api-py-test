"""Builder pattern for complex API requests."""

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping

HTTP_METHODS = {"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"}


@dataclass(frozen=True)
class ApiRequest:
    method: str
    path: str
    headers: Mapping[str, str] = field(default_factory=dict)
    params: Mapping[str, Any] = field(default_factory=dict)
    body: Any = None


class RequestBuilder:
    def __init__(self):
        self._method: str | None = None
        self._path: str | None = None
        self._headers: dict[str, str] = {}
        self._params: dict[str, Any] = {}
        self._body: Any = None

    def method(self, method: str) -> "RequestBuilder":
        method = method.upper()
        if method not in HTTP_METHODS:
            raise ValueError(f"Unsupported HTTP method: {method}")
        self._method = method
        return self

    def path(self, path: str) -> "RequestBuilder":
        self._path = path
        return self

    def get(self, path: str) -> "RequestBuilder":
        return self.method("GET").path(path)

    def post(self, path: str) -> "RequestBuilder":
        return self.method("POST").path(path)

    def put(self, path: str) -> "RequestBuilder":
        return self.method("PUT").path(path)

    def patch(self, path: str) -> "RequestBuilder":
        return self.method("PATCH").path(path)

    def delete(self, path: str) -> "RequestBuilder":
        return self.method("DELETE").path(path)

    def header(self, name: str, value: str) -> "RequestBuilder":
        self._headers[name] = value
        return self

    def query(self, **params: Any) -> "RequestBuilder":
        self._params.update({key: value for key, value in params.items() if value is not None})
        return self

    def json(self, body: Any) -> "RequestBuilder":
        self._body = body
        return self

    def bearer(self, token: str) -> "RequestBuilder":
        return self.header("Authorization", f"Bearer {token}")

    def build(self) -> ApiRequest:
        if not self._method or not self._path:
            raise ValueError("request needs a method and a path before build()")
        if self._body is not None and self._method in {"GET", "HEAD", "DELETE"}:
            raise ValueError(f"{self._method} requests should not have a body")
        return ApiRequest(
            method=self._method,
            path=self._path,
            headers=MappingProxyType(dict(self._headers)),
            params=MappingProxyType(dict(self._params)),
            body=self._body,
        )


class JsonRequestBuilder(RequestBuilder):
    def __init__(self):
        super().__init__()
        self.header("Content-Type", "application/json").header("Accept", "application/json")


class AuthenticatedRequestBuilder(JsonRequestBuilder):
    def __init__(self, token: str):
        super().__init__()
        self.bearer(token)


class RequestDirector:
    """Pagination parameter names differ between APIs, so they are configurable."""

    def __init__(self, limit_param: str = "limit", offset_param: str = "skip"):
        self.limit_param = limit_param
        self.offset_param = offset_param

    def paginated_list(self, builder: RequestBuilder, path: str, limit: int, offset: int = 0) -> ApiRequest:
        return builder.get(path).query(**{self.limit_param: limit, self.offset_param: offset}).build()

    def search(self, builder: RequestBuilder, path: str, term: str, limit: int | None = None) -> ApiRequest:
        return builder.get(path).query(q=term, **{self.limit_param: limit}).build()

    def create(self, builder: RequestBuilder, path: str, payload: Any) -> ApiRequest:
        return builder.post(path).json(payload).build()
