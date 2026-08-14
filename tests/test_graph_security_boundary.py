import io
import os
from contextlib import redirect_stderr, redirect_stdout
from typing import Any, Callable
from unittest.mock import patch

import requests


os.environ["PYTHON_DOTENV_DISABLED"] = "1"

from src.graph.auth import GraphAuthenticator
from src.graph.client import GraphClient
from src.graph.config import GraphConfig, load_graph_config


SECRET_MARKER = "SYNTHETIC_SECRET_MARKER_DO_NOT_EXPOSE"
TOKEN_MARKER = "SYNTHETIC_TOKEN_MARKER_DO_NOT_EXPOSE"
PROVIDER_MARKER = "SYNTHETIC_PROVIDER_DETAIL_DO_NOT_EXPOSE"


class RecordingTokenApplication:
    def __init__(self, result: dict[str, Any]) -> None:
        self.result = result
        self.calls: list[list[str]] = []

    def acquire_token_for_client(
        self,
        *,
        scopes: list[str],
    ) -> dict[str, Any]:
        self.calls.append(
            list(scopes)
        )
        return dict(
            self.result
        )


class RaisingTokenApplication:
    def acquire_token_for_client(
        self,
        *,
        scopes: list[str],
    ) -> dict[str, Any]:
        raise RuntimeError(
            PROVIDER_MARKER
        )


class FixedAuthenticator:
    def __init__(
        self,
        *,
        token: str | None = None,
        error: Exception | None = None,
    ) -> None:
        self.token = token
        self.error = error
        self.call_count = 0

    def get_access_token(self) -> str:
        self.call_count += 1

        if self.error is not None:
            raise self.error

        return str(
            self.token
            or ""
        )


class SyntheticHttpResponse:
    def __init__(
        self,
        *,
        status_code: int,
        diagnostic_marker: str,
        json_error: Exception | None = None,
    ) -> None:
        self.status_code = status_code
        self.diagnostic_marker = diagnostic_marker
        self.json_error = json_error
        self.content = b"synthetic-response-content"

    def raise_for_status(self) -> None:
        if self.status_code < 400:
            return

        error = requests.HTTPError(
            self.diagnostic_marker
        )
        error.response = self
        raise error

    def json(self) -> dict[str, Any]:
        if self.json_error is not None:
            raise self.json_error

        return {}


def build_authenticator(
    result: dict[str, Any],
) -> tuple[GraphAuthenticator, RecordingTokenApplication]:
    application = RecordingTokenApplication(
        result
    )
    authenticator = GraphAuthenticator.__new__(
        GraphAuthenticator
    )
    authenticator._app = application

    return authenticator, application


def build_client(
    authenticator: Any,
) -> GraphClient:
    client = GraphClient.__new__(
        GraphClient
    )
    client.auth = authenticator
    return client


def capture_runtime_error(
    operation: Callable[[], Any],
) -> tuple[RuntimeError, str]:
    stdout = io.StringIO()
    stderr = io.StringIO()

    with redirect_stdout(stdout), redirect_stderr(stderr):
        try:
            operation()
        except RuntimeError as error:
            return error, stdout.getvalue() + stderr.getvalue()

    raise AssertionError(
        "Expected a sanitized RuntimeError."
    )


def assert_sanitized(
    error: RuntimeError,
    captured_output: str,
    *,
    category: str,
    prohibited_markers: tuple[str, ...],
) -> None:
    rendered = str(
        error
    )
    representation = repr(
        error
    )

    assert getattr(
        error,
        "category",
        None,
    ) == category
    assert error.__context__ is None
    assert error.__cause__ is None

    for marker in prohibited_markers:
        assert marker not in rendered
        assert marker not in representation
        assert marker not in captured_output


def test_invalid_credentials_are_sanitized() -> None:
    authenticator, _ = build_authenticator(
        {
            "error": "invalid_client",
            "error_description": PROVIDER_MARKER,
        }
    )

    error, output = capture_runtime_error(
        authenticator.get_access_token
    )

    assert_sanitized(
        error,
        output,
        category="authentication_failed",
        prohibited_markers=(PROVIDER_MARKER,),
    )


