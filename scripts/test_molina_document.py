import re
from pathlib import Path
from time import perf_counter
from typing import Any

from src.document_processing.document_processor import (
    DocumentProcessor,
)
from src.models.document import AuthorizationServiceLine
from src.services.evidence_validation_service import (
    EvidenceValidationService,
)


PDF_DIRECTORY = Path(
    "data/incoming"
)

EXPECTED_DOCUMENT_TYPE = "authorization"
EXPECTED_SERVICE_CODE = "S9110"
EXPECTED_MODIFIER = "U1"

EXPECTED_QUANTITIES = {
    "1",
    "6",
}

EXPECTED_SERVICE_LINE_COUNT = 2

EXPECTED_SOURCE_DATES = (
    "11/25/2025",
    "05/23/2026",
)

SAFE_FLAT_FIELDS = (
    "authorization_status",
    "request_type",
    "service_code",
    "service_codes",
    "service_description",
    "modifier",
    "authorized_units",
    "approved_visits",
    "start_date",
    "end_date",
)

ISO_DATE_PATTERN = re.compile(
    r"^\d{4}-\d{2}-\d{2}$"
)

SOURCE_TOKEN_PATTERN = re.compile(
    r"[A-Za-z0-9]+"
)


def format_percentage(
    value: float | None,
) -> str:
    if value is None:
        return "Not available"

    return f"{value * 100:.1f}%"


def format_value(
    value: Any,
) -> str:
    if value is None:
        return "None"

    return str(
        value
    )


def format_seconds(
    value: Any,
) -> str:
    try:
        seconds = float(
            value
        )
    except (TypeError, ValueError):
        return "Not available"

    return f"{seconds:.2f} seconds"


def normalize_value_set(
    value: Any,
) -> set[str]:
    """
    Convert a scalar or list into normalized string values.
    """

    if value is None:
        return set()

    values = (
        value
        if isinstance(
            value,
            list,
        )
        else [value]
    )

    return {
        str(
            item
        ).strip()
        for item in values
        if str(
            item
        ).strip()
    }


def tokenize_source(
    source_text: str,
) -> set[str]:
    """
    Return uppercase alphanumeric tokens without printing source text.
    """

    return {
        token.upper()
        for token in SOURCE_TOKEN_PATTERN.findall(
            source_text
        )
    }


def is_iso_date(
    value: Any,
) -> bool:
    if not isinstance(
        value,
        str,
    ):
        return False

    return bool(
        ISO_DATE_PATTERN.fullmatch(
            value
        )
    )


def source_contains_date(
    source_text: str,
    date_value: str,
) -> bool:
    """
    Check for a known date without printing source evidence.
    """

    return date_value in source_text


def print_safe_flat_fields(
    extracted_data: dict[str, Any],
    field_confidences: dict[str, float],
) -> None:
    """
    Print only non-identifier fields needed for regression testing.

    Source evidence is intentionally excluded because it may contain
    PHI or other sensitive document content.
    """

    print(
        "Safe flat-field regression output:"
    )

    for field_name in SAFE_FLAT_FIELDS:
        value = extracted_data.get(
            field_name
        )

        confidence = field_confidences.get(
            field_name,
            0.0,
        )

        print(
            f"  {field_name}:"
        )

        print(
            "    value: "
            f"{format_value(value)}"
        )

        print(
            "    confidence: "
            f"{format_percentage(confidence)}"
        )


def print_service_line(
    line_number: int,
    service_line: AuthorizationServiceLine,
) -> None:
    """
    Print the neutral service-line structure without source evidence.
    """

    print(
        f"  Service line {line_number}:"
    )

    print(
        "    service_code: "
        f"{format_value(service_line.service_code)}"
    )

    print(
        "    modifier: "
        f"{format_value(service_line.modifier)}"
    )

    print(
        "    quantity: "
        f"{format_value(service_line.quantity)}"
    )

    print(
        "    start_date: "
        f"{format_value(service_line.start_date)}"
    )

    print(
        "    end_date: "
        f"{format_value(service_line.end_date)}"
    )

    print(
        "    status: "
        f"{format_value(service_line.status)}"
    )

    print(
        "    confidence: "
        f"{format_percentage(service_line.confidence)}"
    )

    print(
        "    source evidence present: "
        f"{bool(service_line.source_text)}"
    )


