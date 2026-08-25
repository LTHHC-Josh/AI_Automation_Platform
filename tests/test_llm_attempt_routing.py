from typing import Any

from src.ai.llm.llm_service import LLMService
from src.models.learning_document_evidence import LearningDocumentEvidence
from src.models.ocr_document import OCRBlock, OCRDocument, OCRPage


class RecordingProvider:
    """
    Minimal provider double used to verify extraction-attempt routing.
    """

    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def classify(
        self,
        text: str,
    ) -> dict:
        return {
            "document_type": "authorization",
            "confidence": 0.90,
        }

    def extract(
        self,
        text: str,
        prompt: str,
        attempt: int = 1,
    ) -> dict:
        self.calls.append(
            {
                "text": text,
                "prompt": prompt,
                "attempt": attempt,
            }
        )

        return {
            "attempt": attempt,
        }

    def analyze_learning_structure(self, text: str) -> dict:
        self.calls.append({"learning_text": text})
        return {"structural": True}


def build_service_with_recording_provider() -> tuple[
    LLMService,
    RecordingProvider,
]:
    """
    Build an LLMService without invoking the configured provider factory.
    """

    provider = RecordingProvider()

    service = LLMService.__new__(
        LLMService
    )

    service.provider = provider

    return service, provider


def test_default_attempt_is_one() -> None:
    service, provider = build_service_with_recording_provider()

    result = service.extract(
        "synthetic OCR text",
        "authorization",
    )

    assert result == {
        "attempt": 1,
    }

    assert provider.calls == [
        {
            "text": "synthetic OCR text",
            "prompt": "authorization",
            "attempt": 1,
        },
    ]


def test_second_attempt_is_forwarded() -> None:
    service, provider = build_service_with_recording_provider()

    result = service.extract(
        "synthetic OCR text",
        "authorization",
        attempt=2,
    )

    assert result == {
        "attempt": 2,
    }

    assert provider.calls == [
        {
            "text": "synthetic OCR text",
            "prompt": "authorization",
            "attempt": 2,
        },
    ]


def test_learning_analysis_is_forwarded_without_interpretation() -> None:
    service, provider = build_service_with_recording_provider()

    result = service.analyze_learning_structure("synthetic OCR text")

    assert result == {"structural": True}
    assert provider.calls == [{"learning_text": "synthetic OCR text"}]


def test_learning_envelope_contains_every_page_and_block_once() -> None:
    evidence = LearningDocumentEvidence.build(
        OCRDocument(
            pages=(
                OCRPage(1, (OCRBlock("page_1_block_1", "first marker", 1),)),
                OCRPage(2, (OCRBlock("page_2_block_1", "second marker", 2),)),
            ),
            relationship_status="preserved",
        ),
        ("posted_date", "service_code"),
    )

    prompt = evidence.to_local_prompt()

    assert prompt.count("first marker") == 1
    assert prompt.count("second marker") == 1
    assert '<PAGE ref="1">' in prompt
    assert '<PAGE ref="2">' in prompt
    assert 'ref="e0001"' in prompt
    assert 'ref="e0002"' in prompt
    assert "page_1_block_1" not in prompt
    assert "posted_date, service_code" in prompt


def run_test(
    test_name: str,
    test_function,
) -> bool:
    try:
        test_function()
    except AssertionError:
        print(
            f"FAILED: {test_name}"
        )

        return False

    print(
        f"PASSED: {test_name}"
    )

    return True


def main() -> None:
    print(
        "=" * 60
    )

    print(
        "Testing LLM Extraction-Attempt Routing"
    )

    print(
        "=" * 60
    )

    tests = [
        (
            "default extraction attempt is one",
            test_default_attempt_is_one,
        ),
        (
            "second extraction attempt is forwarded",
            test_second_attempt_is_forwarded,
        ),
        (
            "learning analysis is forwarded",
            test_learning_analysis_is_forwarded_without_interpretation,
        ),
        (
            "learning envelope includes every page and block",
            test_learning_envelope_contains_every_page_and_block_once,
        ),
    ]

    passed = 0
    failed = 0

    for test_name, test_function in tests:
        if run_test(
            test_name,
            test_function,
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
        "Real or mock: Synthetic provider-routing test"
    )

    print(
        "=" * 60
    )

    if failed:
        raise SystemExit(
            1
        )


if __name__ == "__main__":
    main()
