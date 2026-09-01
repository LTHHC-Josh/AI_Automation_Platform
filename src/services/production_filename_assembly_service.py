from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from src.models.document import Document
from src.services.filename_policy_service import (
    FilenamePolicyRequest,
    FilenamePolicyResult,
    FilenamePolicyService,
)
from src.services.reference_table_service import (
    LookupResult,
    ReferenceTableLoader,
    ReferenceTables,
)


@dataclass(frozen=True)
class ProductionFilenameAssemblyResult:
    policy_result: FilenamePolicyResult = field(repr=False)
    business_name_resolved: bool = False
    status: str = "unresolved"


@dataclass(frozen=True)
class FilenameReadinessDiagnostic:
    person_components_ready: bool
    payer_lookup_ready: bool
    service_lookup_ready: bool
    dates_ready: bool
    workflow_ready: bool
    qualifier_status: str
    filename_result: str


class ProductionFilenameAssemblyService:
    """Assemble a filename only from independently supported evidence."""

    MINIMUM_EVIDENCE_CONFIDENCE = 0.85
    CACHE_PATH = Path("data/reference_cache/reference_tables.xlsx")

    def __init__(self, *, tables_provider: Callable[[], ReferenceTables | None] | None = None,
                 policy_service: FilenamePolicyService | None = None) -> None:
        self.tables_provider = tables_provider or self._cached_tables
        self.policy_service = policy_service or FilenamePolicyService()

    def resolve(self, *, document: Any, source_extension: Any) -> ProductionFilenameAssemblyResult:
        if not isinstance(document, Document):
            return self._failure("processed_document_unavailable")
        try:
            tables = self.tables_provider()
        except Exception:
            tables = None
        if not isinstance(tables, ReferenceTables):
            return self._failure("authoritative_reference_unavailable")

        first = self._supported_scalar(document, "person_first")
        last = self._supported_scalar(document, "person_last")
        middle = self._supported_scalar(document, "person_middle", required=False)
        if first is None or last is None:
            return self._failure("independent_person_name_unresolved")

        payer = self._supported_scalar(document, "payer")
        if payer is None:
            return self._failure("payer_evidence_unresolved")
        payer_lookup = tables.payors.lookup(payer, "")

        service_applicable = str(document.document_category or "").strip().lower() == "authorization"
        if service_applicable and (
            document.classification_support_status != "supported"
            or document.subtype_support_status != "supported"
        ):
            return self._failure("classification_evidence_unresolved")
        service_lookup = None
        start_date = self._supported_scalar(document, "start_date", required=False)
        end_date = self._supported_scalar(document, "end_date", required=False)
        if service_applicable:
            qualifier_evidence = document.field_evidence.get("renewal_qualifier")
            if isinstance(qualifier_evidence, dict) and qualifier_evidence.get("value") is not None:
                return self._failure("qualifier_reference_unavailable")
            service = self._single_service_identity(document)
            if service is None:
                return self._failure("service_identity_unresolved")
            code, modifier, program, line_start, line_end = service
            service_lookup = tables.services.lookup(code, modifier, program)
            start_date = line_start or start_date
            end_date = line_end or end_date

        request = FilenamePolicyRequest(
            person_last=last,
            person_first=first,
            person_middle=middle,
            payer_lookup=payer_lookup,
            service_applicable=service_applicable,
            service_lookup=service_lookup,
            document_category=document.document_category,
            document_subtype=document.document_subtype,
            start_date=start_date,
            end_date=end_date,
            source_extension=source_extension,
        )
        policy = self.policy_service.resolve(request)
        return ProductionFilenameAssemblyResult(
            policy_result=policy,
            business_name_resolved=policy.complete,
            status=policy.status,
        )

    def diagnose(self, *, document: Any, source_extension: Any) -> FilenameReadinessDiagnostic:
        if not isinstance(document, Document):
            return FilenameReadinessDiagnostic(False, False, False, False, False, "Unresolved", "Technical Fallback")
        try:
            tables = self.tables_provider()
        except Exception:
            tables = None
        first = self._supported_scalar(document, "person_first")
        last = self._supported_scalar(document, "person_last")
        person_ready = first is not None and last is not None
        payer = self._supported_scalar(document, "payer")
        payer_ready = bool(
            isinstance(tables, ReferenceTables)
            and payer is not None
            and tables.payors.lookup(payer, "").resolved
        )
        service_applicable = str(document.document_category or "").strip().lower() == "authorization"
        service = self._single_service_identity(document) if service_applicable else None
        service_ready = not service_applicable
        dates_ready = False
        if service_applicable and service is not None and isinstance(tables, ReferenceTables):
            code, modifier, program, start, end = service
            service_ready = tables.services.lookup(code, modifier, program).resolved
            dates_ready = bool(start or end)
        elif not service_applicable:
            dates_ready = bool(
                self._supported_scalar(document, "start_date", required=False)
                or self._supported_scalar(document, "end_date", required=False)
            )
        workflow_ready = (
            document.classification_support_status == "supported"
            and document.subtype_support_status == "supported"
        )
        qualifier_evidence = document.field_evidence.get("renewal_qualifier")
        qualifier_status = (
            "Unresolved"
            if isinstance(qualifier_evidence, dict) and qualifier_evidence.get("value") is not None
            else "Not Required"
        )
        resolved = self.resolve(document=document, source_extension=source_extension)
        return FilenameReadinessDiagnostic(
            person_ready,
            payer_ready,
            service_ready,
            dates_ready,
            workflow_ready,
            qualifier_status,
            "Business" if resolved.business_name_resolved else "Technical Fallback",
        )

    def _single_service_identity(self, document: Document):
        identities = set()
        program = self._supported_scalar(document, "program", required=False)
        program_evidence = document.field_evidence.get("program")
        if (
            isinstance(program_evidence, dict)
            and program_evidence.get("value") is not None
            and program is None
        ):
            return None
        for line in document.service_lines or []:
            code = str(getattr(line, "service_code", None) or "").strip()
            if not code:
                continue
            modifier = str(getattr(line, "modifier", None) or "").strip()
            exact_program = program or ""
            start = str(getattr(line, "start_date", None) or "").strip() or None
            end = str(getattr(line, "end_date", None) or "").strip() or None
            identities.add((code, modifier, exact_program, start, end))
        return next(iter(identities)) if len(identities) == 1 else None

    @classmethod
    def _supported_scalar(cls, document: Document, field_name: str, *, required: bool = True):
        evidence = document.field_evidence.get(field_name)
        if not isinstance(evidence, dict):
            return None
        value = evidence.get("value")
        confidence = evidence.get("confidence")
        source = str(evidence.get("source_text") or "")
        if not isinstance(value, str) or not value.strip():
            return None
        if isinstance(confidence, bool) or not isinstance(confidence, (int, float)):
            return None
        if float(confidence) < cls.MINIMUM_EVIDENCE_CONFIDENCE:
            return None
        normalized = " ".join(value.strip().split())
        if normalized.casefold() not in " ".join(source.split()).casefold():
            return None
        if any(character in normalized for character in "_\\/\r\n"):
            return None
        prefix = f"{field_name} "
        if any(str(action or "").startswith(prefix) for action in document.validation_actions or []):
            return None
        return normalized

    @classmethod
    def _cached_tables(cls):
        loaded = ReferenceTableLoader().load(cls.CACHE_PATH)
        return loaded.tables if loaded.success else None

    @staticmethod
    def _failure(status: str) -> ProductionFilenameAssemblyResult:
        return ProductionFilenameAssemblyResult(
            FilenamePolicyResult(False, None, True, status), False, status
        )
