import contextlib
import base64
import io
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch

import requests

from src.graph.attachment_service import AttachmentService
from src.graph.client import GraphClient
from src.graph.email_service import EmailService
from src.graph.errors import (
    GraphAuthorizationError,
    GraphRequestError,
)


PROTECTED_MESSAGE_MARKER = "SYNTHETIC_MESSAGE_ID_DO_NOT_EXPOSE"
PROVIDER_MARKER = "SYNTHETIC_PROVIDER_DETAIL_DO_NOT_EXPOSE"
TOKEN_MARKER = "SYNTHETIC_TOKEN_DO_NOT_EXPOSE"


class FixedAuthenticator:
    def get_access_token(self):
        return TOKEN_MARKER


class SyntheticResponse:
    def __init__(
        self,
        *,
        status_code,
        content_type="application/json",
        json_error=None,
    ):
        self.status_code = status_code
        self.content = b"synthetic response"
        self.headers = {
            "Content-Type": content_type,
        }
        self._json_error = json_error

    def raise_for_status(self):
        if self.status_code < 400:
            return

        error = requests.HTTPError(PROVIDER_MARKER)
        error.response = self
        raise error

    def json(self):
        if self._json_error is not None:
            raise self._json_error

        return {
            "value": [],
        }


class RecordingGraphClient:
    def __init__(self):
        self.calls = []

    def get(self, endpoint, params=None, operation_category=None):
        self.calls.append(
            {
                "endpoint": endpoint,
                "params": params,
                "operation_category": operation_category,
            }
        )
        return {
            "value": [],
        }


def build_client():
    client = GraphClient.__new__(GraphClient)
    client.auth = FixedAuthenticator()
    return client


def capture_error(operation, expected_type):
    stdout = io.StringIO()
    stderr = io.StringIO()

    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        try:
            operation()
        except expected_type as error:
            return error, stdout.getvalue(), stderr.getvalue()

    raise AssertionError("Expected sanitized Graph boundary error.")


def assert_no_protected_diagnostics(error, stdout, stderr):
    rendered = repr(error) + str(error) + stdout + stderr

    for marker in (
        PROTECTED_MESSAGE_MARKER,
        PROVIDER_MARKER,
        TOKEN_MARKER,
    ):
        assert marker not in rendered

    assert error.__cause__ is None
    assert error.__context__ is None


def test_attachment_listing_uses_allowlisted_operation_category():
    client = RecordingGraphClient()
    service = AttachmentService.__new__(AttachmentService)
    service.client = client
    service.config = SimpleNamespace(
        mailbox="synthetic-mailbox@example.invalid"
    )

    result = service.get_attachments(PROTECTED_MESSAGE_MARKER)

    assert result == []
    assert len(client.calls) == 1
    assert client.calls[0]["operation_category"] == "attachment_enumeration"
    assert client.calls[0]["params"] is None


def build_attachment_service(client):
    service = AttachmentService.__new__(AttachmentService)
    service.client = client
    service.config = SimpleNamespace(mailbox="synthetic-mailbox@example.invalid")
    return service


def test_attachment_metadata_count_follows_graph_continuation_without_content():
    class PagedClient:
        def __init__(self):
            self.calls = []

        def get(self, endpoint, params=None, operation_category=None):
            self.calls.append((endpoint, params, operation_category))
            if len(self.calls) == 1:
                return {
                    "value": [{"@odata.type": "microsoft.graph.itemAttachment"}],
                    "@odata.nextLink": (
                        "https://graph.microsoft.com/v1.0/users/synthetic/messages/"
                        "synthetic/attachments?$skiptoken=opaque"
                    ),
                }
            return {"value": [{
                "@odata.type": "#microsoft.graph.fileAttachment",
                "isInline": False,
                "name": "PROTECTED.pdf",
            }]}

    client = PagedClient()
    result = build_attachment_service(client).count_supported_file_attachments(
        PROTECTED_MESSAGE_MARKER, supported_extensions={".pdf"}
    )
    assert result.success is True and result.count == 1
    assert client.calls[0][1] == {"$select": "id,name,isInline"}
    assert client.calls[1][1] is None
    assert all(call[2] == "attachment_enumeration" for call in client.calls)
    assert "contentBytes" not in repr(client.calls)
    assert "PROTECTED" not in repr(result)