def print_service_line_diagnostics(
    line_number: int,
    service_line: AuthorizationServiceLine,
) -> None:
    """
    Print PHI-safe facts about service-line source evidence.

    Raw source evidence is never printed.
    """

    source_text = str(
        service_line.source_text
        or ""
    )

    source_tokens = tokenize_source(
        source_text
    )

    print(
        f"  Service line {line_number}:"
    )

    print(
        "    source character count: "
        f"{len(source_text)}"
    )

    print(
        "    contains expected service code token: "
        f"{EXPECTED_SERVICE_CODE in source_tokens}"
    )

    print(
        "    contains expected modifier token: "
        f"{EXPECTED_MODIFIER in source_tokens}"
    )

    print(
        "    contains quantity token 1: "
        f"{'1' in source_tokens}"
    )

    print(
        "    contains quantity token 6: "
        f"{'6' in source_tokens}"
    )

    print(
        "    contains expected start date: "
        f"{source_contains_date(
            source_text,
            EXPECTED_SOURCE_DATES[0],
        )}"
    )

    print(
        "    contains expected end date: "
        f"{source_contains_date(
            source_text,
            EXPECTED_SOURCE_DATES[1],
        )}"
    )

    print(
        "    extracted service code supported: "
        f"{bool(
            service_line.service_code
            and str(
                service_line.service_code
            ).strip().upper()
            in source_tokens
        )}"
    )

    extracted_modifier = str(
        service_line.modifier
        or ""
    ).strip().upper()

    print(
        "    extracted modifier supported: "
        f"{bool(
            extracted_modifier
            and extracted_modifier in source_tokens
        )}"
    )

    extracted_quantity = str(
        service_line.quantity
        or ""
    ).strip().upper()

    print(
        "    extracted quantity supported: "
        f"{bool(
            extracted_quantity
            and extracted_quantity in source_tokens
        )}"
    )


def print_service_lines(
    service_lines: list[AuthorizationServiceLine],
) -> None:
    """
    Print service-line count and safe row-level values.
    """

    print(
        "Service-line count: "
        f"{len(service_lines)}"
    )

    if not service_lines:
        print(
            "  No reliable service-line rows were returned."
        )
        return

    for line_number, service_line in enumerate(
        service_lines,
        start=1,
    ):
        print_service_line(
            line_number,
            service_line,
        )


def print_service_line_diagnostic_summary(
    service_lines: list[AuthorizationServiceLine],
) -> None:
    """
    Print only boolean and length diagnostics about source evidence.
    """

    print(
        "PHI-safe service-line source diagnostics:"
    )

    if not service_lines:
        print(
            "  No service lines available for diagnostics."
        )
        return

    for line_number, service_line in enumerate(
        service_lines,
        start=1,
    ):
        print_service_line_diagnostics(
            line_number,
            service_line,
        )


def print_ollama_metrics(
    label: str,
    metrics: Any,
) -> None:
    """
    Print PHI-safe local Ollama timing and token statistics.
    """

    print(
        f"{label} Ollama metrics:"
    )

    if not isinstance(
        metrics,
        dict,
    ) or not metrics:
        print(
            "  Not available"
        )
        return

    print(
        "  request_type: "
        f"{format_value(metrics.get('request_type'))}"
    )

    print(
        "  attempt: "
        f"{format_value(metrics.get('attempt'))}"
    )

    print(
        "  seed: "
        f"{format_value(metrics.get('seed'))}"
    )

    print(
        "  done: "
        f"{format_value(metrics.get('done'))}"
    )

    print(
        "  done_reason: "
        f"{format_value(metrics.get('done_reason'))}"
    )

    print(
        "  total_duration: "
        f"{format_seconds(
            metrics.get(
                'total_duration_seconds'
            )
        )}"
    )

    print(
        "  load_duration: "
        f"{format_seconds(
            metrics.get(
                'load_duration_seconds'
            )
        )}"
    )

    print(
        "  prompt_eval_count: "
        f"{format_value(
            metrics.get(
                'prompt_eval_count'
            )
        )}"
    )

    print(
        "  prompt_eval_duration: "
        f"{format_seconds(
            metrics.get(
                'prompt_eval_duration_seconds'
            )
        )}"
    )

    print(
        "  eval_count: "
        f"{format_value(
            metrics.get(
                'eval_count'
            )
        )}"
    )

    print(
        "  eval_duration: "
        f"{format_seconds(
            metrics.get(
                'eval_duration_seconds'
            )
        )}"
    )

    tokens_per_second = metrics.get(
        "generation_tokens_per_second"
    )

    if isinstance(
        tokens_per_second,
        (
            int,
            float,
        ),
    ):
        formatted_rate = (
            f"{float(tokens_per_second):.2f}"
        )
    else:
        formatted_rate = "Not available"

    print(
        "  generation_tokens_per_second: "
        f"{formatted_rate}"
    )


