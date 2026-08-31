from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

from src.services.mailbox_acceptance_handoff_service import (
    HANDOFF_LEASE_SECONDS,
    MailboxAcceptanceHandoffError,
    MailboxAcceptanceHandoffService,
)


PROTECTED_IDENTITY = "PROTECTED-SYNTHETIC-IDENTITY"


def seal(value: bytes) -> bytes:
    return b"SEALED:" + bytes(item ^ 0xA5 for item in value)


def unseal(value: bytes) -> bytes:
    if not value.startswith(b"SEALED:"):
        raise ValueError
    return bytes(item ^ 0xA5 for item in value[7:])


def service(path: Path, clock):
    return MailboxAcceptanceHandoffService(
        path, clock=lambda: clock[0], protect=seal, unprotect=unseal)


def assert_category(call, category):
    try:
        call()
    except MailboxAcceptanceHandoffError as error:
        assert error.category == category
        assert PROTECTED_IDENTITY not in repr(error)
        return
    raise AssertionError("Expected fail-closed handoff error")


def test_ciphertext_and_fixed_filenames_contain_no_identity_and_claim_is_single_use():
    with TemporaryDirectory() as directory:
        now = [datetime(2026, 8, 31, tzinfo=timezone.utc)]
        handoff = service(Path(directory), now)
        handoff.create(PROTECTED_IDENTITY)
        assert PROTECTED_IDENTITY.encode() not in handoff.path.read_bytes()
        assert PROTECTED_IDENTITY not in str(handoff.path)
        assert PROTECTED_IDENTITY not in repr(handoff.claim())
        assert_category(handoff.claim, "handoff_missing")


def test_duplicate_refused_expiry_fixed_and_cleanup_removes_record():
    with TemporaryDirectory() as directory:
        now = [datetime(2026, 8, 31, tzinfo=timezone.utc)]
        handoff = service(Path(directory), now)
        handoff.create(PROTECTED_IDENTITY)
        assert_category(lambda: handoff.create("another"), "handoff_already_exists")
        now[0] += timedelta(seconds=HANDOFF_LEASE_SECONDS)
        handoff.create("replacement")
        assert handoff.claim().message_identity == "replacement"
        handoff.create(PROTECTED_IDENTITY)
        handoff.cleanup()
        assert not handoff.path.exists()


def test_claim_at_fixed_lease_boundary_expires_and_deletes_record():
    with TemporaryDirectory() as directory:
        now = [datetime(2026, 8, 31, tzinfo=timezone.utc)]
        handoff = service(Path(directory), now)
        handoff.create(PROTECTED_IDENTITY)
        now[0] += timedelta(seconds=HANDOFF_LEASE_SECONDS)
        assert_category(handoff.claim, "handoff_expired")
        assert not handoff.path.exists() and not handoff.claim_path.exists()


def test_corrupt_and_decryption_failures_delete_claimed_record():
    with TemporaryDirectory() as directory:
        now = [datetime(2026, 8, 31, tzinfo=timezone.utc)]
        handoff = service(Path(directory), now)
        handoff.directory.mkdir(parents=True, exist_ok=True)
        handoff.path.write_bytes(b"corrupt")
        assert_category(handoff.claim, "handoff_corrupt")
        assert not handoff.claim_path.exists()


def test_exactly_one_concurrent_consumer_succeeds():
    with TemporaryDirectory() as directory:
        now = [datetime(2026, 8, 31, tzinfo=timezone.utc)]
        handoff = service(Path(directory), now)
        handoff.create(PROTECTED_IDENTITY)

        def claim():
            try:
                return handoff.claim().message_identity == PROTECTED_IDENTITY
            except MailboxAcceptanceHandoffError:
                return False

        with ThreadPoolExecutor(max_workers=8) as pool:
            assert sum(pool.map(lambda _: claim(), range(8))) == 1


if __name__ == "__main__":
    tests = [value for name, value in globals().copy().items() if name.startswith("test_")]
    for test in tests:
        test()
    print(f"Passed: {len(tests)}")
    print("Failed: 0")
    print("Classification: synthetic deterministic and mock")
    print("External integrations: not called")
    print("PHI handling: protected synthetic identity remains sealed and suppressed")
