import os
from pathlib import Path
import tempfile
from types import SimpleNamespace

import src.services.document_processor_training_application_service as application

from src.services.document_processor_training_configuration_service import (
    DPTrainingConfigurationError,
    RUNTIME_FINGERPRINT_ENV,
    load_configured_dp_training_capabilities,
    load_runtime_dp_training_capabilities,
)


RUNTIME_NAMES = ("DP_TRAINING_MODE", RUNTIME_FINGERPRINT_ENV)


def _write(directory: str, text: str) -> Path:
    path = Path(directory) / ".env"
    path.write_text(text, encoding="utf-8", newline="\n")
    return path


def _restore(values: dict[str, str | None]) -> None:
    for name, value in values.items():
        if value is None:
            os.environ.pop(name, None)
        else:
            os.environ[name] = value


def test_all_explicit_modes_resolve_with_stable_safe_fingerprints():
    with tempfile.TemporaryDirectory() as directory:
        fingerprints = set()
        for mode in ("schema_only", "read_only", "proposal_write", "approval_dispatch"):
            configured = load_configured_dp_training_capabilities(
                env_path=_write(directory, f"DP_TRAINING_MODE={mode}\n")
            )
            assert configured.mode == mode
            assert len(configured.fingerprint) == 64
            assert configured.fingerprint.isalnum()
            fingerprints.add(configured.fingerprint)
        assert len(fingerprints) == 4


def test_missing_invalid_and_malformed_capabilities_fail_closed():
    with tempfile.TemporaryDirectory() as directory:
        cases = (
            ("", "training_mode_unavailable"),
            ("DP_TRAINING_MODE=unsafe\n", "training_mode_invalid"),
            (
                "DP_TRAINING_MODE=read_only\n"
                "DP_TRAINING_ALLOW_SMARTSHEET_WRITES=yes\n",
                "training_capability_gate_invalid",
            ),
        )
        for text, category in cases:
            try:
                load_configured_dp_training_capabilities(
                    env_path=_write(directory, text)
                )
            except DPTrainingConfigurationError as error:
                assert error.category == category
            else:
                raise AssertionError("Invalid capability configuration was accepted")


def test_runtime_requires_exact_startup_frozen_mode_and_fingerprint():
    previous = {name: os.environ.get(name) for name in RUNTIME_NAMES}
    try:
        with tempfile.TemporaryDirectory() as directory:
            path = _write(directory, "DP_TRAINING_MODE=read_only\n")
            configured = load_configured_dp_training_capabilities(env_path=path)
            os.environ.pop("DP_TRAINING_MODE", None)
            os.environ.pop(RUNTIME_FINGERPRINT_ENV, None)
            try:
                load_runtime_dp_training_capabilities(env_path=path)
            except DPTrainingConfigurationError as error:
                assert error.category == "training_mode_unavailable"
            else:
                raise AssertionError("Missing runtime snapshot was accepted")

            os.environ["DP_TRAINING_MODE"] = configured.mode
            os.environ[RUNTIME_FINGERPRINT_ENV] = configured.fingerprint
            assert load_runtime_dp_training_capabilities(env_path=path) == configured

            _write(directory, "DP_TRAINING_MODE=schema_only\n")
            try:
                load_runtime_dp_training_capabilities(env_path=path)
            except DPTrainingConfigurationError as error:
                assert error.category == "training_mode_mismatch"
            else:
                raise AssertionError("Changed protected mode was hot-reloaded")
    finally:
        _restore(previous)


def test_explicit_env_path_is_independent_of_current_working_directory():
    previous = Path.cwd()
    with tempfile.TemporaryDirectory() as configured_directory:
        with tempfile.TemporaryDirectory() as unrelated_directory:
            try:
                path = _write(
                    configured_directory, "DP_TRAINING_MODE=read_only\n"
                )
                os.chdir(unrelated_directory)
                assert load_configured_dp_training_capabilities(
                    env_path=path
                ).mode == "read_only"
            finally:
                os.chdir(previous)


def test_application_resolves_runtime_capability_before_client_construction():
    names = (
        "load_runtime_dp_training_capabilities", "SmartsheetClient",
        "SmartsheetCorrectionReader", "SmartsheetCorrectionSchemaService",
        "ProtectedCorrectionCaseRepository", "LocalCorrectionAnalysisService",
        "SmartsheetCorrectionWriter", "PhiSafeImplementationTaskService",
        "BoundedCodexDispatcher",
    )
    original = {name: getattr(application, name) for name in names}
    order = []
    capabilities = SimpleNamespace(
        mode="read_only",
        smartsheet_writes_enabled=False,
        codex_dispatch_enabled=False,
    )

    def load_capabilities():
        order.append("configuration")
        return capabilities

    def client_factory(**kwargs):
        order.append("client")
        return SimpleNamespace()

    try:
        application.load_runtime_dp_training_capabilities = load_capabilities
        application.SmartsheetClient = client_factory
        for name in names[2:]:
            setattr(
                application,
                name,
                lambda *args, **kwargs: SimpleNamespace(),
            )
        service = application.DocumentProcessorTrainingApplicationService.from_environment()
        assert service.mode == "read_only"
        assert order == ["configuration", "client"]
    finally:
        for name, value in original.items():
            setattr(application, name, value)


if __name__ == "__main__":
    tests = [
        value for name, value in tuple(globals().items())
        if name.startswith("test_")
    ]
    for test in tests:
        test()
    print(f"Passed: {len(tests)}")
    print("Failed: 0")
    print("Classification: synthetic deterministic protected configuration")
    print("External integrations: not called")
    print("PHI handling: fixed modes, booleans, and categories only")
