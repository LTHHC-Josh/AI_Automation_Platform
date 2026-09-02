from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

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


class FilenamePolicyService:
    """Resolve only filename rules confirmed by document evidence."""

    INITIAL_WORKFLOW_TOKEN = "AUTH INIT"
    RENEWAL_WORKFLOW_TOKEN = "RENEW AUTH"
    FORM_2067 = "2067"
    SAFE_EXTENSIONS = {".pdf", ".tif", ".tiff", ".png", ".jpg", ".jpeg"}

    def __init__(self, *, builder=None) -> None:
        self.builder = builder or ReferenceFilenameBuilderService()

    def resolve(self, request: FilenamePolicyRequest) -> FilenamePolicyResult:
        if not isinstance(request, FilenamePolicyRequest):
            return self._failure("invalid_policy_request")
        extension = str(request.source_extension or "").strip().lower()
        if extension and not extension.startswith("."):
            extension = f".{extension}"
        if extension not in self.SAFE_EXTENSIONS:
            return self._failure("source_extension_unsupported")

        person_name = self._person_name(request)
        if person_name is None:
            return self._failure("person_name_unresolved")
        payer_token = self._reference_value(request.payer_lookup)
        if payer_token is None:
            return self._failure("payer_reference_unresolved")

        # Service is an optional composition component. Include only one
        # authoritative resolved token; absence or ambiguity is omitted.
        service_token = self._reference_value(request.service_lookup)

        form_token = self._form_token(request.form_type)
        workflow_token, workflow_status = self._workflow_token(
            request.workflow_lookup,
            form_token=form_token,
            category=request.document_category,
            subtype=request.document_subtype,
        )
        qualifier_token, qualifier_status = self._qualifier_token(
            request.qualifier_lookup,
            workflow_token=workflow_token,
        )
        date_token, date_status = self._date_token(request)
        if date_token is None:
            return self._failure(date_status)

        composed = self.builder.build(
            person_name=person_name,
            payer_token=payer_token,
            service_token=service_token,
            form_type_token=form_token,
            workflow_type_token=workflow_token,
            qualifier_token=qualifier_token,
            date_token=date_token,
            policy=FilenameCompositionPolicy(extension=extension),
        )
        if not composed.success:
            return self._failure(composed.status)
        return FilenamePolicyResult(True, composed.filename, False, "resolved")

    @staticmethod
    def _reference_value(result: Any) -> str | None:
        if not isinstance(result, LookupResult) or not result.resolved:
            return None
        value = str(result.value or "").strip()
        return value or None

    @staticmethod
    def _person_name(request: FilenamePolicyRequest) -> str | None:
        values = tuple(
            str(value or "").strip()
            for value in (request.person_last, request.person_first, request.person_middle)
        )
        if not values[0] or not values[1]:
            return None
        if any(any(character in value for character in "_\\/\r\n") for value in values):
            return None
        return " ".join(value for value in values if value)

    @classmethod
    def _form_token(cls, value: Any) -> str | None:
        normalized = " ".join(str(value or "").strip().upper().split())
        if not normalized:
            return None
        return cls.FORM_2067 if normalized == cls.FORM_2067 else None

    @classmethod
    def _workflow_token(
        cls,
        workflow_lookup: Any,
        *,
        form_token: str | None,
        category: Any,
        subtype: Any,
    ) -> tuple[str | None, str]:
        normalized_category = str(category or "").strip().lower()
        normalized_subtype = str(subtype or "").strip().lower()
        if normalized_category == "authorization":
            if normalized_subtype == "initial":
                return cls.INITIAL_WORKFLOW_TOKEN, "resolved"
            if normalized_subtype == "renewal":
                return cls.RENEWAL_WORKFLOW_TOKEN, "resolved"
            return None, "omitted"
        if workflow_lookup is not None:
            value = cls._reference_value(workflow_lookup)
            if value is None:
                return None, "omitted"
            return value, "resolved"
        if form_token == cls.FORM_2067:
            return None, "resolved"
        return None, "omitted"

    @classmethod
    def _qualifier_token(
        cls,
        qualifier_lookup: Any,
        *,
        workflow_token: str | None,
    ) -> tuple[str | None, str]:
        if qualifier_lookup is None:
            return None, "resolved"
        if workflow_token != cls.RENEWAL_WORKFLOW_TOKEN:
            return None, "omitted"
        value = cls._reference_value(qualifier_lookup)
        if value is None:
            return None, "omitted"
        return value, "resolved"

    @classmethod
    def _date_token(cls, request: FilenamePolicyRequest) -> tuple[str | None, str]:
        if cls._form_token(request.form_type) == cls.FORM_2067:
            posted_date = cls._reference_value(request.posted_date_lookup)
            if posted_date is None:
                return None, "posted_date_unresolved"
            formatted = cls._format_date(posted_date)
            if formatted is None:
                return None, "posted_date_invalid"
            return formatted, "resolved"

        start_present = bool(str(request.start_date or "").strip())
        end_present = bool(str(request.end_date or "").strip())
        if start_present and end_present:
            start = cls._format_date(request.start_date)
            end = cls._format_date(request.end_date)
            if start is None or end is None:
                return None, "date_invalid"
            return f"{start}-{end}", "resolved"

        candidates = []
        if start_present:
            candidates.append(request.start_date)
        if end_present:
            candidates.append(request.end_date)
        candidates.extend(request.naming_dates or ())
        candidates = [value for value in candidates if str(value or "").strip()]
        if not candidates:
            return None, "date_unresolved"
        if len(candidates) != 1:
            return None, "date_ownership_unresolved"
        formatted = cls._format_date(candidates[0])
        if formatted is None:
            return None, "date_invalid"
        return formatted, "resolved"

    @staticmethod
    def _format_date(value: Any) -> str | None:
        text = str(value or "").strip()
        for pattern in ("%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y", "%m%d%y"):
            try:
                return datetime.strptime(text, pattern).strftime("%m%d%y")
            except ValueError:
                continue
        return None

    @staticmethod
    def _failure(status: str) -> FilenamePolicyResult:
        return FilenamePolicyResult(False, None, True, status)
