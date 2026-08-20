from dataclasses import dataclass, field
from datetime import datetime
import re
from typing import Any

from src.models.document import Document
from src.services.reference_table_service import LookupResult


@dataclass(frozen=True)
class ValidatedFilenameInput:
    lookup: LookupResult = field(repr=False)
    confidence: float = 0.0
    source_text: str = field(default="", repr=False)


@dataclass(frozen=True)
class ValidatedFilenameInputs:
    posted_date: ValidatedFilenameInput
    workflow_context: ValidatedFilenameInput
    renewal_qualifier: ValidatedFilenameInput
    review_required: bool
    review_reasons: tuple[str, ...]


class FilenameValidatedInputService:
    """Expose only validated evidence and approved context to filename policy."""

    FORM_2067 = "2067"
    POSTED_DATE_FIELD = "posted_date"
    RENEWAL_QUALIFIER_FIELD = "renewal_qualifier"

    def resolve(
        self,
        document: Document,
        *,
        form_type: Any = None,
        workflow_context: LookupResult | None = None,
        qualifier_reference: LookupResult | None = None,
    ) -> ValidatedFilenameInputs:
        if not isinstance(document, Document):
            unresolved = self._unresolved("invalid_document")
            return ValidatedFilenameInputs(
                unresolved,
                unresolved,
                unresolved,
                True,
                ("filename_inputs_invalid_document",),
            )

        is_2067 = self._normalize_token(form_type) == self.FORM_2067
        reasons: list[str] = []
        posted_date = self._posted_date(document, required=is_2067)
        if is_2067 and not posted_date.lookup.resolved:
            reasons.append(f"posted_date_{posted_date.lookup.status}")

        workflow = self._workflow_context(
            workflow_context,
            required=is_2067,
        )
        if is_2067 and not workflow.lookup.resolved:
            reasons.append(f"workflow_context_{workflow.lookup.status}")

        qualifier = self._renewal_qualifier(
            document,
            qualifier_reference=qualifier_reference,
        )
        if qualifier.lookup.status not in {"resolved", "not_present"}:
            reasons.append(
                f"renewal_qualifier_{qualifier.lookup.status}"
            )

        return ValidatedFilenameInputs(
            posted_date=posted_date,
            workflow_context=workflow,
            renewal_qualifier=qualifier,
            review_required=bool(reasons),
            review_reasons=tuple(dict.fromkeys(reasons)),
        )

    def _posted_date(
        self,
        document: Document,
        *,
        required: bool,
    ) -> ValidatedFilenameInput:
        if not required:
            return self._unresolved("not_applicable")
        evidence = self._evidence(document, self.POSTED_DATE_FIELD)
        source_text = str(evidence.get("source_text") or "")
        action_status = self._validation_status(
            document,
            self.POSTED_DATE_FIELD,
        )
        if action_status is not None:
            return self._unresolved(
                action_status,
                source_text=source_text,
            )
        value = evidence.get("value")
        if value is None:
            return self._unresolved("missing", source_text=source_text)
        normalized = self._normalized_date(value)
        if normalized is None or not self._posted_date_is_explicit(
            normalized,
            source_text,
        ):
            return self._unresolved("unsupported", source_text=source_text)
        return self._resolved(
            normalized,
            evidence.get("confidence"),
            source_text,
        )

    def _workflow_context(
        self,
        workflow_context: Any,
        *,
        required: bool,
    ) -> ValidatedFilenameInput:
        if not required:
            return self._unresolved("not_applicable")
        if workflow_context is None:
            return self._unresolved("missing")
        if not isinstance(workflow_context, LookupResult):
            return self._unresolved("unsupported")
        value = self._lookup_value(workflow_context)
        if value is None:
            return self._unresolved(
                self._safe_status(workflow_context.status)
            )
        return self._resolved(value, 0.0, "")

    def _renewal_qualifier(
        self,
        document: Document,
        *,
        qualifier_reference: Any,
    ) -> ValidatedFilenameInput:
        evidence = self._evidence(document, self.RENEWAL_QUALIFIER_FIELD)
        source_text = str(evidence.get("source_text") or "")
        action_status = self._validation_status(
            document,
            self.RENEWAL_QUALIFIER_FIELD,
        )
        value = evidence.get("value")
        has_claim = value is not None or action_status is not None
        is_renewal = (
            self._normalize_token(document.document_category).lower()
            == "authorization"
            and self._normalize_token(document.document_subtype).lower()
            == "renewal"
        )
        if not has_claim and qualifier_reference is None:
            return self._unresolved("not_present")
        if not is_renewal:
            return self._unresolved(
                "not_applicable",
                source_text=source_text,
            )
        if action_status is not None:
            return self._unresolved(
                action_status,
                source_text=source_text,
            )
        if value is None:
            return self._unresolved("missing", source_text=source_text)

        normalized = self._normalize_token(value)
        referenced = self._lookup_value(qualifier_reference)
        if (
            not normalized
            or referenced is None
            or normalized != self._normalize_token(referenced)
            or not self._qualifier_is_explicit(normalized, source_text)
        ):
            status = (
                self._safe_status(qualifier_reference.status)
                if isinstance(qualifier_reference, LookupResult)
                and not qualifier_reference.resolved
                else "unsupported"
            )
            return self._unresolved(status, source_text=source_text)
        return self._resolved(
            referenced,
            evidence.get("confidence"),
            source_text,
        )

    @staticmethod
    def _evidence(document: Document, field_name: str) -> dict[str, Any]:
        evidence = document.field_evidence.get(field_name)
        return evidence if isinstance(evidence, dict) else {}

    @classmethod
    def _validation_status(
        cls,
        document: Document,
        field_name: str,
    ) -> str | None:
        prefix = f"{field_name} "
        actions = (
            document.validation_actions
            if isinstance(document.validation_actions, list)
            else []
        )
        for action in actions:
            text = str(action or "")
            if not text.startswith(prefix):
                continue
            lowered = text.lower()
            if "multiple" in lowered or "conflict" in lowered:
                return "conflicting"
            if "normalize" in lowered or "invalid" in lowered:
                return "invalid"
            return "unsupported"
        return None

    @staticmethod
    def _normalized_date(value: Any) -> str | None:
        text = str(value or "").strip()
        for pattern in ("%Y-%m-%d", "%m/%d/%Y", "%m-%d-%Y"):
            try:
                return datetime.strptime(text, pattern).strftime("%Y-%m-%d")
            except ValueError:
                continue
        return None

    @classmethod
    def _posted_date_is_explicit(cls, value: str, source_text: str) -> bool:
        pattern = re.compile(
            r"\bposted\s+date\b\s*[:#-]?\s*"
            r"(\d{1,2}[/-]\d{1,2}[/-]\d{4}|\d{4}-\d{2}-\d{2})",
            re.IGNORECASE,
        )
        return any(
            cls._normalized_date(match.group(1)) == value
            for match in pattern.finditer(source_text)
        )

    @staticmethod
    def _qualifier_is_explicit(value: str, source_text: str) -> bool:
        return re.search(
            r"\brenewal\s+qualifier\b\s*[:#-]?\s*"
            + re.escape(value)
            + r"(?=\s|$|[.,;])",
            source_text,
            re.IGNORECASE,
        ) is not None

    @staticmethod
    def _normalize_token(value: Any) -> str:
        return " ".join(str(value or "").strip().upper().split())

    @classmethod
    def _lookup_value(cls, result: Any) -> str | None:
        if not isinstance(result, LookupResult) or not result.resolved:
            return None
        value = cls._normalize_token(result.value)
        return value or None

    @staticmethod
    def _safe_status(value: Any) -> str:
        normalized = re.sub(
            r"[^a-z0-9_]+",
            "_",
            str(value or "unresolved").strip().lower(),
        ).strip("_")
        return normalized or "unresolved"

    @classmethod
    def _resolved(
        cls,
        value: str,
        confidence: Any,
        source_text: str,
    ) -> ValidatedFilenameInput:
        normalized_confidence = 0.0
        if not isinstance(confidence, bool) and isinstance(
            confidence,
            (int, float),
        ):
            normalized_confidence = max(0.0, min(float(confidence), 1.0))
        return ValidatedFilenameInput(
            lookup=LookupResult(True, value, "resolved"),
            confidence=normalized_confidence,
            source_text=source_text,
        )

    @staticmethod
    def _unresolved(
        status: str,
        *,
        source_text: str = "",
    ) -> ValidatedFilenameInput:
        return ValidatedFilenameInput(
            lookup=LookupResult(False, None, status),
            confidence=0.0,
            source_text=source_text,
        )
