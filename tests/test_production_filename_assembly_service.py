from pathlib import Path
import tempfile

from src.models.document import AuthorizationServiceLine, Document
from src.services.document_attachment_naming_service import DocumentAttachmentNamingService
from src.services.filename_policy_service import (
    FilenamePolicyResult,
    FilenamePolicyService,
)
from src.services.production_filename_assembly_service import ProductionFilenameAssemblyService
from src.services.reference_table_service import PayorReferenceTable, ReferenceTables, ServiceReferenceTable
from src.services.mailbox_document_job_state_service import MailboxDocumentJobStateService, MailboxDocumentWorkItem
from src.services.mailbox_document_smartsheet_recovery_service import MailboxDocumentSmartsheetRecoveryService


def evidence(value, confidence=0.95):
    return {"value": value, "confidence": confidence, "source_text": f"Supported: {value}"}


def tables():
    return ReferenceTables(
        PayorReferenceTable({("SYNTHETIC PLAN", ""): "PLAN"}),
        ServiceReferenceTable({("T0000", "U1", ""): {"SERVICE"}}),
    )


def document():
    subject = Document(
        file_path=Path("synthetic.pdf"),
        document_category="authorization",
        document_subtype="initial",
        classification_support_status="supported",
        subtype_support_status="supported",
    )
    subject.field_evidence = {
        "person_last": evidence("EXAMPLE"),
        "person_first": evidence("SYNTHETIC"),
        "person_middle": evidence("Q"),
        "payer": evidence("SYNTHETIC PLAN"),
    }
    subject.service_lines = [AuthorizationServiceLine(
        service_code="T0000", modifier="U1",
        start_date="2026-01-02", end_date="2026-02-03",
        confidence=0.95,
    )]
    return subject


def test_complete_independently_supported_inputs_use_existing_policy_format():
    result = ProductionFilenameAssemblyService(tables_provider=tables).resolve(
        document=document(), source_extension=".pdf"
    )
    assert result.business_name_resolved is True
    assert result.policy_result.filename == (
        "EXAMPLE SYNTHETIC Q_PLAN_SERVICE_AUTH INIT_010226-020326.pdf"
    )
    repeated = ProductionFilenameAssemblyService(tables_provider=tables).resolve(
        document=document(), source_extension=".pdf"
    )
    assert repeated.policy_result.filename == result.policy_result.filename


def test_combined_name_and_context_cannot_replace_independent_components():
    subject = document()
    subject.field_evidence.pop("person_first")
    subject.field_evidence.pop("person_last")
    subject.field_evidence["patient_name"] = evidence("Synthetic Combined")
    subject.field_evidence["sender"] = evidence("Synthetic Sender")
    result = ProductionFilenameAssemblyService(tables_provider=tables).resolve(
        document=subject, source_extension=".pdf"
    )
    assert result.business_name_resolved is False
    assert result.status == "person_components_unresolved"
    assert result.policy_result.filename is None


def test_low_confidence_or_ambiguous_service_uses_fallback_without_guessing():
    subject = document()
    subject.field_evidence["person_first"] = evidence("SYNTHETIC", 0.50)
    unresolved_name = ProductionFilenameAssemblyService(tables_provider=tables).resolve(
        document=subject, source_extension=".pdf"
    )
    assert unresolved_name.status == "person_components_unresolved"

    subject = document()
    subject.service_lines.append(AuthorizationServiceLine(
        service_code="T9999", modifier="", start_date="2026-01-02",
        end_date="2026-02-03", confidence=0.95,
    ))
    unresolved_service = ProductionFilenameAssemblyService(tables_provider=tables).resolve(
        document=subject, source_extension=".pdf"
    )
    assert unresolved_service.business_name_resolved is True
    assert "SERVICE" not in unresolved_service.policy_result.filename

    subject = document()
    subject.field_evidence["program"] = evidence("UNSUPPORTED", 0.50)
    unresolved_program = ProductionFilenameAssemblyService(tables_provider=tables).resolve(
        document=subject, source_extension=".pdf"
    )
    assert unresolved_program.business_name_resolved is True


