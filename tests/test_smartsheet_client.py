from pathlib import Path
import tempfile

from src.clients.smartsheet_client import (
    SmartsheetClient,
)


passed = 0
failed = 0


def run_test(
    name,
    test,
):
    global passed
    global failed

    try:
        test()
        passed += 1
        print(
            f"PASSED: {name}"
        )
    except Exception as error:
        failed += 1
        print(
            f"FAILED: {name}: "
            f"{type(error).__name__}"
        )


class FakeAttachments:
    def __init__(self):
        self.sheet_id = None
        self.row_id = None
        self.received_name = None
        self.received_bytes = None
        self.received_stream = None

    def attach_file_to_row(
        self,
        sheet_id,
        row_id,
        file_stream,
    ):
        self.sheet_id = sheet_id
        self.row_id = row_id
        self.received_name = Path(
            file_stream.name
        ).name
        self.received_bytes = (
            file_stream.read()
        )
        self.received_stream = file_stream

        return "attached"


class FakeSdkClient:
    def __init__(self):
        self.Attachments = FakeAttachments()


def test_attachment_uses_real_binary_file_stream():
    service = SmartsheetClient.__new__(
        SmartsheetClient
    )

    service.sheet_id = 123
    service.client = FakeSdkClient()

    expected_bytes = (
        b"%PDF-1.4\n"
        b"synthetic attachment test\n"
    )

    with tempfile.TemporaryDirectory() as directory:
        source = (
            Path(directory)
            / "LTHHC_AUTH_TEST_abcdef123456.pdf"
        )

        source.write_bytes(
            expected_bytes
        )

        result = service.attach_file_to_row(
            row_id=456,
            file_path=source,
        )

    attachments = service.client.Attachments

    assert result == "attached"
    assert attachments.sheet_id == 123
    assert attachments.row_id == 456

    assert (
        attachments.received_name
        == "LTHHC_AUTH_TEST_abcdef123456.pdf"
    )

    assert (
        attachments.received_bytes
        == expected_bytes
    )

    assert (
        attachments.received_stream.closed
        is True
    )


print(
    "=" * 60
)
print(
    "Testing Smartsheet Client Attachment Boundary"
)
print(
    "=" * 60
)

run_test(
    "attachment sends real binary stream with filename",
    test_attachment_uses_real_binary_file_stream,
)

print()
print(
    f"Passed: {passed}"
)
print(
    f"Failed: {failed}"
)
print(
    "Real or mock: Mock SDK boundary"
)
print(
    "PHI handling: Synthetic bytes only"
)

if failed:
    raise SystemExit(
        1
    )