def print_processing_metrics(
    metrics: dict[str, Any],
    measured_total_seconds: float,
) -> None:
    """
    Print PHI-safe stage timing, retry decisions, and Ollama metadata.
    """

    print(
        "PHI-safe processing metrics:"
    )

    print(
        "  externally measured total: "
        f"{measured_total_seconds:.2f} seconds"
    )

    print(
        "  processor total: "
        f"{format_seconds(
            metrics.get(
                'total_wall_seconds'
            )
        )}"
    )

    print(
        "  OCR wall time: "
        f"{format_seconds(
            metrics.get(
                'ocr_wall_seconds'
            )
        )}"
    )

    print(
        "  classification wall time: "
        f"{format_seconds(
            metrics.get(
                'classification_wall_seconds'
            )
        )}"
    )

    print(
        "  extraction wall time: "
        f"{format_seconds(
            metrics.get(
                'extraction_wall_seconds'
            )
        )}"
    )

    print(
        "  extraction attempt count: "
        f"{format_value(
            metrics.get(
                'extraction_attempt_count'
            )
        )}"
    )

    print(
        "  extraction retry triggered: "
        f"{format_value(
            metrics.get(
                'extraction_retry_triggered'
            )
        )}"
    )

    print(
        "  extraction raw retry required: "
        f"{format_value(
            metrics.get(
                'extraction_raw_retry_required'
            )
        )}"
    )

    print(
        "  extraction validated retry required: "
        f"{format_value(
            metrics.get(
                'extraction_validated_retry_required'
            )
        )}"
    )

    print(
        "  selected extraction attempt: "
        f"{format_value(
            metrics.get(
                'extraction_selected_attempt'
            )
        )}"
    )

    print(
        "  validation wall time: "
        f"{format_seconds(
            metrics.get(
                'validation_wall_seconds'
            )
        )}"
    )

    print(
        "  business-rules wall time: "
        f"{format_seconds(
            metrics.get(
                'business_rules_wall_seconds'
            )
        )}"
    )

    print(
        "  human-review wall time: "
        f"{format_seconds(
            metrics.get(
                'human_review_wall_seconds'
            )
        )}"
    )

    print()

    print_ollama_metrics(
        "Classification",
        metrics.get(
            "classification_ollama"
        ),
    )

    extraction_attempts = metrics.get(
        "extraction_attempts"
    )

    if isinstance(
        extraction_attempts,
        list,
    ):
        for attempt in extraction_attempts:
            if not isinstance(
                attempt,
                dict,
            ):
                continue

            attempt_number = attempt.get(
                "attempt"
            )

            print()

            print(
                "Extraction attempt "
                f"{format_value(attempt_number)} wall time: "
                f"{format_seconds(
                    attempt.get(
                        'wall_seconds'
                    )
                )}"
            )

            print_ollama_metrics(
                (
                    "Extraction attempt "
                    f"{format_value(attempt_number)}"
                ),
                attempt.get(
                    "ollama"
                ),
            )
    else:
        print()

        print_ollama_metrics(
            "Extraction",
            metrics.get(
                "extraction_ollama"
            ),
        )