def test_optional_qualifier_claim_is_omitted_without_authoritative_lookup():
    subject = document()
    subject.document_subtype = "renewal"
    subject.field_evidence["renewal_qualifier"] = evidence("SYNTHETIC QUALIFIER")
    result = ProductionFilenameAssemblyService(tables_provider=tables).resolve(
        document=subject, source_extension=".pdf"
    )
    assert result.business_name_resolved is True
    assert "SYNTHETIC QUALIFIER" not in result.policy_result.filename


def test_technical_fallback_is_deterministic_non_phi_and_source_is_unchanged():
    service = DocumentAttachmentNamingService()
    unresolved = ProductionFilenameAssemblyService(tables_provider=lambda: None).resolve(
        document=document(), source_extension=".pdf"
    )
    with tempfile.TemporaryDirectory() as directory:
        source = Path(directory) / "synthetic-source.pdf"
        source.write_bytes(b"SYNTHETIC")
        first = service.prepare(source_path=source, filename_policy_result=unresolved.policy_result)
        second = service.prepare(source_path=source, filename_policy_result=unresolved.policy_result)
        assert first.temporary_path.name == second.temporary_path.name
        assert first.temporary_path.name.startswith("LTHHC_TECHNICAL_DOCUMENT_")
        assert len(first.temporary_path.stem.rsplit("_", 1)[-1]) == 64
        assert first.temporary_path.suffix == ".pdf"
        assert source.read_bytes() == b"SYNTHETIC"
        service.cleanup(first.temporary_path)
        service.cleanup(second.temporary_path)


def test_unsupported_extension_is_replaced_by_safe_bin_extension():
    service = DocumentAttachmentNamingService()
    with tempfile.TemporaryDirectory() as directory:
        source = Path(directory) / "synthetic.unsupported"
        source.write_bytes(b"SYNTHETIC")
        result = service.prepare(source_path=source)
        assert result.success is True
        assert result.temporary_path.suffix == ".bin"
        service.cleanup(result.temporary_path)


def test_extraction_schema_supports_separate_components_without_parsing_combined_name():
    from src.ai.llm.providers.ollama_provider import OllamaProvider

    assert {"person_first", "person_middle", "person_last", "program"} <= set(
        OllamaProvider.FIELD_NAMES
    )
    prompt = object.__new__(OllamaProvider)._extraction_prompt()
    assert "Do not split" in prompt
    assert "Do not infer program" in prompt


def test_recovery_persists_exact_business_name_before_external_write():
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        source = root / "synthetic.pdf"
        source.write_bytes(b"SYNTHETIC")
        jobs = MailboxDocumentJobStateService(root / "jobs")
        discovered = jobs.discover(
            message_key="a" * 64,
            attachment_key="b" * 64,
            document_key="c" * 64,
        ).state
        lease = jobs.acquire_processing_lease(discovered.job_key).state
        pending = jobs.transition(
            discovered.job_key,
            expected_stages={"processing"},
            stage="row_write_pending",
            lease_token=lease.lease_token,
        ).state
        recovery = MailboxDocumentSmartsheetRecoveryService(
            job_state_service=jobs,
            filename_assembly_service=ProductionFilenameAssemblyService(tables_provider=tables),
        )
        work_item = MailboxDocumentWorkItem(
            pending.job_key, "a" * 64, "b" * 64, "c" * 64,
            source, pending.stage, document(),
        )
        stored, status, diagnostic = recovery._ensure_attachment_name(
            work_item, pending
        )
        expected = "EXAMPLE SYNTHETIC Q_PLAN_SERVICE_AUTH INIT_010226-020326.pdf"
        assert status == "ready"
        assert stored.attachment_filename == expected
        assert stored.attachment_naming_status == "business_filename"
        assert diagnostic.filename_result == "business"
        assert diagnostic.extension_component_status == "Ready"
        reloaded = MailboxDocumentJobStateService(root / "jobs").load(pending.job_key).state
        assert reloaded.attachment_filename == expected
        assert pending.job_key not in expected
        assert source.read_bytes() == b"SYNTHETIC"


