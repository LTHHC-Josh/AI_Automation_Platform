from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from src.models.document import Document
from src.services.field_validation_diagnostic_service import FieldValidationDiagnosticService
from src.services.filename_policy_service import (
    FilenamePolicyRequest, FilenamePolicyResult, FilenamePolicyService,
)
from src.services.reference_table_service import (
    LookupResult, ReferenceTableLoader, ReferenceTables,
)


@dataclass(frozen=True)
class FilenameReadinessDiagnostic:
    person_components_ready: bool
    payer_lookup_ready: bool
    service_lookup_ready: bool
    dates_ready: bool
    workflow_ready: bool
    qualifier_status: str
    filename_result: str
    filename_failure_category: str = "none"
    business_filename_attempted: bool = True
    required_component_failure_count: int = 0
    optional_component_omission_count: int = 0
    service_component_status: str = "Omitted"
    form_component_status: str = "Omitted"
    workflow_component_status: str = "Omitted"
    extension_ready: bool = False
    extension_component_status: str = "Unresolved"
    payer_lookup_status: str = "unresolved"


@dataclass(frozen=True)
class ProductionFilenameAssemblyResult:
    policy_result: FilenamePolicyResult = field(repr=False)
    business_name_resolved: bool = False
    status: str = "unresolved"
    business_filename_attempted: bool = True
    required_component_failure_count: int = 0
    optional_component_omission_count: int = 0
    diagnostic: FilenameReadinessDiagnostic | None = field(
        default=None,
        repr=False,
    )


