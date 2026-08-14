import requests

from .auth import GraphAuthenticator
from .errors import (
    GraphAuthorizationError,
    GraphRequestError,
)


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
        return self._request(
            request_method=requests.get,
            endpoint=endpoint,
            params=params,
        )

    def post(
        self,
        endpoint: str,
        payload: dict,
    ):
        return self._request(
            request_method=requests.post,
            endpoint=endpoint,
            json=payload,
        )

    def patch(
        self,
        endpoint: str,
        payload: dict,
    ):
        return self._request(
            request_method=requests.patch,
            endpoint=endpoint,
            json=payload,
        )

    def _request(
        self,
        *,
        request_method,
        endpoint: str,
        **kwargs,
    ):
        failure_category = None
        response = None

        try:
            response = request_method(
                f"{self.BASE_URL}{endpoint}",
                headers=self._headers(),
                timeout=30,
                **kwargs,
            )

            response.raise_for_status()

            if not response.content:
                return {}

            return response.json()

        except requests.HTTPError as error:
            error_response = getattr(
                error,
                "response",
                None,
            )
            status_code = getattr(
                error_response,
                "status_code",
                None,
            )

            if status_code in {
                401,
                403,
            }:
                failure_category = "authorization_failed"
            else:
                failure_category = "graph_request_failed"

        except (
            requests.RequestException,
            ValueError,
        ):
            failure_category = "graph_request_failed"

        response = None
        kwargs.clear()

        if failure_category == "authorization_failed":
            raise GraphAuthorizationError()

        raise GraphRequestError()
