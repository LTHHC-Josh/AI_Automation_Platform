from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from src.models.document_processor_business_context import (
    DOCUMENT_PROCESSOR_BUSINESS_CONTEXT,
)
from src.models.document import Document
from src.services.field_validation_diagnostic_service import FieldValidationDiagnosticService
from src.services.filename_policy_service import (
    FilenamePolicyRequest, FilenamePolicyResult, FilenamePolicyService,
)
from src.services.intake_document_naming_service import (
    IntakeDocumentNamingVocabulary,
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
    document_type_component_status: str = "Unresolved"
    subtype_component_status: str = "Omitted"
    placeholder_count: int = 0
    placeholder_categories: tuple[str, ...] = ()
    technical_fallback_reason: str = "none"


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
    business_context_version: int = (
        DOCUMENT_PROCESSOR_BUSINESS_CONTEXT.business_context_version
    )


class ProductionFilenameAssemblyService:
    """Assemble a business filename from authoritative final field state."""

    MINIMUM_EVIDENCE_CONFIDENCE = (
        DOCUMENT_PROCESSOR_BUSINESS_CONTEXT.confidence_policy.field_acceptance
    )
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
                person_components_ready=False,
                payer_lookup_ready=False,
                service_lookup_ready=False,
                dates_ready=False,
                workflow_ready=False,
                qualifier_status="Not Applicable",
                filename_result="technical_fallback",
                filename_failure_category="processed_document_unavailable",
                business_filename_attempted=False,
                required_component_failure_count=0,
                optional_component_omission_count=0,
                extension_ready=False,
                extension_component_status="Unresolved",
                payer_lookup_status="unavailable",
                technical_fallback_reason="processed_document_unavailable",
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
            if tables_ready and payer is not None else None
        )
        payer_ready = bool(
            isinstance(payer_lookup, LookupResult) and payer_lookup.resolved
        )
        if payer is None:
            payer_lookup_status = "evidence_unresolved"
        elif not tables_ready:
            payer_lookup_status = "reference_unavailable"
        elif isinstance(payer_lookup, LookupResult):
            payer_lookup_status = "resolved" if payer_lookup.resolved else payer_lookup.status
        else:
            payer_lookup_status = "not_resolved"

        start_date = self._accepted_scalar(document, "start_date")
        end_date = self._accepted_scalar(document, "end_date")
        line_start, line_end = self._service_line_dates(document)
        start_date = start_date or line_start
        end_date = end_date or line_end

        service_lookup = None
        service_identities = self._service_identities(document)
        service_expected = self._service_expected(document)
        if service_identities and tables_ready:
            candidate_lookups = [
                tables.services.lookup(code, modifier, program)
                for code, modifier, program in service_identities
            ]
            resolved_values = {
                lookup.value
                for lookup in candidate_lookups
                if lookup.resolved
            }
            if (
                all(lookup.resolved for lookup in candidate_lookups)
                and len(resolved_values) == 1
            ):
                service_lookup = candidate_lookups[0]

        document_type = IntakeDocumentNamingVocabulary.resolve(document)
        category = str(document.document_category or "").strip().lower()
        form_type = "2067" if category == "2067" else None
        posted_date = self._accepted_scalar(document, "posted_date")
        request = FilenamePolicyRequest(
            person_last=last,
            person_first=first,
            person_middle=middle,
            payer_lookup=payer_lookup,
            service_applicable=service_expected,
            service_lookup=service_lookup,
            document_type_resolution=document_type,
            form_type=form_type,
            document_category=category,
            document_subtype=document.document_subtype,
            posted_date_lookup=(
                LookupResult(True, posted_date, "resolved")
                if form_type == "2067" and posted_date is not None else None
            ),
            start_date=start_date,
            end_date=end_date,
            source_extension=source_extension,
        )
        date_status = self.policy_service.date_status(request)
        dates_ready = date_status == "resolved"
        extension_ready = self.policy_service.extension_supported(source_extension)
        policy = self.policy_service.resolve(request)

        required_failures = []
        if not person_ready:
            required_failures.append("person")
        if not extension_ready:
            required_failures.append("extension")
        if not policy.complete and person_ready and extension_ready:
            required_failures.append("safe_composition")

        business_available = policy.complete
        failure_category = "none" if business_available else policy.status
        result_name = policy.filename_result if business_available else "technical_fallback"
        service_status = (
            "Ready" if service_lookup is not None
            else ("Placeholder" if service_expected else "Omitted")
        )
        diagnostic = FilenameReadinessDiagnostic(
            person_components_ready=person_ready,
            payer_lookup_ready=payer_ready,
            service_lookup_ready=service_lookup is not None,
            dates_ready=dates_ready,
            workflow_ready=document_type.subtype_status == "Ready",
            qualifier_status="Not Applicable",
            filename_result=result_name,
            filename_failure_category=failure_category,
            business_filename_attempted=True,
            required_component_failure_count=len(required_failures),
            optional_component_omission_count=policy.optional_omission_count,
            service_component_status=service_status,
            form_component_status=("Ready" if category == "2067" else "Omitted"),
            workflow_component_status=document_type.subtype_status,
            extension_ready=extension_ready,
            extension_component_status=("Ready" if extension_ready else "Unresolved"),
            payer_lookup_status=payer_lookup_status,
            document_type_component_status=document_type.document_type_status,
            subtype_component_status=document_type.subtype_status,
            placeholder_count=len(policy.placeholder_categories),
            placeholder_categories=policy.placeholder_categories,
            technical_fallback_reason=failure_category,
        )
        return ProductionFilenameAssemblyResult(
            policy,
            business_available,
            policy.status,
            True,
            len(required_failures),
            policy.optional_omission_count,
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
            person_components_ready=False,
            payer_lookup_ready=False,
            service_lookup_ready=False,
            dates_ready=False,
            workflow_ready=False,
            qualifier_status="Not Applicable",
            filename_result="technical_fallback",
            filename_failure_category=result.status,
            business_filename_attempted=result.business_filename_attempted,
            required_component_failure_count=result.required_component_failure_count,
            optional_component_omission_count=result.optional_component_omission_count,
            technical_fallback_reason=result.status,
        )

    @staticmethod
    def _service_expected(document: Document) -> bool:
        for field_name in ("service_code", "service_codes"):
            evidence = document.field_evidence.get(field_name)
            if isinstance(evidence, dict):
                for key in ("value", "candidate_value"):
                    if evidence.get(key) not in (None, "", [], {}):
                        return True
        for line in document.service_lines or []:
            candidate = getattr(line, "candidate_evidence", {})
            if isinstance(candidate, dict) and candidate.get("service_code") not in (
                None, ""
            ):
                return True
            if str(getattr(line, "service_code", None) or "").strip():
                return True
        return False

    def _service_identities(self, document: Document):
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
            identities.add((code, modifier, program))
        if identities:
            return tuple(sorted(identities))

        codes = self._accepted_value(document, "service_codes")
        if not isinstance(codes, list):
            codes = [codes] if codes is not None else []
        codes = [str(value).strip() for value in codes if str(value or "").strip()]
        if len(set(codes)) != 1:
            single = self._accepted_scalar(document, "service_code")
            codes = [single] if single else []
        if len(codes) != 1:
            return ()
        return ((
            codes[0], self._accepted_scalar(document, "modifier") or "", program,
        ),)

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
            policy_result=FilenamePolicyResult(
                complete=False,
                filename=None,
                review_required=True,
                status=status,
                filename_result="technical_fallback",
            ),
            business_name_resolved=False,
            status=status,
            business_filename_attempted=attempted,
            required_component_failure_count=required_failure_count,
            optional_component_omission_count=0,
            diagnostic=diagnostic,
        )