def test_filename_readiness_diagnostics_are_phi_safe_and_match_result():
    service = ProductionFilenameAssemblyService(tables_provider=tables)
    ready = service.diagnose(document=document(), source_extension=".pdf")
    assert ready.person_components_ready is True
    assert ready.payer_lookup_ready is True
    assert ready.service_lookup_ready is True
    assert ready.dates_ready is True
    assert ready.workflow_ready is True
    assert ready.qualifier_status == "Not Required"
    assert ready.filename_result == "business"

    unresolved = document()
    unresolved.field_evidence["person_first"]["value"] = None
    fallback = service.diagnose(document=unresolved, source_extension=".pdf")
    assert fallback.person_components_ready is False
    assert fallback.filename_result == "technical_fallback"
    assert "EXAMPLE" not in repr(fallback)


def test_unique_authoritative_service_resolves_when_modifier_and_program_are_absent():
    subject = document()
    subject.service_lines[0].modifier = None
    result = ProductionFilenameAssemblyService(tables_provider=tables).resolve(
        document=subject, source_extension=".pdf")
    assert result.business_name_resolved is True
    assert "SERVICE" in result.policy_result.filename


def test_single_supported_service_date_is_ready_and_policy_supported():
    subject = document()
    subject.service_lines[0].end_date = None
    service = ProductionFilenameAssemblyService(tables_provider=tables)
    diagnostic = service.diagnose(document=subject, source_extension=".pdf")
    result = service.resolve(document=subject, source_extension=".pdf")
    assert diagnostic.dates_ready is True
    assert result.business_name_resolved is True


def test_top_level_validated_service_identity_can_resolve_business_filename():
    subject = document()
    subject.service_lines = []
    subject.field_evidence.update({
        "service_codes": evidence(["T0000"]),
        "modifier": evidence("U1"),
        "start_date": evidence("2026-01-02"),
        "end_date": evidence("2026-02-03"),
    })
    subject.extracted_data = {
        "service_codes": ["T0000"],
        "modifier": "U1",
        "start_date": "2026-01-02",
        "end_date": "2026-02-03",
    }
    result = ProductionFilenameAssemblyService(tables_provider=tables).resolve(
        document=subject, source_extension=".pdf"
    )
    diagnostic = ProductionFilenameAssemblyService(tables_provider=tables).diagnose(
        document=subject, source_extension=".pdf"
    )
    assert result.business_name_resolved is True
    assert diagnostic.filename_failure_category == "none"


def test_filename_failure_category_is_safe_and_scoped_to_naming():
    subject = document()
    subject.field_evidence.pop("person_first")
    diagnostic = ProductionFilenameAssemblyService(tables_provider=tables).diagnose(
        document=subject, source_extension=".pdf"
    )
    assert diagnostic.filename_result == "technical_fallback"
    assert diagnostic.filename_failure_category == "person_components_unresolved"


def test_unknown_subtype_and_missing_optional_tokens_still_use_business_name():
    subject = document()
    subject.document_subtype = "unknown"
    subject.subtype_support_status = "missing"
    subject.field_evidence.pop("person_middle")
    subject.service_lines[0].end_date = None
    service = ProductionFilenameAssemblyService(tables_provider=tables)
    result = service.resolve(document=subject, source_extension=".pdf")
    diagnostic = service.diagnose(document=subject, source_extension=".pdf")
    assert result.business_name_resolved is True
    assert "AUTH INIT" not in result.policy_result.filename
    assert "RENEW AUTH" not in result.policy_result.filename
    assert result.policy_result.filename.endswith("_010226.pdf")
    assert diagnostic.business_filename_attempted is True
    assert diagnostic.filename_result == "business"
    assert diagnostic.filename_failure_category == "none"
    assert diagnostic.required_component_failure_count == 0
    assert diagnostic.optional_component_omission_count >= 1
    assert diagnostic.workflow_component_status == "Omitted"