def test_expired_secret_response_is_sanitized() -> None:
    authenticator, _ = build_authenticator(
        {
            "error": "invalid_client",
            "error_description": (
                "expired credential "
                + SECRET_MARKER
            ),
        }
    )

    error, output = capture_runtime_error(
        authenticator.get_access_token
    )

    assert_sanitized(
        error,
        output,
        category="authentication_failed",
        prohibited_markers=(SECRET_MARKER,),
    )


def test_missing_configuration_names_only_variables() -> None:
    with (
        patch(
            "src.graph.config.load_dotenv",
            return_value=False,
        ),
        patch.dict(
            os.environ,
            {},
            clear=True,
        ),
    ):
        error, output = capture_runtime_error(
            load_graph_config
        )

    assert getattr(
        error,
        "category",
        None,
    ) == "configuration_error"
    assert "GRAPH_CLIENT_SECRET" in str(error)
    assert SECRET_MARKER not in str(error)
    assert TOKEN_MARKER not in str(error)
    assert output == ""


def test_insufficient_permission_response_is_sanitized() -> None:
    response = SyntheticHttpResponse(
        status_code=403,
        diagnostic_marker=PROVIDER_MARKER,
    )
    client = build_client(
        FixedAuthenticator(
            token=TOKEN_MARKER
        )
    )

    with patch(
        "src.graph.client.requests.post",
        return_value=response,
    ):
        error, output = capture_runtime_error(
            lambda: client.post(
                "/synthetic-endpoint",
                {"synthetic": True},
            )
        )

    assert_sanitized(
        error,
        output,
        category="authorization_failed",
        prohibited_markers=(
            PROVIDER_MARKER,
            TOKEN_MARKER,
        ),
    )


def test_unauthorized_response_is_sanitized() -> None:
    response = SyntheticHttpResponse(
        status_code=401,
        diagnostic_marker=PROVIDER_MARKER,
    )
    client = build_client(
        FixedAuthenticator(
            token=TOKEN_MARKER
        )
    )

    with patch(
        "src.graph.client.requests.get",
        return_value=response,
    ):
        error, output = capture_runtime_error(
            lambda: client.get(
                "/synthetic-endpoint"
            )
        )

    assert_sanitized(
        error,
        output,
        category="authorization_failed",
        prohibited_markers=(
            PROVIDER_MARKER,
            TOKEN_MARKER,
        ),
    )


def test_forbidden_response_is_sanitized() -> None:
    response = SyntheticHttpResponse(
        status_code=403,
        diagnostic_marker=PROVIDER_MARKER,
    )
    client = build_client(
        FixedAuthenticator(
            token=TOKEN_MARKER
        )
    )

    with patch(
        "src.graph.client.requests.patch",
        return_value=response,
    ):
        error, output = capture_runtime_error(
            lambda: client.patch(
                "/synthetic-endpoint",
                {"synthetic": True},
            )
        )

    assert_sanitized(
        error,
        output,
        category="authorization_failed",
        prohibited_markers=(
            PROVIDER_MARKER,
            TOKEN_MARKER,
        ),
    )


def test_provider_secret_marker_is_not_exposed() -> None:
    authenticator, _ = build_authenticator(
        {
            "error": "invalid_client",
            "error_description": SECRET_MARKER,
        }
    )

    error, output = capture_runtime_error(
        authenticator.get_access_token
    )

    assert_sanitized(
        error,
        output,
        category="authentication_failed",
        prohibited_markers=(SECRET_MARKER,),
    )


def test_provider_token_marker_is_not_exposed() -> None:
    authenticator, _ = build_authenticator(
        {
            "error": "invalid_client",
            "error_description": TOKEN_MARKER,
        }
    )

    error, output = capture_runtime_error(
        authenticator.get_access_token
    )

    assert_sanitized(
        error,
        output,
        category="authentication_failed",
        prohibited_markers=(TOKEN_MARKER,),
    )


