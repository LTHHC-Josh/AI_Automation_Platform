import requests

from .auth import GraphAuthenticator


class GraphClient:
    BASE_URL = "https://graph.microsoft.com/v1.0"

    def __init__(self):
        self.auth = GraphAuthenticator()

    def _headers(self) -> dict:
        return {
            "Authorization": (
                f"Bearer {self.auth.get_access_token()}"
            ),
            "Content-Type": "application/json",
        }

    def get(
        self,
        endpoint: str,
        params: dict | None = None,
    ):
        response = requests.get(
            f"{self.BASE_URL}{endpoint}",
            headers=self._headers(),
            params=params,
            timeout=30,
        )

        response.raise_for_status()

        if not response.content:
            return {}

        return response.json()

    def post(
        self,
        endpoint: str,
        payload: dict,
    ):
        response = requests.post(
            f"{self.BASE_URL}{endpoint}",
            headers=self._headers(),
            json=payload,
            timeout=30,
        )

        response.raise_for_status()

        if not response.content:
            return {}

        return response.json()

    def patch(
        self,
        endpoint: str,
        payload: dict,
    ):
        response = requests.patch(
            f"{self.BASE_URL}{endpoint}",
            headers=self._headers(),
            json=payload,
            timeout=30,
        )

        response.raise_for_status()

        if not response.content:
            return {}

        return response.json()