def test_missing_or_ambiguous_optional_service_does_not_force_fallback():
    subject = document()
    subject.service_lines = []
    subject.field_evidence.update({
        "start_date": evidence("2026-01-02"),
        "end_date": {"value": None, "confidence": None, "source_text": ""},
    })
    subject.extracted_data = {"start_date": "2026-01-02", "end_date": None}
    service = ProductionFilenameAssemblyService(tables_provider=tables)
    result = service.resolve(document=subject, source_extension=".pdf")
    assert result.business_name_resolved is True
    assert "SERVICE" not in result.policy_result.filename
    assert result.policy_result.filename.endswith("_010226.pdf")


def test_safe_non_pdf_extension_can_use_business_name():
    result = ProductionFilenameAssemblyService(tables_provider=tables).resolve(
        document=document(), source_extension=".tif"
    )
    assert result.business_name_resolved is True
    assert result.policy_result.filename.endswith(".tif")


def test_recovery_never_recomputes_a_persisted_technical_name():
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        source = root / "synthetic.pdf"
        source.write_bytes(b"SYNTHETIC")
        jobs = MailboxDocumentJobStateService(root / "jobs")
        discovered = jobs.discover(
            message_key="a" * 64, attachment_key="b" * 64,
            document_key="c" * 64,
        ).state
        lease = jobs.acquire_processing_lease(discovered.job_key).state
        technical_name = "LTHHC_TECHNICAL_DOCUMENT_" + "d" * 64 + ".pdf"
        pending = jobs.transition(
            discovered.job_key,
            expected_stages={"processing"},
            stage="row_write_pending",
            lease_token=lease.lease_token,
            attachment_filename=technical_name,
            attachment_naming_status="technical_fallback",
        ).state
        recovery = MailboxDocumentSmartsheetRecoveryService(
            job_state_service=jobs,
            filename_assembly_service=ProductionFilenameAssemblyService(
                tables_provider=tables
            ),
        )
        work_item = MailboxDocumentWorkItem(
            pending.job_key, "a" * 64, "b" * 64, "c" * 64,
            source, pending.stage, document(),
        )
        stored, status, diagnostic = recovery._ensure_attachment_name(
            work_item, pending
        )
        assert status == "ready"
        assert stored.attachment_filename == technical_name
        assert stored.attachment_naming_status == "technical_fallback"
        assert diagnostic.filename_result == "technical_fallback"
        assert diagnostic.filename_failure_category == (
            "persisted_technical_fallback"
        )
        assert diagnostic.business_filename_attempted is False


def test_optional_service_line_child_failure_does_not_discard_supported_siblings():
    subject = document()
    line = subject.service_lines[0]
    line.status = None
    line.end_date = None
    line.confidence = 0.50
    line.candidate_evidence = {
        "service_code": "T0000", "modifier": "U1",
        "start_date": "2026-01-02", "end_date": None,
        "status": "Unsupported", "confidence": 0.95,
    }
    subject.validation_actions = [
        "Service line 1 status is not supported by its source evidence"
    ]
    result = ProductionFilenameAssemblyService(tables_provider=tables).resolve(
        document=subject, source_extension=".pdf"
    )
    assert result.business_name_resolved is True
    assert "SERVICE" in result.policy_result.filename
    assert result.policy_result.filename.endswith("_010226.pdf")