def test_download_accepts_same_graph_file_type_spellings_as_metadata_proof():
    content = b"synthetic non-PHI document"

    class FixedClient:
        def get(self, *args, **kwargs):
            return {"value": [{
                "@odata.type": "microsoft.graph.fileAttachment",
                "id": "synthetic-attachment",
                "isInline": False,
                "name": "synthetic.pdf",
                "contentBytes": base64.b64encode(content).decode("ascii"),
            }]}

    with TemporaryDirectory() as directory:
        service = build_attachment_service(FixedClient())
        service.download_dir = Path(directory)
        result = service.download_supported_file_attachments(
            PROTECTED_MESSAGE_MARKER,
            supported_extensions={".pdf"},
        )
        assert len(result.candidate_outcomes) == 1
        assert result.candidate_outcomes[0].status == "downloaded"
        assert len(result.downloaded_files) == 1


def test_attachment_metadata_unprovable_reasons_are_allowlisted_and_fail_closed():
    cases = (
        (RuntimeError(PROVIDER_MARKER), "attachment_metadata_request_failed"),
        ({"value": "invalid"}, "attachment_metadata_response_invalid"),
        ({"value": ["invalid"]}, "attachment_metadata_item_invalid"),
        ({"value": [{}]}, "attachment_metadata_type_unprovable"),
        ({"value": [{"@odata.type": "microsoft.graph.fileAttachment"}]},
         "attachment_metadata_inline_state_unprovable"),
        ({"value": [{"@odata.type": "microsoft.graph.fileAttachment",
                     "isInline": False}]}, "attachment_metadata_name_unprovable"),
        ({"value": [], "@odata.nextLink": "https://example.invalid/private"},
         "attachment_metadata_pagination_invalid"),
    )
    for response, reason in cases:
        class FixedClient:
            def get(self, *args, **kwargs):
                if isinstance(response, Exception):
                    raise response
                return response

        result = build_attachment_service(FixedClient()).count_supported_file_attachments(
            PROTECTED_MESSAGE_MARKER, supported_extensions={".pdf"}
        )
        assert result.success is False and result.count is None
        assert result.unprovable_reason == reason
        rendered = repr(result)
        assert PROTECTED_MESSAGE_MARKER not in rendered
        assert PROVIDER_MARKER not in rendered


def test_attachment_metadata_continuation_failure_is_distinguished_and_closed():
    class FailingContinuationClient:
        calls = 0

        def get(self, *args, **kwargs):
            self.calls += 1
            if self.calls == 1:
                return {
                    "value": [],
                    "@odata.nextLink": (
                        "https://graph.microsoft.com/v1.0/users/synthetic/messages/"
                        "synthetic/attachments?$skiptoken=opaque"
                    ),
                }
            raise RuntimeError(PROVIDER_MARKER)

    result = build_attachment_service(
        FailingContinuationClient()
    ).count_supported_file_attachments(
        PROTECTED_MESSAGE_MARKER, supported_extensions={".pdf"}
    )
    assert result.success is False and result.count is None
    assert result.unprovable_reason == "attachment_metadata_pagination_request_failed"
    assert PROVIDER_MARKER not in repr(result)


def test_mailbox_listing_uses_allowlisted_operation_category():
    client = RecordingGraphClient()
    service = EmailService.__new__(EmailService)
    service.client = client
    service.config = SimpleNamespace(
        mailbox="synthetic-mailbox@example.invalid"
    )

    result = service.get_unread_messages(top=2)

    assert result == []
    assert len(client.calls) == 1
    assert client.calls[0]["operation_category"] == "mailbox_enumeration"


def test_exact_acceptance_refetch_is_inbox_scoped_and_metadata_only():
    client = RecordingGraphClient()
    service = EmailService.__new__(EmailService)
    service.client = client
    service.config = SimpleNamespace(
        mailbox="synthetic-mailbox@example.invalid"
    )

    result = service.get_unread_inbox_message(PROTECTED_MESSAGE_MARKER)

    assert result == {"value": []}
    assert len(client.calls) == 1
    call = client.calls[0]
    assert call["endpoint"].endswith(
        f"/mailFolders/inbox/messages/{PROTECTED_MESSAGE_MARKER}"
    )
    assert call["operation_category"] == "mailbox_enumeration"
    assert "body" not in call["params"]["$select"]
    assert "uniqueBody" not in call["params"]["$select"]