def validate_flat_fields(
    extracted_data: dict[str, Any],
) -> list[str]:
    """
    Validate known flat-field expectations for this regression document.
    """

    failures: list[str] = []

    authorization_status = str(
        extracted_data.get(
            "authorization_status"
        )
        or ""
    ).strip().lower()

    if authorization_status != "approved":
        failures.append(
            "authorization_status must remain Approved"
        )

    service_code = str(
        extracted_data.get(
            "service_code"
        )
        or ""
    ).strip().upper()

    if service_code != EXPECTED_SERVICE_CODE:
        failures.append(
            "service_code must remain S9110"
        )

    service_codes = {
        value.upper()
        for value in normalize_value_set(
            extracted_data.get(
                "service_codes"
            )
        )
    }

    if EXPECTED_SERVICE_CODE not in service_codes:
        failures.append(
            "service_codes must contain S9110"
        )

    authorized_units = normalize_value_set(
        extracted_data.get(
            "authorized_units"
        )
    )

    if authorized_units != EXPECTED_QUANTITIES:
        failures.append(
            "authorized_units must preserve quantities 1 and 6"
        )

    modifier = str(
        extracted_data.get(
            "modifier"
        )
        or ""
    ).strip().upper()

    if modifier != EXPECTED_MODIFIER:
        failures.append(
            "top-level modifier must remain U1"
        )

    if extracted_data.get(
        "request_type"
    ) is not None:
        failures.append(
            "ambiguous request_type must remain null"
        )

    if extracted_data.get(
        "approved_visits"
    ) is not None:
        failures.append(
            "requested visits must not become approved_visits"
        )

    if not is_iso_date(
        extracted_data.get(
            "start_date"
        )
    ):
        failures.append(
            "top-level start_date must be ISO formatted"
        )

    if not is_iso_date(
        extracted_data.get(
            "end_date"
        )
    ):
        failures.append(
            "top-level end_date must be ISO formatted"
        )

    return failures


def validate_service_lines(
    service_lines: list[AuthorizationServiceLine],
) -> list[str]:
    """
    Validate row-level expectations for this regression document.

    A row-level modifier is not required because current evidence does
    not reliably associate the supported top-level modifier with a
    specific service line.
    """

    failures: list[str] = []

    if len(
        service_lines
    ) != EXPECTED_SERVICE_LINE_COUNT:
        failures.append(
            "exactly two service-line rows must be preserved"
        )

    observed_quantities: set[str] = set()

    for line_number, service_line in enumerate(
        service_lines,
        start=1,
    ):
        if not isinstance(
            service_line,
            AuthorizationServiceLine,
        ):
            failures.append(
                f"service line {line_number} has invalid structure"
            )
            continue

        source_tokens = tokenize_source(
            service_line.source_text
        )

        service_code = str(
            service_line.service_code
            or ""
        ).strip().upper()

        if service_code != EXPECTED_SERVICE_CODE:
            failures.append(
                f"service line {line_number} must preserve S9110"
            )

        if service_code not in source_tokens:
            failures.append(
                f"service line {line_number} service code "
                "must be supported by row evidence"
            )

        quantity = str(
            service_line.quantity
            or ""
        ).strip()

        if not quantity:
            failures.append(
                f"service line {line_number} must preserve quantity"
            )
        else:
            observed_quantities.add(
                quantity
            )

            if quantity.upper() not in source_tokens:
                failures.append(
                    f"service line {line_number} quantity "
                    "must be supported by row evidence"
                )

        if not is_iso_date(
            service_line.start_date
        ):
            failures.append(
                f"service line {line_number} start_date "
                "must be ISO formatted"
            )

        if not is_iso_date(
            service_line.end_date
        ):
            failures.append(
                f"service line {line_number} end_date "
                "must be ISO formatted"
            )

        status = str(
            service_line.status
            or ""
        ).strip().lower()

        if status != "approved":
            failures.append(
                f"service line {line_number} must preserve "
                "Approved status"
            )

        if not service_line.source_text:
            failures.append(
                f"service line {line_number} must preserve "
                "source evidence"
            )

        if service_line.modifier:
            normalized_modifier = str(
                service_line.modifier
            ).strip().upper()

            if normalized_modifier not in source_tokens:
                failures.append(
                    f"service line {line_number} must not retain "
                    "an unsupported modifier"
                )

    if observed_quantities != EXPECTED_QUANTITIES:
        failures.append(
            "service-line rows must preserve quantities 1 and 6"
        )

    return failures


