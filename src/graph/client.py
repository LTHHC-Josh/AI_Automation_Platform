import requests
from collections.abc import Mapping

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
        operation_category: str = "graph_request",
    ):
        return self._request(
            request_method=requests.get,
            endpoint=endpoint,
            params=params,
            operation_category=operation_category,
        )

    def post(
        self,
        endpoint: str,
        payload: dict,
        operation_category: str = "graph_request",
    ):
        return self._request(
            request_method=requests.post,
            endpoint=endpoint,
            json=payload,
            operation_category=operation_category,
        )

    def patch(
        self,
        endpoint: str,
        payload: dict,
        operation_category: str = "graph_request",
    ):
        return self._request(
            request_method=requests.patch,
            endpoint=endpoint,
            json=payload,
            operation_category=operation_category,
        )

    def _request(
        self,
        *,
        request_method,
        endpoint: str,
        operation_category: str = "graph_request",
        **kwargs,
    ):
        failure_category = None
        failure_status_code = None
        failure_response_present = False
        failure_content_type = None
        failure_kind = "unknown"
        response = None
        error_response = None

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
            failure_kind = "http_error"
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

        except requests.Timeout as error:
            failure_category = "graph_request_failed"
            failure_kind = "timeout"
            error_response = getattr(
                error,
                "response",
                None,
            )

        except requests.ConnectionError as error:
            failure_category = "graph_request_failed"
            failure_kind = "connection"
            error_response = getattr(
                error,
                "response",
                None,
            )

        except requests.RequestException as error:
            failure_category = "graph_request_failed"
            failure_kind = "request_error"
            error_response = getattr(
                error,
                "response",
                None,
            )

            if error_response is None:
                error_response = response

        except ValueError:
            failure_category = "graph_request_failed"
            failure_kind = "response_decode"
            error_response = response

        failure_status_code = getattr(
            error_response,
            "status_code",
            None,
        )
        failure_response_present = (
            error_response is not None
        )
        failure_content_type = (
            self._get_content_type(
                error_response
            )
        )

        response = None
        error_response = None
        kwargs.clear()

        if failure_category == "authorization_failed":
            raise GraphAuthorizationError()

        raise GraphRequestError(
            status_code=failure_status_code,
            operation_category=operation_category,
            response_present=failure_response_present,
            response_content_type=failure_content_type,
            failure_kind=failure_kind,
        )

    @staticmethod
    def _get_content_type(response):
        headers = getattr(
            response,
            "headers",
            None,
        )

        if not isinstance(headers, Mapping):
            return None

        return headers.get(
            "Content-Type"
        )
