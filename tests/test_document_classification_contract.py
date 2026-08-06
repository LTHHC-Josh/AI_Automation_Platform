from pathlib import Path

from src.ai.llm.providers.ollama_provider import (
    OllamaProvider,
)
from src.models.document import Document
from src.services.review_output_service import (
    ReviewOutputService,
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


def provider():
    """
    Build without calling OllamaProvider.__init__ or connecting locally.
    """

    return OllamaProvider.__new__(
        OllamaProvider
    )


def normalize(
    category,
    subtype,
    confidence=0.90,
):
    return provider()._normalize_classification(
        {
            "document_category": category,
            "document_subtype": subtype,
            "confidence": confidence,
            "reason": "Synthetic supported classification reason.",
        }
    )


def test_initial_authorization():
    result = normalize(
        "authorization",
        "initial",
    )

    assert result[
        "document_category"
    ] == "authorization"

    assert result[
        "document_subtype"
    ] == "initial"

    assert result[
        "document_type"
    ] == "authorization"


def test_renewal_preserves_legacy_routing():
    result = normalize(
        "authorization",
        "renewal",
    )

    assert result[
        "document_subtype"
    ] == "renewal"

    assert result[
        "document_type"
    ] == "authorization_renewal"


def test_extension_preserves_legacy_routing():
    result = normalize(
        "authorization",
        "extension",
    )

    assert result[
        "document_type"
    ] == "authorization_renewal"


def test_referral_uses_unknown_subtype():
    result = normalize(
        "referral",
        "initial",
    )

    assert result[
        "document_category"
    ] == "referral"

    assert result[
        "document_subtype"
    ] == "unknown"

    assert result[
        "document_type"
    ] == "referral"


def test_authorization_termination():
    result = normalize(
        "termination",
        "authorization_termination",
    )

    assert result[
        "document_category"
    ] == "termination"

    assert result[
        "document_subtype"
    ] == "authorization_termination"

    assert result[
        "document_type"
    ] == "termination"


def test_service_termination():
    result = normalize(
        "termination",
        "service_termination",
    )

    assert result[
        "document_subtype"
    ] == "service_termination"


def test_non_service_termination_subtype_is_rejected():
    result = normalize(
        "termination",
        "initial",
    )

    assert result[
        "document_subtype"
    ] == "unknown"


def test_other_category():
    result = normalize(
        "other",
        "renewal",
    )

    assert result[
        "document_category"
    ] == "other"

    assert result[
        "document_subtype"
    ] == "unknown"


def test_invalid_category_becomes_unknown():
    result = normalize(
        "employee_termination",
        "authorization_termination",
    )

    assert result[
        "document_category"
    ] == "unknown"

    assert result[
        "document_subtype"
    ] == "unknown"

    assert result[
        "document_type"
    ] == "unknown"


def test_invalid_subtype_becomes_unknown():
    result = normalize(
        "authorization",
        "guessed_subtype",
    )

    assert result[
        "document_subtype"
    ] == "unknown"


def test_confidence_is_normalized():
    result = normalize(
        "authorization",
        "initial",
        confidence=90,
    )

    assert result[
        "confidence"
    ] == 0.90


def test_review_output_preserves_classification():
    document = Document(
        file_path=Path(
            "synthetic_document.pdf"
        ),
        document_type="authorization_renewal",
        document_category="authorization",
        document_subtype="renewal",
        classification_reason=(
            "Synthetic supported classification reason."
        ),
        confidence=0.90,
    )

    review_output = ReviewOutputService().build(
        document
    )

    assert review_output.document_type == (
        "authorization_renewal"
    )

    assert review_output.document_category == (
        "authorization"
    )

    assert review_output.document_subtype == (
        "renewal"
    )

    assert review_output.classification_reason == (
        "Synthetic supported classification reason."
    )


def test_blank_review_labels_become_unknown():
    document = Document(
        file_path=Path(
            "synthetic_document.pdf"
        ),
        document_category="",
        document_subtype="",
    )

    review_output = ReviewOutputService().build(
        document
    )

    assert review_output.document_category == (
        "unknown"
    )

    assert review_output.document_subtype == (
        "unknown"
    )


def test_schema_requires_two_level_contract():
    schema = OllamaProvider.CLASSIFICATION_SCHEMA

    assert schema[
        "required"
    ] == [
        "document_category",
        "document_subtype",
        "confidence",
        "reason",
    ]

    assert "document_type" not in schema[
        "properties"
    ]


def test_prompt_limits_termination_scope():
    prompt = provider()._classification_prompt()

    assert (
        "authorization or an authorized service"
        in prompt
    )

    assert (
        "employee, provider, vendor"
        in prompt
    )


print(
    "=" * 60
)
print(
    "Testing Document Classification Contract"
)
print(
    "=" * 60
)

run_test(
    "initial authorization",
    test_initial_authorization,
)
run_test(
    "renewal preserves legacy routing",
    test_renewal_preserves_legacy_routing,
)
run_test(
    "extension preserves legacy routing",
    test_extension_preserves_legacy_routing,
)
run_test(
    "referral uses unknown subtype",
    test_referral_uses_unknown_subtype,
)
run_test(
    "authorization termination",
    test_authorization_termination,
)
run_test(
    "service termination",
    test_service_termination,
)
run_test(
    "non-service termination subtype is rejected",
    test_non_service_termination_subtype_is_rejected,
)
run_test(
    "other category",
    test_other_category,
)
run_test(
    "invalid category becomes unknown",
    test_invalid_category_becomes_unknown,
)
run_test(
    "invalid subtype becomes unknown",
    test_invalid_subtype_becomes_unknown,
)
run_test(
    "confidence is normalized",
    test_confidence_is_normalized,
)
run_test(
    "review output preserves classification",
    test_review_output_preserves_classification,
)
run_test(
    "blank review labels become unknown",
    test_blank_review_labels_become_unknown,
)
run_test(
    "schema requires two-level contract",
    test_schema_requires_two_level_contract,
)
run_test(
    "prompt limits termination scope",
    test_prompt_limits_termination_scope,
)

print()
print(
    f"Passed: {passed}"
)
print(
    f"Failed: {failed}"
)
print(
    "Real or mock: Synthetic deterministic test"
)
print(
    "External integration: Not called"
)
print(
    "Local Ollama request: Not called"
)
print(
    "PHI handling: No OCR text or document values printed"
)

if failed:
    raise SystemExit(
        1
    )
