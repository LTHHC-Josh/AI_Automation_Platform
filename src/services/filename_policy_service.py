from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from src.services.intake_document_naming_service import (
    IntakeDocumentNamingVocabulary,
    IntakeDocumentTypeResolution,
)
from src.services.reference_filename_builder_service import (
    FilenameCompositionPolicy,
    ReferenceFilenameBuilderService,
)
from src.services.reference_table_service import LookupResult


@dataclass(frozen=True)
class FilenamePolicyRequest:
    person_last: Any
    person_first: Any
    person_middle: Any = None
    payer_lookup: LookupResult | None = None
    service_applicable: bool = False
    service_lookup: LookupResult | None = None
    document_type_resolution: IntakeDocumentTypeResolution | None = None
    # Legacy dimensions remain accepted while callers migrate to the single
    # canonical intake document-type segment.
    form_type: Any = None
    workflow_lookup: LookupResult | None = None
    qualifier_lookup: LookupResult | None = None
    document_category: Any = None
    document_subtype: Any = None
    posted_date_lookup: LookupResult | None = None
    start_date: Any = None
    end_date: Any = None
    naming_dates: tuple[Any, ...] = ()
    source_extension: Any = ".pdf"


@dataclass(frozen=True)
class FilenamePolicyResult:
    complete: bool
    filename: str | None = field(default=None, repr=False)
    review_required: bool = True
    status: str = "unresolved"
    filename_result: str = "technical_fallback"
    placeholder_categories: tuple[str, ...] = ()
    optional_omission_count: int = 0