def validate_review_decision(
    needs_human_review: bool,
    validation_actions: list[str],
    review_reasons: list[str],
) -> list[str]:
    """
    Confirm unresolved ambiguity still routes to human review.
    """

    failures: list[str] = []

    relationship_action = (
        EvidenceValidationService
        .SERVICE_LINE_MODIFIER_RELATIONSHIP_ACTION
    )

    if relationship_action not in validation_actions:
        failures.append(
            "unresolved service-line modifier relationship "
            "must create a validation action"
        )

    if not needs_human_review:
        failures.append(
            "human review must remain required"
        )

    if not validation_actions:
        failures.append(
            "validation actions must explain unresolved evidence"
        )

    if not review_reasons:
        failures.append(
            "review reasons must be populated"
        )

    if relationship_action not in review_reasons:
        failures.append(
            "modifier relationship action must appear "
            "in review reasons"
        )

    return failures


def print_semantic_results(
    failures: list[str],
) -> None:
    print()
    print(
        "Semantic regression result:"
    )

    if not failures:
        print(
            "  PASSED"
        )
        return

    print(
        "  FAILED"
    )

    for failure in failures:
        print(
            f"  - {failure}"
        )


def main() -> None:
    print(
        "=" * 60
    )

    print(
        "Testing Molina Authorization Service-Line Extraction"
    )

    print(
        "=" * 60
    )

    pdf_files = sorted(
        PDF_DIRECTORY.glob(
            "*.pdf"
        )
    )

    if not pdf_files:
        print(
            "No PDF files were found in the configured incoming "
            "directory."
        )

        raise SystemExit(
            1
        )

    processor = DocumentProcessor()

    passed = 0
    failed = 0

    for document_number, pdf_file in enumerate(
        pdf_files,
        start=1,
    ):
        print()
        print(
            "-" * 60
        )

        print(
            "Processing local document "
            f"{document_number} of {len(pdf_files)}"
        )

        started_at = perf_counter()

        try:
            document = processor.process(
                pdf_file
            )

            total_seconds = (
                perf_counter()
                - started_at
            )

            print(
                "Document type: "
                f"{document.document_type}"
            )

            print(
                "Classification confidence: "
                f"{format_percentage(document.confidence)}"
            )

            print()

            print_service_lines(
                document.service_lines
            )

            print()

            print_service_line_diagnostic_summary(
                document.service_lines
            )

            print()

            print_safe_flat_fields(
                document.extracted_data,
                document.field_confidences,
            )

            print()

            print(
                "Deterministic validation actions: "
                f"{document.validation_actions}"
            )

            print(
                "Business-rule actions: "
                f"{document.rule_actions}"
            )

            print(
                "Minimum field confidence: "
                f"{format_percentage(
                    document.minimum_field_confidence
                )}"
            )

            print(
                "Review status: "
                f"{document.review_status}"
            )

            print(
                "Human verification required: "
                f"{document.needs_human_review}"
            )

            print(
                "Review reasons: "
                f"{document.review_reasons}"
            )

            semantic_failures: list[str] = []

            if (
                document.document_type
                != EXPECTED_DOCUMENT_TYPE
            ):
                semantic_failures.append(
                    "document type must remain authorization"
                )

            semantic_failures.extend(
                validate_flat_fields(
                    document.extracted_data
                )
            )

            semantic_failures.extend(
                validate_service_lines(
                    document.service_lines
                )
            )

            semantic_failures.extend(
                validate_review_decision(
                    needs_human_review=(
                        document.needs_human_review
                    ),
                    validation_actions=(
                        document.validation_actions
                    ),
                    review_reasons=(
                        document.review_reasons
                    ),
                )
            )

            print_semantic_results(
                semantic_failures
            )

            print()

            print_processing_metrics(
                document.processing_metrics,
                total_seconds,
            )

            if semantic_failures:
                failed += 1
            else:
                passed += 1

        except Exception as ex:
            total_seconds = (
                perf_counter()
                - started_at
            )

            print(
                "ERROR: "
                f"{type(ex).__name__}: {ex}"
            )

            print(
                "Elapsed time before failure: "
                f"{total_seconds:.2f} seconds"
            )

            failed += 1

    print()
    print(
        "=" * 60
    )

    print(
        f"Passed: {passed}"
    )

    print(
        f"Failed: {failed}"
    )

    print(
        "Real or mock: Real cached OCR and local Ollama processing"
    )

    print(
        "PHI output: Suppressed"
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