from src.services.windows_dpapi_service import (
    WindowsDpapiError,
    protect_current_user,
    unprotect_current_user,
)


def test_current_user_round_trip_and_ciphertext_boundary():
    source = b"synthetic protected state"
    purpose = b"LTHHC synthetic DPAPI test v1"
    sealed = protect_current_user(source, purpose=purpose)
    assert sealed != source
    assert source not in sealed
    assert unprotect_current_user(sealed, purpose=purpose) == source


def test_purpose_separation_fails_closed():
    sealed = protect_current_user(
        b"synthetic protected state", purpose=b"LTHHC purpose one"
    )
    try:
        unprotect_current_user(sealed, purpose=b"LTHHC purpose two")
        raise AssertionError("cross-purpose decryption was accepted")
    except WindowsDpapiError as error:
        assert error.category == "dpapi_decryption_failed"


if __name__ == "__main__":
    tests = [
        value for name, value in tuple(globals().items())
        if name.startswith("test_")
    ]
    for test in tests:
        test()
    print(f"Passed: {len(tests)}")
    print("Failed: 0")
    print("Classification: synthetic deterministic local Windows DPAPI")
    print("External integrations: not called")
    print("PHI handling: synthetic bytes only")