class FilenamePolicyService:
    """Compose the approved intake filename without guessing business values."""

    SAFE_EXTENSIONS = {".pdf", ".tif", ".tiff", ".png", ".jpg", ".jpeg"}
    PAYER_PLACEHOLDER = "[PAYER]"
    SERVICE_PLACEHOLDER = "[SERVICE]"
    DATE_PLACEHOLDER = "[DATE]"

    def __init__(self, *, builder=None) -> None:
        self.builder = builder or ReferenceFilenameBuilderService()

    def resolve(self, request: FilenamePolicyRequest) -> FilenamePolicyResult:
        if not isinstance(request, FilenamePolicyRequest):
            return self._failure("invalid_policy_request")
        extension = self._normalized_extension(request.source_extension)
        if extension not in self.SAFE_EXTENSIONS:
            return self._failure("source_extension_unsupported")
        person_name = self._person_name(request)
        if person_name is None:
            return self._failure("person_name_unresolved")

        placeholders = []
        payer_token = self._reference_value(request.payer_lookup)
        if payer_token is None:
            payer_token = self.PAYER_PLACEHOLDER
            placeholders.append("payer")
        service_token = self._reference_value(request.service_lookup)
        if service_token is None and request.service_applicable:
            service_token = self.SERVICE_PLACEHOLDER
            placeholders.append("service")

        document_type = request.document_type_resolution
        if not isinstance(document_type, IntakeDocumentTypeResolution):
            document_type = self._legacy_document_type_resolution(request)
        if document_type.document_type_status == "Placeholder":
            placeholders.append("document_type")
        if document_type.subtype_status == "Placeholder":
            placeholders.append("document_subtype")

        date_token, _ = self._date_token(request)
        if date_token is None:
            date_token = self.DATE_PLACEHOLDER
            placeholders.append("date")

        omissions = self._optional_omission_count(
            middle=request.person_middle,
            service_applicable=request.service_applicable,
            end_date=request.end_date,
        )
        composed = self.builder.build(
            person_name=person_name,
            payer_token=payer_token,
            service_token=service_token,
            document_type_token=document_type.document_type_segment,
            date_token=date_token,
            policy=FilenameCompositionPolicy(extension=extension.upper()),
        )
        if not composed.success:
            return self._failure(composed.status)
        categories = tuple(dict.fromkeys(placeholders))
        result = "partial_business" if categories else "complete_business"
        return FilenamePolicyResult(
            True, composed.filename, bool(categories),
            "resolved_with_placeholders" if categories else "resolved",
            result, categories, omissions,
        )

    @classmethod
    def extension_supported(cls, value: Any) -> bool:
        return cls._normalized_extension(value) in cls.SAFE_EXTENSIONS

    @classmethod
    def date_status(cls, request: Any) -> str:
        if not isinstance(request, FilenamePolicyRequest):
            return "invalid_policy_request"
        _, status = cls._date_token(request)
        return status

    @staticmethod
    def _normalized_extension(value: Any) -> str:
        extension = str(value or "").strip().lower()
        if extension and not extension.startswith("."):
            extension = f".{extension}"
        return extension

    @staticmethod
    def _reference_value(result: Any) -> str | None:
        if not isinstance(result, LookupResult) or not result.resolved:
            return None
        value = " ".join(str(result.value or "").strip().split())
        return value or None

    @staticmethod
    def _person_name(request: FilenamePolicyRequest) -> str | None:
        values = tuple(
            " ".join(str(value or "").strip().split()).upper()
            for value in (request.person_last, request.person_first, request.person_middle)
        )
        if not values[0] or not values[1]:
            return None
        invalid = '_<>:"/\\|?*\r\n'
        if any(any(character in value for character in invalid) for value in values):
            return None
        given = " ".join(value for value in values[1:] if value)
        return f"{values[0]}, {given}"

    @classmethod
    def _legacy_document_type_resolution(
        cls, request: FilenamePolicyRequest
    ) -> IntakeDocumentTypeResolution:
        category = str(request.document_category or "unknown").strip().lower()
        if str(request.form_type or "").strip() == "2067":
            category = "2067"
        token = IntakeDocumentNamingVocabulary.TOP_LEVEL_TOKENS.get(category)
        if token is None:
            return IntakeDocumentTypeResolution(
                IntakeDocumentNamingVocabulary.DOCUMENT_TYPE_PLACEHOLDER,
                "Placeholder",
            )
        if category == "authorization":
            return IntakeDocumentTypeResolution(
                f"AUTH {IntakeDocumentNamingVocabulary.SUBTYPE_PLACEHOLDER}",
                "Ready", subtype_key="unknown", subtype_display="unknown",
                subtype_status="Placeholder", subtype_source_category="unresolved",
            )
        return IntakeDocumentTypeResolution(token, "Ready")

    @classmethod
    def _date_token(cls, request: FilenamePolicyRequest) -> tuple[str | None, str]:
        if str(request.form_type or "").strip() == "2067":
            posted_date = cls._reference_value(request.posted_date_lookup)
            if posted_date is not None:
                formatted = cls._format_date(posted_date)
                if formatted is None:
                    return None, "posted_date_invalid"
                return formatted, "resolved"
        start_present = bool(str(request.start_date or "").strip())
        end_present = bool(str(request.end_date or "").strip())
        if start_present and end_present:
            start = cls._parse_date(request.start_date)
            end = cls._parse_date(request.end_date)
            if start is None or end is None:
                return None, "date_invalid"
            if end < start:
                return None, "date_range_invalid"
            return (
                f"{start.strftime('%m%d%y')}-{end.strftime('%m%d%y')}",
                "resolved",
            )
        candidates = []
        if start_present:
            candidates.append(request.start_date)
        if end_present:
            candidates.append(request.end_date)
        candidates.extend(request.naming_dates or ())
        candidates = [value for value in candidates if str(value or "").strip()]
        if not candidates:
            return None, "date_unresolved"
        normalized = {cls._format_date(value) for value in candidates}
        if None in normalized:
            return None, "date_invalid"
        if len(normalized) != 1:
            return None, "date_ownership_unresolved"
        return next(iter(normalized)), "resolved"

    @staticmethod
    def _format_date(value: Any) -> str | None:
        parsed = FilenamePolicyService._parse_date(value)
        return parsed.strftime("%m%d%y") if parsed is not None else None

    @staticmethod
    def _parse_date(value: Any) -> datetime | None:
        text = str(value or "").strip()
        for pattern in ("%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y", "%m%d%y"):
            try:
                return datetime.strptime(text, pattern)
            except ValueError:
                continue
        return None

    @staticmethod
    def _optional_omission_count(*, middle, service_applicable, end_date) -> int:
        return sum((
            not bool(str(middle or "").strip()),
            not bool(service_applicable),
            not bool(str(end_date or "").strip()),
        ))

    @staticmethod
    def _failure(status: str) -> FilenamePolicyResult:
        return FilenamePolicyResult(
            False, None, True, status, "technical_fallback", (), 0
        )