def test_2067_unknown_subtype_uses_business_name_with_ready_requirements():
    subject = document()
    subject.document_category = "2067"
    subject.document_subtype = "unknown"
    subject.subtype_support_status = "unknown"
    subject.field_evidence["posted_date"] = evidence("2026-04-05")
    service = ProductionFilenameAssemblyService(tables_provider=tables)
    result = service.resolve(document=subject, source_extension=".pdf")
    diagnostic = service.diagnose(document=subject, source_extension=".pdf")
    assert result.business_name_resolved is True
    assert "_2067_040526.pdf" in result.policy_result.filename
    assert "AUTH INIT" not in result.policy_result.filename
    assert diagnostic.form_component_status == "Ready"
    assert diagnostic.workflow_component_status == "Omitted"
    assert diagnostic.extension_component_status == "Ready"


def test_2067_without_posted_date_uses_one_supported_alternative_date():
    subject = document()
    subject.document_category = "2067"
    subject.document_subtype = "unknown"
    subject.subtype_support_status = "unknown"
    subject.service_lines[0].end_date = None
    result = ProductionFilenameAssemblyService(tables_provider=tables).resolve(
        document=subject, source_extension=".pdf"
    )
    assert result.business_name_resolved is True
    assert result.policy_result.filename.endswith("_010226.pdf")


def test_all_required_failures_are_counted_and_primary_category_is_stable():
    subject = document()
    subject.field_evidence["payer"] = evidence("UNMAPPED PLAN")
    subject.service_lines = []
    service = ProductionFilenameAssemblyService(tables_provider=tables)
    result = service.resolve(document=subject, source_extension=".doc")
    diagnostic = result.diagnostic
    assert result.business_filename_attempted is True
    assert result.status == "payer_reference_unresolved"
    assert result.required_component_failure_count == 3
    assert diagnostic.payer_lookup_status == "not_resolved"
    assert diagnostic.dates_ready is False
    assert diagnostic.extension_ready is False


def test_each_required_component_independently_forces_scoped_fallback():
    cases = []

    missing_person = document()
    missing_person.field_evidence.pop("person_first")
    cases.append((missing_person, ".pdf", "person_components_unresolved"))

    missing_payer = document()
    missing_payer.field_evidence.pop("payer")
    cases.append((missing_payer, ".pdf", "payer_evidence_unresolved"))

    missing_date = document()
    missing_date.service_lines = []
    cases.append((missing_date, ".pdf", "date_unresolved"))

    invalid_extension = document()
    cases.append((invalid_extension, ".doc", "source_extension_unsupported"))

    service = ProductionFilenameAssemblyService(tables_provider=tables)
    for subject, extension, expected in cases:
        result = service.resolve(
            document=subject, source_extension=extension
        )
        assert result.business_name_resolved is False
        assert result.status == expected
        assert result.required_component_failure_count == 1


def test_policy_is_invoked_even_when_required_component_is_unresolved():
    class CountingPolicy(FilenamePolicyService):
        def __init__(self):
            super().__init__()
            self.calls = 0

        def resolve(self, request):
            self.calls += 1
            return super().resolve(request)

    policy = CountingPolicy()
    subject = document()
    subject.field_evidence.pop("person_first")
    result = ProductionFilenameAssemblyService(
        tables_provider=tables,
        policy_service=policy,
    ).resolve(document=subject, source_extension=".pdf")
    assert policy.calls == 1
    assert result.business_filename_attempted is True
    assert result.status == "person_components_unresolved"


def test_safe_composition_failure_is_scoped_and_counted():
    class FailingCompositionPolicy(FilenamePolicyService):
        def resolve(self, request):
            return FilenamePolicyResult(
                False, None, True, "component_invalid"
            )

    result = ProductionFilenameAssemblyService(
        tables_provider=tables,
        policy_service=FailingCompositionPolicy(),
    ).resolve(document=document(), source_extension=".pdf")
    assert result.business_name_resolved is False
    assert result.status == "component_invalid"
    assert result.required_component_failure_count == 1


if __name__ == "__main__":
    tests = [value for name, value in list(globals().items()) if name.startswith("test_")]
    for test in tests:
        test()
    print(f"Passed: {len(tests)}")
    print("Failed: 0")
    print("Classification: synthetic deterministic")
    print("PHI handling: synthetic values only; filename values are not printed")