def test_verbose_provider_detail_is_not_exposed() -> None:
    authenticator, _ = build_authenticator(
        {
            "error": "invalid_client",
            "error_description": PROVIDER_MARKER,
            "correlation_id": PROVIDER_MARKER,
        }
    )

    error, output = capture_runtime_error(
        authenticator.get_access_token
    )

    assert_sanitized(
        error,
        output,
        category="authentication_failed",
        prohibited_markers=(PROVIDER_MARKER,),
    )


def test_token_provider_exception_is_sanitized() -> None:
    authenticator = GraphAuthenticator.__new__(
        GraphAuthenticator
    )
    authenticator._app = RaisingTokenApplication()

    error, output = capture_runtime_error(
        authenticator.get_access_token
    )

    assert_sanitized(
        error,
        output,
        category="authentication_failed",
        prohibited_markers=(PROVIDER_MARKER,),
    )


def test_authenticator_construction_exception_is_sanitized() -> None:
    config = GraphConfig(
        tenant_id="synthetic-tenant",
        client_id="synthetic-client",
        client_secret=SECRET_MARKER,
        mailbox="synthetic-mailbox",
    )

    with (
        patch(
            "src.graph.auth.load_graph_config",
            return_value=config,
        ),
        patch(
            "src.graph.auth.ConfidentialClientApplication",
            side_effect=RuntimeError(
                PROVIDER_MARKER
            ),
        ),
    ):
        error, output = capture_runtime_error(
            GraphAuthenticator
        )

    assert_sanitized(
        error,
        output,
        category="authentication_failed",
        prohibited_markers=(
            PROVIDER_MARKER,
            SECRET_MARKER,
        ),
    )


def test_successful_token_is_returned_without_output() -> None:
    authenticator, application = build_authenticator(
        {
            "access_token": TOKEN_MARKER,
        }
    )
    stdout = io.StringIO()
    stderr = io.StringIO()

    with redirect_stdout(stdout), redirect_stderr(stderr):
        token = authenticator.get_access_token()

    assert token == TOKEN_MARKER
    assert TOKEN_MARKER not in stdout.getvalue()
    assert TOKEN_MARKER not in stderr.getvalue()
    assert len(application.calls) == 1


def test_successful_graph_request_preserves_response() -> None:
    response = SyntheticHttpResponse(
        status_code=200,
        diagnostic_marker="unused",
    )
    authenticator = FixedAuthenticator(
        token=TOKEN_MARKER
    )
    client = build_client(
        authenticator
    )
    stdout = io.StringIO()
    stderr = io.StringIO()

    with (
        patch(
            "src.graph.client.requests.get",
            return_value=response,
        ) as request,
        redirect_stdout(stdout),
        redirect_stderr(stderr),
    ):
        result = client.get(
            "/synthetic-endpoint"
        )

    assert result == {}
    assert request.call_count == 1
    assert authenticator.call_count == 1
    assert TOKEN_MARKER not in stdout.getvalue()
    assert TOKEN_MARKER not in stderr.getvalue()


def test_auth_failure_prevents_graph_request() -> None:
    authenticator, _ = build_authenticator(
        {
            "error": "invalid_client",
            "error_description": SECRET_MARKER,
        }
    )
    client = build_client(
        authenticator
    )

    with patch(
        "src.graph.client.requests.get"
    ) as request:
        error, output = capture_runtime_error(
            lambda: client.get(
                "/synthetic-endpoint"
            )
        )

    assert request.call_count == 0
    assert_sanitized(
        error,
        output,
        category="authentication_failed",
        prohibited_markers=(SECRET_MARKER,),
    )


def test_blank_token_prevents_graph_request() -> None:
    authenticator, _ = build_authenticator(
        {
            "access_token": "   ",
        }
    )
    client = build_client(
        authenticator
    )

    with patch(
        "src.graph.client.requests.get"
    ) as request:
        error, output = capture_runtime_error(
            lambda: client.get(
                "/synthetic-endpoint"
            )
        )

    assert request.call_count == 0
    assert_sanitized(
        error,
        output,
        category="authentication_failed",
        prohibited_markers=(
            SECRET_MARKER,
            TOKEN_MARKER,
            PROVIDER_MARKER,
        ),
    )


