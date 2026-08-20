import argparse
import json
from typing import Any

from src.services.local_document_evaluation_service import (
    LocalDocumentEvaluationService,
)
from src.ui.local_protected_review import (
    LocalProtectedReviewConsumer,
)


def parse_document_index(
    value: str,
) -> int:
    try:
        normalized = int(
            value
        )
    except (TypeError, ValueError):
        raise argparse.ArgumentTypeError(
            "Document selector must be a positive numeric index."
        ) from None

    if normalized < 1:
        raise argparse.ArgumentTypeError(
            "Document selector must be a positive numeric index."
        )

    return normalized


def parse_run_type(
    value: str,
) -> str:
    normalized = str(
        value
    ).strip()

    if not normalized:
        raise argparse.ArgumentTypeError(
            "Run Type must be explicit nonblank PHI-safe operator text."
        )

    if not LocalDocumentEvaluationService.normalize_run_type(
        normalized
    ):
        raise argparse.ArgumentTypeError(
            "Run Type must use PHI-safe letters, numbers, spaces, "
            "hyphens, or underscores."
        )

    return normalized


def _display_label(value: str) -> str:
    return value.replace("_", " ").strip().title()


def _display_value(value: Any) -> str:
    if value is True:
        return "Yes"
    if value is False:
        return "No"
    if value is None:
        return "None"
    if value == []:
        return "[]"
    if value == {}:
        return "{}"
    return str(value)


def render_document_list(safe_result: dict[str, Any]) -> str:
    lines = [
        "Available Documents",
        "-------------------",
    ]
    documents = safe_result.get("documents", [])
    if not isinstance(documents, list):
        documents = []

    if documents:
        headers = ("Index", "Relative Order", "Type", "Cached OCR")
        rows = [
            (
                str(item.get("index", "")),
                str(item.get("relative_order", "")),
                str(item.get("file_type", "")).upper(),
                _display_value(item.get("cached_ocr_available")),
            )
            for item in documents
            if isinstance(item, dict)
        ]
        widths = [
            max(len(headers[column]), *(len(row[column]) for row in rows))
            for column in range(len(headers))
        ]
        lines.append(
            "  ".join(
                header.ljust(widths[column])
                for column, header in enumerate(headers)
            ).rstrip()
        )
        lines.extend(
            "  ".join(
                value.ljust(widths[column])
                for column, value in enumerate(row)
            ).rstrip()
            for row in rows
        )
    else:
        lines.append("No selectable documents.")

    if safe_result.get("success") is False:
        lines.append(
            "Status: "
            + _display_value(safe_result.get("failure_category"))
        )
    return "\n".join(lines)


def _render_section_value(
    lines: list[str],
    label: str,
    value: Any,
    *,
    indent: int = 0,
) -> None:
    prefix = " " * indent
    display_label = _display_label(label)
    if isinstance(value, dict):
        lines.append(f"{prefix}{display_label}:")
        if not value:
            lines.append(f"{prefix}  {{}}")
        for child_label, child_value in value.items():
            _render_section_value(
                lines,
                child_label,
                child_value,
                indent=indent + 2,
            )
        return
    if isinstance(value, list):
        lines.append(f"{prefix}{display_label}:")
        if not value:
            lines.append(f"{prefix}  []")
        for item_number, item in enumerate(value, start=1):
            if isinstance(item, dict):
                lines.append(f"{prefix}  {item_number}.")
                for child_label, child_value in item.items():
                    _render_section_value(
                        lines,
                        child_label,
                        child_value,
                        indent=indent + 4,
                    )
            else:
                lines.append(f"{prefix}  - {_display_value(item)}")
        return
    lines.append(f"{prefix}{display_label}: {_display_value(value)}")


def render_learning_report(safe_result: dict[str, Any]) -> str:
    lines = ["Document Learning Analysis", "==========================", ""]
    lines.extend(["Evaluation Summary", "------------------"])
    for key, value in safe_result.items():
        if key != "learning_report":
            _render_section_value(lines, key, value)

    report = safe_result.get("learning_report")
    lines.extend(["", "Learning Report", "---------------"])
    if isinstance(report, dict):
        for section_name, section_value in report.items():
            lines.extend(["", _display_label(section_name)])
            lines.append("-" * len(lines[-1]))
            if isinstance(section_value, dict):
                for key, value in section_value.items():
                    _render_section_value(lines, key, value)
            else:
                _render_section_value(lines, section_name, section_value)
    else:
        lines.append("Status: Not available")
    return "\n".join(lines)


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run one explicitly authorized aggregate-only local "
            "document evaluation."
        )
    )

    mode = parser.add_mutually_exclusive_group(required=True)

    mode.add_argument(
        "--document-index",
        type=parse_document_index,
        help=(
            "Positive local selector. The selected filename and path "
            "are never displayed."
        ),
    )

    mode.add_argument(
        "--list-documents",
        action="store_true",
        help=(
            "List PHI-safe numeric candidate metadata without evaluating "
            "a document."
        ),
    )

    parser.add_argument(
        "--run-type",
        type=parse_run_type,
        help="Explicit nonblank PHI-safe operator metadata.",
    )

    parser.add_argument(
        "--authorize-cached-ocr-access",
        action="store_true",
        help=(
            "Authorize local protected-document access in cache-only "
            "OCR mode."
        ),
    )

    parser.add_argument(
        "--authorize-local-ollama",
        action="store_true",
        help="Authorize local Ollama for this evaluation.",
    )

    parser.add_argument(
        "--protected-review",
        action="store_true",
        help=(
            "Open the processed document and protected extraction details "
            "in the synchronous local desktop review window."
        ),
    )

    parser.add_argument(
        "--learning-report",
        action="store_true",
        help=(
            "Run one additional local Ollama structural-learning analysis and "
            "return a PHI-safe value-free report."
        ),
    )

    parser.add_argument(
        "--json",
        action="store_true",
        help="Return the existing PHI-safe machine-readable JSON output.",
    )

    return parser


def main() -> None:
    parser = build_argument_parser()
    args = parser.parse_args()

    if args.list_documents:
        result = LocalDocumentEvaluationService().list_documents()
        safe_result = result.to_safe_dict()
        print(
            json.dumps(safe_result, sort_keys=True)
            if args.json
            else render_document_list(safe_result)
        )
        if not result.success:
            raise SystemExit(1)
        return

    if (
        args.run_type is None
        or not args.authorize_cached_ocr_access
        or not args.authorize_local_ollama
    ):
        parser.error(
            "Evaluation requires --run-type, "
            "--authorize-cached-ocr-access, and --authorize-local-ollama."
        )

    protected_review_consumer = (
        LocalProtectedReviewConsumer()
        if args.protected_review
        else None
    )

    result = LocalDocumentEvaluationService(
        protected_review_consumer=protected_review_consumer,
    ).evaluate(
        document_index=args.document_index,
        run_type=args.run_type,
        authorize_cached_ocr_access=(
            args.authorize_cached_ocr_access
        ),
        authorize_local_ollama=args.authorize_local_ollama,
        include_learning_report=args.learning_report,
    )

    safe_result = result.to_safe_dict()
    if args.learning_report and not args.json:
        print(render_learning_report(safe_result))
    else:
        print(json.dumps(safe_result, sort_keys=True))

    if not result.success:
        raise SystemExit(
            1
        )


if __name__ == "__main__":
    main()