class ProductionFilenameAssemblyService:
    """Assemble a business filename from authoritative final field state."""

    MINIMUM_EVIDENCE_CONFIDENCE = 0.85
    CACHE_PATH = Path("data/reference_cache/reference_tables.xlsx")

    def __init__(self, *, tables_provider: Callable[[], ReferenceTables | None] | None = None,
                 policy_service: FilenamePolicyService | None = None,
                 diagnostic_service: FieldValidationDiagnosticService | None = None) -> None:
        self.tables_provider = tables_provider or self._cached_tables
        self.policy_service = policy_service or FilenamePolicyService()
        self.diagnostic_service = diagnostic_service or FieldValidationDiagnosticService()

    def evaluate(
        self,
        *,
        document: Any,
        source_extension: Any,
    ) -> ProductionFilenameAssemblyResult:
        if not isinstance(document, Document):
            diagnostic = FilenameReadinessDiagnostic(
                False, False, False, False, False, "Not Required",
                "technical_fallback", "processed_document_unavailable",
                False, 0, 5,
                extension_ready=False,
                extension_component_status="Unresolved",
                payer_lookup_status="unavailable",
            )
            return self._failure(
                "processed_document_unavailable",
                attempted=False,
                required_failure_count=0,
                diagnostic=diagnostic,
            )

        try:
            tables = self.tables_provider()
        except Exception:
            tables = None
        tables_ready = isinstance(tables, ReferenceTables)

        first = self._accepted_scalar(document, "person_first")
        last = self._accepted_scalar(document, "person_last")
        middle = self._accepted_scalar(document, "person_middle")
        person_ready = first is not None and last is not None

        payer = self._accepted_scalar(document, "payer")
        payer_lookup = (
            tables.payors.lookup(payer, "")
            if tables_ready and payer is not None
            else None
        )
        payer_ready = bool(
            isinstance(payer_lookup, LookupResult) and payer_lookup.resolved
        )
        if payer is None:
            payer_lookup_status = "evidence_unresolved"
        elif not tables_ready:
            payer_lookup_status = "reference_unavailable"
        elif isinstance(payer_lookup, LookupResult):
            payer_lookup_status = (
                "resolved" if payer_lookup.resolved else payer_lookup.status
            )
        else:
            payer_lookup_status = "not_resolved"

        start_date = self._accepted_scalar(document, "start_date")
        end_date = self._accepted_scalar(document, "end_date")
        line_start, line_end = self._service_line_dates(document)
        start_date = start_date or line_start
        end_date = end_date or line_end
        service_lookup = None
        service = self._single_service_identity(document)
        if service is not None:
            code, modifier, program, line_start, line_end = service
            if tables_ready:
                candidate_lookup = tables.services.lookup(
                    code, modifier, program
                )
                if candidate_lookup.resolved:
                    service_lookup = candidate_lookup
            start_date = start_date or line_start
            end_date = end_date or line_end

        category = str(document.document_category or "").strip().lower()
        category_supported = document.classification_support_status == "supported"
        subtype_supported = document.subtype_support_status == "supported"
        policy_category = category if category_supported else "unknown"
        policy_subtype = (
            str(document.document_subtype or "unknown").strip().lower()
            if category_supported and subtype_supported else "unknown"
        )
        form_type = "2067" if policy_category == "2067" else None
        posted_date = self._accepted_scalar(document, "posted_date")
        workflow_ready = self._workflow_ready(policy_category, policy_subtype)
        service_status = (
            "Ready" if service_lookup is not None
            else ("Unresolved" if service is not None else "Omitted")
        )
        form_status = "Ready" if form_type is not None else "Omitted"
        workflow_status = "Ready" if workflow_ready else "Omitted"
        qualifier_evidence = document.field_evidence.get("renewal_qualifier")
        qualifier_claimed = bool(
            isinstance(qualifier_evidence, dict)
            and qualifier_evidence.get("value") is not None
        )
        qualifier_status = (
            "Unresolved" if qualifier_claimed else "Not Required"
        )
        omissions = self._optional_omission_count(
            middle=middle, service_ready=service_lookup is not None,
            form_ready=form_type is not None, workflow_ready=workflow_ready,
            qualifier_ready=False,
        )

        request = FilenamePolicyRequest(
            person_last=last, person_first=first, person_middle=middle,
            payer_lookup=payer_lookup,
            service_applicable=service_lookup is not None,
            service_lookup=service_lookup, form_type=form_type,
            document_category=policy_category, document_subtype=policy_subtype,
            posted_date_lookup=(
                LookupResult(True, posted_date, "resolved")
                if form_type == "2067" and posted_date is not None else None
            ),
            start_date=start_date, end_date=end_date,
            source_extension=source_extension,
        )
        date_status = self.policy_service.date_status(request)
        dates_ready = date_status == "resolved"
        extension_ready = self.policy_service.extension_supported(
            source_extension
        )

        # Invoke the approved policy for every valid new document. Component
        # readiness is still evaluated independently so the operator receives
        # a complete, PHI-safe explanation instead of only the first failure.
        policy = self.policy_service.resolve(request)
        required_failures = []
        if not person_ready:
            required_failures.append("person")
        if not payer_ready:
            required_failures.append("payer")
        if not dates_ready:
            required_failures.append("date")
        if not extension_ready:
            required_failures.append("extension")

        if not tables_ready:
            failure_category = "authoritative_reference_unavailable"
        elif not person_ready:
            failure_category = "person_components_unresolved"
        elif payer is None:
            failure_category = "payer_evidence_unresolved"
        elif not payer_ready:
            failure_category = "payer_reference_unresolved"
        elif not dates_ready:
            failure_category = date_status
        elif not extension_ready:
            failure_category = "source_extension_unsupported"
        elif not policy.complete:
            failure_category = policy.status
            required_failures.append("safe_composition")
        else:
            failure_category = "none"

        business_resolved = failure_category == "none" and policy.complete
        effective_policy = (
            policy
            if business_resolved
            else FilenamePolicyResult(
                False, None, True, failure_category
            )
        )
        diagnostic = FilenameReadinessDiagnostic(
            person_ready,
            payer_ready,
            service_lookup is not None,
            dates_ready,
            workflow_ready,
            qualifier_status,
            "business" if business_resolved else "technical_fallback",
            failure_category,
            True,
            len(required_failures),
            omissions,
            service_status,
            form_status,
            workflow_status,
            extension_ready,
            "Ready" if extension_ready else "Unresolved",
            payer_lookup_status,
        )
        return ProductionFilenameAssemblyResult(
            effective_policy,
            business_resolved,
            effective_policy.status,
            True,
            len(required_failures),
            omissions,
            diagnostic,
        )

    def resolve(
        self,
        *,
        document: Any,
        source_extension: Any,
    ) -> ProductionFilenameAssemblyResult:
        return self.evaluate(
            document=document,
            source_extension=source_extension,
        )

    def diagnose(self, *, document: Any, source_extension: Any) -> FilenameReadinessDiagnostic:
        result = self.evaluate(
            document=document,
            source_extension=source_extension,
        )
        if result.diagnostic is not None:
            return result.diagnostic
        return FilenameReadinessDiagnostic(
            False, False, False, False, False, "Not Required",
            "technical_fallback", result.status,
            result.business_filename_attempted,
            result.required_component_failure_count,
            result.optional_component_omission_count,
        )

    def _single_service_identity(self, document: Document):
        identities = set()
        program = self._accepted_scalar(document, "program") or ""
        for index, line in enumerate(document.service_lines or []):
            if self.diagnostic_service.build_service_line(
                document, index, "service_code"
            ).field_state != "accepted":
                continue
            code = str(getattr(line, "service_code", None) or "").strip()
            if not code:
                continue
            modifier = (
                str(getattr(line, "modifier", None) or "").strip()
                if self.diagnostic_service.build_service_line(
                    document, index, "modifier"
                ).field_state == "accepted" else ""
            )
            start = self._accepted_line_component(
                document, index, "start_date"
            )
            end = self._accepted_line_component(
                document, index, "end_date"
            )
            identities.add((code, modifier, program, start, end))
        if len(identities) == 1:
            return next(iter(identities))
        if identities:
            return None

        codes = self._accepted_value(document, "service_codes")
        if not isinstance(codes, list):
            codes = [codes] if codes is not None else []
        codes = [str(value).strip() for value in codes if str(value or "").strip()]
        if len(set(codes)) != 1:
            single = self._accepted_scalar(document, "service_code")
            codes = [single] if single else []
        if len(codes) != 1:
            return None
        return (
            codes[0], self._accepted_scalar(document, "modifier") or "", program,
            self._accepted_scalar(document, "start_date"),
            self._accepted_scalar(document, "end_date"),
        )

    def _service_line_dates(self, document: Document):
        starts = set()
        ends = set()
        for index, line in enumerate(document.service_lines or []):
            start = self._accepted_line_component(
                document, index, "start_date"
            ) or ""
            end = self._accepted_line_component(
                document, index, "end_date"
            ) or ""
            if start:
                starts.add(start)
            if end:
                ends.add(end)
        return (
            next(iter(starts)) if len(starts) == 1 else None,
            next(iter(ends)) if len(ends) == 1 else None,
        )

    def _accepted_line_component(
        self, document: Document, index: int, component: str
    ):
        diagnostic = self.diagnostic_service.build_service_line(
            document, index, component
        )
        if diagnostic.field_state != "accepted":
            return None
        value = getattr(document.service_lines[index], component, None)
        normalized = " ".join(str(value or "").strip().split())
        if not normalized or any(
            character in normalized for character in "_\\/\r\n"
        ):
            return None
        return normalized

    def _accepted_value(self, document: Document, field_name: str):
        if self.diagnostic_service.build(document, field_name).field_state != "accepted":
            return None
        evidence = document.field_evidence.get(field_name)
        return evidence.get("value") if isinstance(evidence, dict) else document.extracted_data.get(field_name)

    def _accepted_scalar(self, document: Document, field_name: str):
        value = self._accepted_value(document, field_name)
        if not isinstance(value, str) or not value.strip():
            return None
        normalized = " ".join(value.strip().split())
        if any(character in normalized for character in "_\\/\r\n"):
            return None
        return normalized

    @staticmethod
    def _workflow_ready(category: str, subtype: str) -> bool:
        return category == "authorization" and subtype in {"initial", "renewal"}

    @staticmethod
    def _optional_omission_count(*, middle, service_ready, form_ready,
                                 workflow_ready, qualifier_ready) -> int:
        return sum((not bool(middle), not bool(service_ready), not bool(form_ready),
                    not bool(workflow_ready), not bool(qualifier_ready)))

    @classmethod
    def _cached_tables(cls):
        loaded = ReferenceTableLoader().load(cls.CACHE_PATH)
        return loaded.tables if loaded.success else None

    @staticmethod
    def _failure(
        status: str,
        *,
        attempted: bool = True,
        required_failure_count: int = 1,
        diagnostic: FilenameReadinessDiagnostic | None = None,
    ):
        return ProductionFilenameAssemblyResult(
            FilenamePolicyResult(False, None, True, status),
            False,
            status,
            attempted,
            required_failure_count,
            0,
            diagnostic,
        )