def test_request_exception_is_sanitized() -> None:
    client = build_client(
        FixedAuthenticator(
            token=TOKEN_MARKER
        )
    )

    with patch(
        "src.graph.client.requests.get",
        side_effect=requests.RequestException(
            PROVIDER_MARKER
        ),
    ):
        error, output = capture_runtime_error(
            lambda: client.get(
                "/synthetic-endpoint"
            )
        )

    assert_sanitized(
        error,
        output,
        category="graph_request_failed",
        prohibited_markers=(
            PROVIDER_MARKER,
            TOKEN_MARKER,
        ),
    )


def test_response_decode_exception_is_sanitized() -> None:
    response = SyntheticHttpResponse(
        status_code=200,
        diagnostic_marker="unused",
        json_error=requests.RequestException(
            PROVIDER_MARKER
        ),
    )
    client = build_client(
        FixedAuthenticator(
            token=TOKEN_MARKER
        )
    )

    with patch(
        "src.graph.client.requests.get",
        return_value=response,
    ):
        error, output = capture_runtime_error(
            lambda: client.get(
                "/synthetic-endpoint"
            )
        )

    assert_sanitized(
        error,
        output,
        category="graph_request_failed",
        prohibited_markers=(
            PROVIDER_MARKER,
            TOKEN_MARKER,
        ),
    )


def run_test(
    name: str,
    function: Callable[[], None],
) -> bool:
    try:
        function()
    except Exception as error:
        print(
            f"FAILED: {name}: "
            f"{type(error).__name__}"
        )
        return False

    print(
        f"PASSED: {name}"
    )
    return True


def main() -> None:
    print("=" * 60)
    print("Testing Microsoft Graph Security Boundary")
    print("=" * 60)

    tests = [
        (
            "invalid credentials are sanitized",
            test_invalid_credentials_are_sanitized,
        ),
        (
            "expired secret response is sanitized",
            test_expired_secret_response_is_sanitized,
        ),
        (
            "missing configuration names only variables",
            test_missing_configuration_names_only_variables,
        ),
        (
            "insufficient permission response is sanitized",
            test_insufficient_permission_response_is_sanitized,
        ),
        (
            "unauthorized response is sanitized",
            test_unauthorized_response_is_sanitized,
        ),
        (
            "forbidden response is sanitized",
            test_forbidden_response_is_sanitized,
        ),
        (
            "provider secret marker is not exposed",
            test_provider_secret_marker_is_not_exposed,
        ),
        (
            "provider token marker is not exposed",
            test_provider_token_marker_is_not_exposed,
        ),
        (
            "verbose provider detail is not exposed",
            test_verbose_provider_detail_is_not_exposed,
        ),
        (
            "token provider exception is sanitized",
            test_token_provider_exception_is_sanitized,
        ),
        (
            "authenticator construction exception is sanitized",
            test_authenticator_construction_exception_is_sanitized,
        ),
        (
            "successful token is returned without output",
            test_successful_token_is_returned_without_output,
        ),
        (
            "successful Graph request preserves response",
            test_successful_graph_request_preserves_response,
        ),
        (
            "auth failure prevents Graph request",
            test_auth_failure_prevents_graph_request,
        ),
        (
            "blank token prevents Graph request",
            test_blank_token_prevents_graph_request,
        ),
        (
            "request exception is sanitized",
            test_request_exception_is_sanitized,
        ),
        (
            "response decode exception is sanitized",
            test_response_decode_exception_is_sanitized,
        ),
    ]

    passed = 0
    failed = 0

    for name, function in tests:
        if run_test(
            name,
            function,
        ):
            passed += 1
        else:
            failed += 1

    print()
    print(
        f"Passed: {passed}"
    )
    print(
        f"Failed: {failed}"
    )
    print(
        "Real or mock: Synthetic deterministic/mock test"
    )
    print(
        "Microsoft Graph and MSAL: Mocked"
    )
    print(
        "External integration: Not called"
    )
    print(
        "PHI handling: No protected data accessed"
    )
    print("=" * 60)

    if failed:
        raise SystemExit(
            1
        )


if __name__ == "__main__":
    main()
