import requests

from api_client.base_client import BaseClient
from api_client.request_builder import RequestBuilder


def salons_in(response: requests.Response) -> list[dict]:
    return [result["salon"] for result in response.json()["results"]]


class BeautySalonsApi:
    def __init__(self, client: BaseClient):
        self.client = client

    def health(self) -> requests.Response:
        return self.client.get("/health")

    def categories(self) -> requests.Response:
        return self.client.get("/api/v1/categories")

    def salon(self, salon_id) -> requests.Response:
        return self.client.get(f"/api/v1/salons/{salon_id}")

    def search(self, **params) -> requests.Response:
        """``params`` are the API's query parameters: q, city, category, page, page_size, sort..."""
        request = RequestBuilder().get("/api/v1/search").query(**params).build()
        return self.client.send(request)

    def sync(self) -> requests.Response:
        return self.client.post("/api/v1/admin/sync")

    def cluster_health(self) -> requests.Response:
        return self.client.get("/api/v1/admin/cluster/health")
