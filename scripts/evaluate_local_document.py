import argparse
import json

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

    return parser


def main() -> None:
    parser = build_argument_parser()
    args = parser.parse_args()

    if args.list_documents:
        result = LocalDocumentEvaluationService().list_documents()
        print(json.dumps(result.to_safe_dict(), sort_keys=True))
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

    print(
        json.dumps(
            result.to_safe_dict(),
            sort_keys=True,
        )
    )

    if not result.success:
        raise SystemExit(
            1
        )


if __name__ == "__main__":
    main()
