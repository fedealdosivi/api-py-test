"""Generic HTTP client every service builds on.

It knows nothing about a specific API. It takes a ``Config`` and gives you paths resolved against ``base_url``

"""

import logging
import time

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from config.config import Config

logger = logging.getLogger(__name__)

RETRY_STATUSES = (429, 500, 502, 503, 504)


class BaseClient:
    def __init__(self, config: Config, session: requests.Session | None = None):
        self.config = config
        self.session = session or requests.Session()
        self.session.headers.update({"Accept": "application/json"})
        self.history: list[requests.Response] = []

        retry = Retry(
            total=config.retries,
            backoff_factor=0.5,
            status_forcelist=RETRY_STATUSES,
            allowed_methods=None,
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retry)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def set_token(self, token: str) -> None:
        self.session.headers["Authorization"] = f"Bearer {token}"

    def clear_token(self) -> None:
        self.session.headers.pop("Authorization", None)

    def url(self, path: str) -> str:
        return f"{self.config.base_url}/{path.lstrip('/')}"

    def request(self, method: str, path: str, **kwargs) -> requests.Response:
        kwargs.setdefault("timeout", self.config.timeout)
        kwargs.setdefault("verify", self.config.verify_ssl)
        url = self.url(path)

        start = time.perf_counter()
        response = self.session.request(method, url, **kwargs)
        elapsed_ms = (time.perf_counter() - start) * 1000

        logger.info("%s %s -> %s (%.0f ms)", method.upper(), url, response.status_code, elapsed_ms)
        self.history.append(response)
        return response

    def get(self, path: str, **kwargs) -> requests.Response:
        return self.request("GET", path, **kwargs)

    def post(self, path: str, **kwargs) -> requests.Response:
        return self.request("POST", path, **kwargs)

    def put(self, path: str, **kwargs) -> requests.Response:
        return self.request("PUT", path, **kwargs)

    def patch(self, path: str, **kwargs) -> requests.Response:
        return self.request("PATCH", path, **kwargs)

    def delete(self, path: str, **kwargs) -> requests.Response:
        return self.request("DELETE", path, **kwargs)