def test_recent_attachment_listing_requests_only_internal_required_fields():
    client = RecordingGraphClient()
    service = EmailService.__new__(EmailService)
    service.client = client
    service.config = SimpleNamespace(
        mailbox="synthetic-mailbox@example.invalid"
    )

    result = service.get_recent_attachment_messages(top=3)

    assert result == []
    assert len(client.calls) == 1
    assert client.calls[0]["operation_category"] == "mailbox_enumeration"
    assert client.calls[0]["params"] == {
        "$orderby": "receivedDateTime desc",
        "$top": 3,
        "$select": "id,receivedDateTime,hasAttachments",
    }


def test_http_failure_retains_only_safe_attachment_diagnostics():
    response = SyntheticResponse(status_code=400)
    client = build_client()

    with patch("src.graph.client.requests.get", return_value=response):
        error, stdout, stderr = capture_error(
            lambda: client.get(
                "/synthetic/attachments",
                operation_category="attachment_enumeration",
            ),
            GraphRequestError,
        )

    assert error.category == "graph_request_failed"
    assert error.status_code == 400
    assert error.operation_category == "attachment_enumeration"
    assert error.response_present is True
    assert error.response_content_type_category == "json"
    assert error.failure_kind == "http_error"
    assert_no_protected_diagnostics(error, stdout, stderr)


def test_response_decoding_failure_retains_safe_response_diagnostics():
    response = SyntheticResponse(
        status_code=200,
        content_type="application/json; charset=utf-8",
        json_error=ValueError(PROVIDER_MARKER),
    )
    client = build_client()

    with patch("src.graph.client.requests.get", return_value=response):
        error, stdout, stderr = capture_error(
            lambda: client.get(
                "/synthetic/attachments",
                operation_category="attachment_enumeration",
            ),
            GraphRequestError,
        )

    assert error.status_code == 200
    assert error.operation_category == "attachment_enumeration"
    assert error.response_present is True
    assert error.response_content_type_category == "json"
    assert error.failure_kind == "response_decode"
    assert_no_protected_diagnostics(error, stdout, stderr)


def test_timeout_retains_only_safe_transport_category():
    client = build_client()

    with patch(
        "src.graph.client.requests.get",
        side_effect=requests.Timeout(PROVIDER_MARKER),
    ):
        error, stdout, stderr = capture_error(
            lambda: client.get(
                "/synthetic/attachments",
                operation_category="attachment_enumeration",
            ),
            GraphRequestError,
        )

    assert error.status_code is None
    assert error.operation_category == "attachment_enumeration"
    assert error.response_present is False
    assert error.response_content_type_category == "none"
    assert error.failure_kind == "timeout"
    assert_no_protected_diagnostics(error, stdout, stderr)


def test_authorization_failure_remains_sanitized():
    response = SyntheticResponse(status_code=403)
    client = build_client()

    with patch("src.graph.client.requests.get", return_value=response):
        error, stdout, stderr = capture_error(
            lambda: client.get(
                "/synthetic/attachments",
                operation_category="attachment_enumeration",
            ),
            GraphAuthorizationError,
        )

    assert error.category == "authorization_failed"
    assert_no_protected_diagnostics(error, stdout, stderr)


def main():
    tests = [
        test_attachment_listing_uses_allowlisted_operation_category,
        test_attachment_metadata_count_follows_graph_continuation_without_content,
        test_download_accepts_same_graph_file_type_spellings_as_metadata_proof,
        test_attachment_metadata_unprovable_reasons_are_allowlisted_and_fail_closed,
        test_attachment_metadata_continuation_failure_is_distinguished_and_closed,
        test_mailbox_listing_uses_allowlisted_operation_category,
        test_http_failure_retains_only_safe_attachment_diagnostics,
        test_response_decoding_failure_retains_safe_response_diagnostics,
        test_timeout_retains_only_safe_transport_category,
        test_authorization_failure_remains_sanitized,
    ]
    passed = 0
    failed = 0

    for operation in tests:
        try:
            operation()
            passed += 1
        except Exception:
            failed += 1

    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print("Classification: synthetic deterministic/mock")
    print("Live integrations: not called")
    print("PHI/protected-data access: no")

    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
