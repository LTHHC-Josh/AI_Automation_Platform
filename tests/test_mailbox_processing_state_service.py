from dataclasses import fields
import hashlib
from pathlib import Path
from tempfile import TemporaryDirectory

from src.services.mailbox_processing_state_service import (
    MailboxProcessingStateResult,
    MailboxProcessingStateService,
)


passed = 0
failed = 0


def run_test(
    name,
    test_function,
):
    global passed
    global failed

    try:
        test_function()
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


def test_new_message_is_not_handled():
    with TemporaryDirectory() as directory:
        service = MailboxProcessingStateService(
            directory
        )

        result = service.check(
            "synthetic-message-id"
        )

        assert result.success is True
        assert result.handled is False
        assert result.stored is False
        assert result.duplicate is False
        assert result.status == "not_handled"


def test_handled_message_is_persisted():
    with TemporaryDirectory() as directory:
        service = MailboxProcessingStateService(
            directory
        )

        stored = service.mark_handled(
            "synthetic-message-id"
        )

        checked = service.check(
            "synthetic-message-id"
        )

        assert stored.success is True
        assert stored.stored is True
        assert stored.handled is True
        assert checked.success is True
        assert checked.handled is True
        assert checked.status == "already_handled"


def test_duplicate_mark_is_idempotent():
    with TemporaryDirectory() as directory:
        service = MailboxProcessingStateService(
            directory
        )

        first = service.mark_handled(
            "synthetic-message-id"
        )

        second = service.mark_handled(
            "synthetic-message-id"
        )

        assert first.stored is True
        assert first.duplicate is False
        assert second.stored is False
        assert second.duplicate is True
        assert second.success is True
        assert second.status == "already_handled"


def test_raw_message_id_is_not_stored():
    with TemporaryDirectory() as directory:
        state_dir = Path(
            directory
        )

        message_id = (
            "synthetic-private-message-id"
        )

        service = MailboxProcessingStateService(
            state_dir
        )

        result = service.mark_handled(
            message_id
        )

        assert result.success is True

        files = list(
            state_dir.iterdir()
        )

        assert len(files) == 1

        marker = files[0]

        expected_fingerprint = hashlib.sha256(
            message_id.encode(
                "utf-8"
            )
        ).hexdigest()

        assert marker.name == (
            expected_fingerprint
            + ".handled"
        )

        marker_text = marker.read_text(
            encoding="ascii"
        )

        assert marker_text == "handled\n"
        assert message_id not in marker.name
        assert message_id not in marker_text


def test_different_message_ids_are_distinct():
    with TemporaryDirectory() as directory:
        service = MailboxProcessingStateService(
            directory
        )

        first = service.mark_handled(
            "synthetic-message-one"
        )

        second = service.mark_handled(
            "synthetic-message-two"
        )

        assert first.success is True
        assert second.success is True

        assert service.check(
            "synthetic-message-one"
        ).handled is True

        assert service.check(
            "synthetic-message-two"
        ).handled is True


def test_blank_message_id_is_rejected():
    with TemporaryDirectory() as directory:
        service = MailboxProcessingStateService(
            directory
        )

        result = service.mark_handled(
            "   "
        )

        assert result.success is False
        assert result.handled is False
        assert result.status == "invalid_message_id"


def test_non_string_message_id_is_rejected():
    with TemporaryDirectory() as directory:
        service = MailboxProcessingStateService(
            directory
        )

        result = service.check(
            ["synthetic"]
        )

        assert result.success is False
        assert result.status == "invalid_message_id"


def test_storage_failure_is_sanitized():
    with TemporaryDirectory() as directory:
        root = Path(
            directory
        )

        invalid_state_dir = (
            root
            / "state-as-file"
        )

        invalid_state_dir.write_text(
            "synthetic",
            encoding="utf-8",
        )

        service = MailboxProcessingStateService(
            invalid_state_dir
        )

        result = service.mark_handled(
            "synthetic-message-id"
        )

        rendered = repr(
            result
        )

        assert result.success is False
        assert result.status == "state_storage_failed"
        assert "synthetic-message-id" not in rendered
        assert str(invalid_state_dir) not in rendered


def test_result_contract_is_phi_safe():
    field_names = {
        item.name
        for item in fields(
            MailboxProcessingStateResult
        )
    }

    assert field_names == {
        "handled",
        "stored",
        "duplicate",
        "success",
        "status",
    }


print("=" * 60)
print("Testing Mailbox Processing State")
print("=" * 60)

run_test(
    "new message is not handled",
    test_new_message_is_not_handled,
)
run_test(
    "handled message is persisted",
    test_handled_message_is_persisted,
)
run_test(
    "duplicate mark is idempotent",
    test_duplicate_mark_is_idempotent,
)
run_test(
    "raw message ID is not stored",
    test_raw_message_id_is_not_stored,
)
run_test(
    "different message IDs are distinct",
    test_different_message_ids_are_distinct,
)
run_test(
    "blank message ID is rejected",
    test_blank_message_id_is_rejected,
)
run_test(
    "non-string message ID is rejected",
    test_non_string_message_id_is_rejected,
)
run_test(
    "storage failure is sanitized",
    test_storage_failure_is_sanitized,
)
run_test(
    "result contract is PHI-safe",
    test_result_contract_is_phi_safe,
)

print()
print(f"Passed: {passed}")
print(f"Failed: {failed}")
print(
    "Real or mock: "
    "Synthetic deterministic local-state test"
)
print("Microsoft Graph: Not called")
print("Attachment download: Not called")
print("Document processing: Not called")
print("OCR: Not called")
print("Ollama: Not called")
print("Smartsheet: Not called")
print("External integration: Not called")
print(
    "PHI handling: Only synthetic message IDs "
    "were hashed locally; raw IDs were not stored"
)

if failed:
    raise SystemExit(1)
