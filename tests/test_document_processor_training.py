from dataclasses import fields
import inspect
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace

import yaml

import src.services.document_processor_training_codex_service as codex_module

from src.models.document_processor_business_context import BUSINESS_CONTEXT_VERSION

from src.services.document_processor_training_analysis_service import (
    LocalCorrectionAnalysisService,
    PhiSafeImplementationTaskService,
    serialize_phi_safe_task,
)
from src.services.document_processor_training_application_service import (
    DocumentProcessorTrainingApplicationService,
)
from src.services.smartsheet_feedback_case_storage_service import (
    CorrectionCase,
    ProtectedCorrectionCaseRepository,
    stable_digest,
)
from src.services.document_processor_training_codex_service import (
    BoundedCodexDispatcher,
    CodexDispatchResult,
)
from src.services.document_processor_training_contracts import (
    AI_CORRECTION,
    AI_CORRECTION_STATUS,
    AI_CORRECTION_TYPE,
    AI_PROPOSED_CORRECTION,
    AI_RESOLUTION_RESULT,
    APPROVE_AI_CORRECTION,
    APPROVE_AI_RESOLUTION,
    CORRECTION_STATUSES,
    CORRECTION_TYPES,
    HISTORICAL_ACCEPTANCE_IMPLEMENTATION_STATE,
    HISTORICAL_ACCEPTANCE_RESULT,
    REQUIRED_COLUMNS,
    WORKFLOW_OWNED_COLUMNS,
    CorrectionAnalysis,
    CorrectionComment,
    CorrectionRow,
    CorrectionSchemaResult,
    TrainingCycleSummary,
    normalize_checkbox,
)
from src.services.smartsheet_document_processor_training_service import (
    ALLOWED_COLUMN_TYPES,
    SmartsheetCorrectionReader,
    SmartsheetCorrectionSchemaService,
    SmartsheetCorrectionWriter,
)


ROOT = Path(__file__).resolve().parent.parent


def correction_analysis(**overrides):
    values = {
        "primary_correction_type": "Date",
        "related_correction_types": (),
        "affected_fields": ("End Date",),
        "behavior_code": "remain_blank_when_absent",
        "desired_behavior": "",
        "likely_layers": ("Business Rule",),
        "desired_behavior_sufficient": True,
        "technical_disposition": "Known",
        "feedback_relationship": "Initial",
        "observed_failure_type": "Date",
        "affected_document_category": "authorization",
        "desired_intake_subtype": "not_applicable",
        "required_filename_components": (),
        "excluded_filename_components": (),
    }
    values.update(overrides)
    return CorrectionAnalysis(**values)


def schema_result():
    ids = {title: index + 1 for index, title in enumerate(sorted(REQUIRED_COLUMNS))}
    return CorrectionSchemaResult(
        True,
        "ready",
        7,
        ids,
        {
            title: (
                "TEXT_NUMBER"
                if "TEXT_NUMBER" in ALLOWED_COLUMN_TYPES[title]
                else "CHECKBOX"
            )
            for title in ids
        },
        {title: "none" for title in ids},
        {},
    )


class SchemaClient:
    def __init__(self, columns):
        self.columns = columns

    def get_columns(self):
        return SimpleNamespace(data=self.columns)


def column(
    title, column_id, column_type, *, system=None, formula=None, options=None
):
    return SimpleNamespace(
        title=title,
        id=column_id,
        type=column_type,
        system_column_type=system,
        formula=formula,
        options=options,
    )


def valid_columns():
    return [
        column(
            title,
            index + 1,
            "TEXT_NUMBER" if "TEXT_NUMBER" in ALLOWED_COLUMN_TYPES[title] else "CHECKBOX",
        )
        for index, title in enumerate(sorted(REQUIRED_COLUMNS))
    ]


def test_exact_seven_column_contract_and_result_name():
    assert len(REQUIRED_COLUMNS) == 7
    assert "AI Resolution Result" in REQUIRED_COLUMNS
    assert "AI Correction Result" not in REQUIRED_COLUMNS
    assert len(CORRECTION_TYPES) == 17
    assert "Implementation Complete" not in CORRECTION_STATUSES


def test_schema_accepts_exact_types_and_rejects_missing_duplicate_formula_system():
    assert SmartsheetCorrectionSchemaService(client=SchemaClient(valid_columns())).read().success
    for columns in (
        valid_columns()[:-1],
        valid_columns() + [valid_columns()[0]],
        [*valid_columns()[:-1], column("AI Resolution Result", 7, "CHECKBOX")],
        [*valid_columns()[:-1], column("AI Resolution Result", 7, "TEXT_NUMBER", formula="x")],
        [*valid_columns()[:-1], column("AI Resolution Result", 7, "TEXT_NUMBER", system="CREATED_DATE")],
    ):
        assert not SmartsheetCorrectionSchemaService(client=SchemaClient(columns)).read().success


def test_schema_accepts_only_complete_controlled_picklists():
    columns = valid_columns()
    for index, value in enumerate(columns):
        if value.title == AI_CORRECTION_TYPE:
            columns[index] = column(
                value.title, value.id, "PICKLIST", options=list(CORRECTION_TYPES)
            )
        if value.title == AI_CORRECTION_STATUS:
            columns[index] = column(
                value.title, value.id, "PICKLIST", options=list(CORRECTION_STATUSES)
            )
    assert SmartsheetCorrectionSchemaService(client=SchemaClient(columns)).read().success
    bad = list(columns)
    status_index = next(
        index for index, value in enumerate(bad)
        if value.title == AI_CORRECTION_STATUS
    )
    bad[status_index] = column(
        AI_CORRECTION_STATUS,
        bad[status_index].id,
        "PICKLIST",
        options=list(CORRECTION_STATUSES[:-1]),
    )
    result = SmartsheetCorrectionSchemaService(client=SchemaClient(bad)).read()
    assert not result.success
    assert result.status == "schema_picklist_options_incompatible"


def test_checkbox_accepts_only_boolean_or_official_untouched_absence():
    assert normalize_checkbox(True) is True
    assert normalize_checkbox(False) is False
    assert normalize_checkbox(None) is None
    for invalid in (1, 0, "true", "false", [], {}):
        try:
            normalize_checkbox(invalid)
            raise AssertionError("invalid checkbox accepted")
        except ValueError:
            pass


class DiscussionApi:
    def __init__(self):
        self.calls = []

    def get_row_discussions(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        page = kwargs["page"]
        item = SimpleNamespace(
            id=page,
            comments=[SimpleNamespace(
                id=page,
                text="protected synthetic feedback",
                created_at=f"2026-01-0{page}",
                modified_at=f"2026-01-0{page}",
                created_by=SimpleNamespace(name="Synthetic Reviewer"),
            )],
        )
        return SimpleNamespace(data=[item], total_count=2)


def test_discussion_pagination_requests_comments_and_never_attachments():
    from src.clients.smartsheet_client import SmartsheetClient

    client = object.__new__(SmartsheetClient)
    client.sheet_id = "protected"
    api = DiscussionApi()
    client.client = SimpleNamespace(Discussions=api)
    result = client.get_row_discussions(row_id=9)
    assert len(result) == 2
    assert [call[1]["page"] for call in api.calls] == [1, 2]
    assert all(call[1]["include"] == ["comments"] for call in api.calls)
    assert "attachments" not in repr(api.calls).lower()


class SheetPageApi:
    def __init__(self, *, duplicate=False):
        self.calls = []
        self.duplicate = duplicate

    def get_sheet(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        page = kwargs["page"]
        row_id = 1 if page == 1 or self.duplicate else 2
        return SimpleNamespace(
            version=7, total_row_count=2,
            rows=[SimpleNamespace(id=row_id, cells=[])],
        )


def test_selected_row_pagination_is_stable_and_rejects_duplicates():
    from src.clients.smartsheet_client import SmartsheetClient

    client = object.__new__(SmartsheetClient)
    client.sheet_id = "protected"
    pages = SheetPageApi()
    client.client = SimpleNamespace(Sheets=pages)
    version, rows = client.get_selected_rows(column_ids=[1, 2, 3])
    assert version == 7 and [row.id for row in rows] == [1, 2]
    assert all(call[1]["column_ids"] == [1, 2, 3] for call in pages.calls)
    client.client = SimpleNamespace(Sheets=SheetPageApi(duplicate=True))
    try:
        client.get_selected_rows(column_ids=[1, 2, 3])
        raise AssertionError("duplicate selected row was accepted")
    except RuntimeError:
        pass


class SelectedRowsClient:
    def __init__(self):
        self.calls = []
        self.row = SimpleNamespace(id=31, cells=[])

    def get_selected_rows(self, *, column_ids):
        self.calls.append(("rows", tuple(column_ids)))
        return 1, (self.row,)

    def get_selected_row(self, *, row_id, column_ids):
        self.calls.append(("row", tuple(column_ids)))
        return 1, self.row


def test_unflagged_discovery_reads_no_protected_context_columns():
    base = schema_result()
    schema = CorrectionSchemaResult(
        base.success, base.status, base.column_count, base.column_ids,
        base.column_types, base.system_column_types, {"Patient Name": 9001},
    )
    client = SelectedRowsClient()
    reader = SmartsheetCorrectionReader(client=client)
    reader.read_rows(schema=schema)
    assert client.calls[0] == ("rows", tuple(schema.column_ids.values()))
    assert 9001 not in client.calls[0][1]
    reader.read_context_row(row_id=31, schema=schema)
    assert 9001 in client.calls[1][1]


class WriterReader:
    def __init__(self, row):
        self.row = row

    def read_row(self, **kwargs):
        return self.row


class WriterClient:
    def __init__(self, reader, schema):
        self.reader = reader
        self.schema = schema
        self.calls = []

    def update_row(self, row_id, updates):
        self.calls.append((row_id, updates))
        values = dict(self.reader.row.values)
        reverse = {column_id: title for title, column_id in self.schema.column_ids.items()}
        values.update({reverse[column_id]: value for column_id, value in updates.items()})
        self.reader.row = CorrectionRow(row_id, values, 2)


def test_writer_is_hard_limited_to_four_fields_and_reconciles():
    schema = schema_result()
    row = CorrectionRow(10, {title: None for title in REQUIRED_COLUMNS}, 1)
    reader = WriterReader(row)
    client = WriterClient(reader, schema)
    writer = SmartsheetCorrectionWriter(client=client, reader=reader)
    blocked = writer.write(
        row_id=10, updates={APPROVE_AI_CORRECTION: True}, schema=schema
    )
    assert not blocked.success and client.calls == []
    blocked_none = writer.write(
        row_id=10, updates={AI_CORRECTION_STATUS: None}, schema=schema
    )
    assert not blocked_none.success
    result = writer.write(
        row_id=10,
        updates={AI_CORRECTION_STATUS: "Analysis Ready"},
        schema=schema,
    )
    assert result.success and result.outcome_proven and len(client.calls) == 1
    assert set(WORKFLOW_OWNED_COLUMNS) == {
        AI_PROPOSED_CORRECTION, AI_CORRECTION_TYPE,
        AI_CORRECTION_STATUS, AI_RESOLUTION_RESULT,
    }


class UncertainWriterClient(WriterClient):
    def __init__(self, reader, schema, *, applies_before_failure):
        super().__init__(reader, schema)
        self.applies_before_failure = applies_before_failure

    def update_row(self, row_id, updates):
        self.calls.append((row_id, updates))
        if self.applies_before_failure:
            values = dict(self.reader.row.values)
            reverse = {
                column_id: title
                for title, column_id in self.schema.column_ids.items()
            }
            values.update(
                {reverse[column_id]: value for column_id, value in updates.items()}
            )
            self.reader.row = CorrectionRow(row_id, values, 2)
        raise RuntimeError("protected API detail")


def test_writer_reconciles_uncertain_update_and_never_blindly_repeats():
    schema = schema_result()
    for applies, expected_success, expected_status in (
        (True, True, "workflow_write_reconciled"),
        (False, False, "workflow_write_rejected"),
    ):
        row = CorrectionRow(10, {title: None for title in REQUIRED_COLUMNS}, 1)
        reader = WriterReader(row)
        client = UncertainWriterClient(
            reader, schema, applies_before_failure=applies
        )
        result = SmartsheetCorrectionWriter(client=client, reader=reader).write(
            row_id=10,
            updates={AI_CORRECTION_STATUS: "Analysis Ready"},
            schema=schema,
        )
        assert result.success is expected_success
        assert result.status == expected_status
        assert len(client.calls) == 1


def test_writer_uses_exact_preconditions_and_skips_reconciled_values():
    schema = schema_result()
    values = {title: None for title in REQUIRED_COLUMNS}
    values[AI_CORRECTION_STATUS] = "Analysis Ready"
    row = CorrectionRow(10, values, 1)
    reader = WriterReader(row)
    client = WriterClient(reader, schema)
    writer = SmartsheetCorrectionWriter(client=client, reader=reader)
    already = writer.write(
        row_id=10,
        updates={AI_CORRECTION_STATUS: "Analysis Ready"},
        schema=schema,
        expected_proposal_hash_values={AI_CORRECTION_STATUS: "Analysis Ready"},
    )
    assert already.success and not already.request_attempted and client.calls == []
    stale = writer.write(
        row_id=10,
        updates={AI_CORRECTION_STATUS: "Resolved"},
        schema=schema,
        expected_proposal_hash_values={AI_CORRECTION_STATUS: "Retest Required"},
    )
    assert not stale.success and stale.status == "workflow_write_stale"
    assert client.calls == []


def test_protected_case_repository_is_encrypted_and_restart_idempotent():
    with TemporaryDirectory() as directory:
        repository = ProtectedCorrectionCaseRepository(
            directory,
            protect=lambda value: value[::-1],
            unprotect=lambda value: value[::-1],
        )
        first = repository.load_or_create(source_scope="synthetic", row_id=42)
        first.comments = [{"text": "protected synthetic feedback"}]
        repository.save(first)
        second = repository.load_or_create(source_scope="synthetic", row_id=42)
        assert second.case_id == first.case_id
        assert second.comments == first.comments
        case_bytes = next(Path(directory).glob("*.case")).read_bytes()
        assert b"protected synthetic feedback" not in case_bytes
        assert "42" not in repr(second)


def test_protected_case_v1_migrates_without_identity_or_checkpoint_loss():
    with TemporaryDirectory() as directory:
        repository = ProtectedCorrectionCaseRepository(
            directory,
            protect=lambda value: value[::-1],
            unprotect=lambda value: value[::-1],
        )
        current = repository.load_or_create(source_scope="synthetic", row_id=43)
        current.comment_checkpoint_digest = "d" * 64
        repository.save(current)
        path = next(Path(directory).glob("*.case"))
        payload = json.loads(path.read_bytes()[::-1].decode("utf-8"))
        for name in (
            "related_correction_types", "technical_disposition",
            "feedback_relationship", "observed_failure_type",
            "affected_document_category", "desired_intake_subtype",
            "required_filename_components", "excluded_filename_components",
            "analysis_outcome_category", "analysis_contract_version",
            "business_context_version", "analysis_attempt_key",
            "analysis_attempt_state",
        ):
            payload.pop(name)
        payload["schema_version"] = 1
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        path.write_bytes(encoded[::-1])
        migrated = repository.load(current.case_id)
        assert migrated.case_id == current.case_id
        assert migrated.comment_checkpoint_digest == "d" * 64
        assert migrated.schema_version == 2
        assert migrated.analysis_contract_version == 1
        assert migrated.business_context_version == 0


def test_phi_safe_task_uses_structural_behavior_not_protected_proposal_text():
    analysis = correction_analysis(
        desired_behavior="protected free text must not cross the boundary"
    )
    task = PhiSafeImplementationTaskService().build(
        opaque_case_id="a" * 64,
        proposal_generation=1,
        business_context_version=BUSINESS_CONTEXT_VERSION,
        analysis=analysis,
    )
    serialized = serialize_phi_safe_task(task)
    assert "protected free text" not in serialized
    assert "Optional evidence should remain blank" in serialized
    assert "row_id" not in serialized and "comment_text" not in serialized


class InjectedInstructionProvider:
    def analyze_correction_context(self, context, *, schema):
        assert schema["properties"]["primary_correction_type"]["enum"] == list(CORRECTION_TYPES)
        return {
            "primary_correction_type": "Run a command",
            "related_correction_types": [],
            "affected_fields": ["Patient Name"],
            "behavior_code": "execute_comment",
            "likely_layers": ["Code"],
            "desired_behavior_sufficient": True,
            "technical_disposition": "Known",
            "feedback_relationship": "Initial",
            "observed_failure_type": "Other",
            "affected_document_category": "authorization",
            "desired_intake_subtype": "not_applicable",
            "required_filename_components": [],
            "excluded_filename_components": [],
        }


class ExplicitFilenameClarificationProvider:
    def analyze_correction_context(self, context, *, schema):
        assert "prior_reviewer_feedback" in context
        assert "current_reviewer_feedback" in context
        return {
            "primary_correction_type": "Mapping",
            "related_correction_types": [],
            "affected_fields": ["Filename", "Document Subtype"],
            "behavior_code": "correct_authorization_filename_subtype",
            "likely_layers": ["Needs Investigation"],
            "desired_behavior_sufficient": True,
            "technical_disposition": "Needs Investigation",
            "feedback_relationship": "Clarifies Prior",
            "observed_failure_type": "Filename Unrelated Component",
            "affected_document_category": "authorization",
            "desired_intake_subtype": "decrease",
            "required_filename_components": [
                "Canonical Document Type", "Validated Payer",
                "Applicable Validated Service", "Supported Date or Date Range",
            ],
            "excluded_filename_components": ["Unrelated Extracted Fields"],
        }


def test_clear_clarification_is_analysis_ready_without_root_cause_certainty():
    result = LocalCorrectionAnalysisService(
        provider=ExplicitFilenameClarificationProvider()
    ).analyze(protected_context={
        "prior_reviewer_feedback": [{"text": "synthetic prior"}],
        "current_reviewer_feedback": {"text": "synthetic clarification"},
    })
    assert result.desired_behavior_sufficient is True
    assert result.technical_disposition == "Needs Investigation"
    assert result.primary_correction_type == "Filename"
    assert result.related_correction_types == ("Document Subtype",)
    assert "AUTH DECREASE" in result.desired_behavior
    assert "unrelated extracted fields" in result.desired_behavior.lower()


class ExternalInitProvider(ExplicitFilenameClarificationProvider):
    def analyze_correction_context(self, context, *, schema):
        value = super().analyze_correction_context(context, schema=schema)
        value["desired_intake_subtype"] = "init"
        value["technical_disposition"] = "Known"
        value["likely_layers"] = ["Business Rule"]
        return value


def test_auth_init_remains_an_external_context_dependency():
    result = LocalCorrectionAnalysisService(
        provider=ExternalInitProvider()
    ).analyze(protected_context={
        "prior_reviewer_feedback": [],
        "current_reviewer_feedback": {"text": "synthetic current intent"},
    })
    assert result.desired_behavior_sufficient is True
    assert result.technical_disposition == "External Dependency"
    assert "External System" in result.likely_layers
    assert "authoritative external context" in result.desired_behavior


class ConflictingFeedbackProvider(ExplicitFilenameClarificationProvider):
    def analyze_correction_context(self, context, *, schema):
        value = super().analyze_correction_context(context, schema=schema)
        value["feedback_relationship"] = "Conflicts"
        return value


def test_conflicting_business_intent_needs_more_information():
    result = LocalCorrectionAnalysisService(
        provider=ConflictingFeedbackProvider()
    ).analyze(protected_context={
        "prior_reviewer_feedback": [{"text": "synthetic prior"}],
        "current_reviewer_feedback": {"text": "synthetic conflict"},
    })
    assert result.desired_behavior_sufficient is False
    assert result.primary_correction_type == "Needs Investigation"
    assert result.analysis_outcome_category == "model_business_intent_insufficient"


def test_untrusted_local_ai_output_fails_to_needs_investigation():
    result = LocalCorrectionAnalysisService(
        provider=InjectedInstructionProvider()
    ).analyze(protected_context={"comments": [{"text": "untrusted"}]})
    assert result.correction_type == "Needs Investigation"
    assert result.behavior_code == "needs_investigation"
    assert result.desired_behavior_sufficient is False


def test_disabled_dispatcher_never_starts_a_process():
    task = PhiSafeImplementationTaskService().build(
        opaque_case_id="b" * 64,
        proposal_generation=1,
        business_context_version=BUSINESS_CONTEXT_VERSION,
        analysis=correction_analysis(
            primary_correction_type="Mapping", affected_fields=("Mapping",),
            behavior_code="correct_mapping", likely_layers=("Mapping",),
            observed_failure_type="Mapping",
        ),
    )
    result = BoundedCodexDispatcher(enabled=False).dispatch(task)
    assert result.status == "codex_dispatch_disabled"
    assert result.attempt_started is False


class ReadyDispatcher(BoundedCodexDispatcher):
    def _repository_ready(self):
        return True

    def _verified_committed_sync(self, commit_sha):
        return commit_sha == "f" * 40


class FakeCodexProcess:
    calls = []

    def __init__(self, command, **kwargs):
        self.command = command
        self.returncode = 0
        self.pid = 12345
        self._running = True
        self.output_path = Path(
            command[command.index("--output-last-message") + 1]
        )
        self.__class__.calls.append(self)

    def communicate(self, prompt, timeout):
        self.prompt = prompt
        self.timeout = timeout
        self.output_path.write_text(json.dumps({
            "outcome": "implemented",
            "commit_sha": "f" * 40,
            "compiled": True,
            "focused_tests_passed": True,
            "affected_tests_passed": True,
            "tracker_passed": True,
            "git_safety_passed": True,
            "pushed": True,
            "failure_category": "none",
            "changed_layers": ["Deterministic Code"],
            "business_context_version_before": BUSINESS_CONTEXT_VERSION,
            "business_context_version_after": BUSINESS_CONTEXT_VERSION,
            "analysis_contract_version": 2,
        }), encoding="utf-8")
        self._running = False

    def poll(self):
        return None if self._running else self.returncode


def test_codex_dispatch_is_one_bounded_ephemeral_sanitized_process():
    analysis = correction_analysis(desired_behavior="protected proposal text")
    task = PhiSafeImplementationTaskService().build(
        opaque_case_id="9" * 64, proposal_generation=1,
        business_context_version=BUSINESS_CONTEXT_VERSION, analysis=analysis
    )
    original_which = codex_module.shutil.which
    original_popen = codex_module.subprocess.Popen
    FakeCodexProcess.calls = []
    started = []
    try:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            schema = root / "src/contracts/dp_training_codex_result.schema.json"
            schema.parent.mkdir(parents=True)
            schema.write_text("{}", encoding="ascii")
            codex_module.shutil.which = lambda name: "synthetic-codex.cmd"
            codex_module.subprocess.Popen = FakeCodexProcess
            result = ReadyDispatcher(
                repository_root=root, enabled=True, timeout_seconds=15
            ).dispatch(task, on_started=lambda: started.append(True))
            assert result.success and result.commit_sha == "f" * 40
            assert started == [True] and len(FakeCodexProcess.calls) == 1
            process = FakeCodexProcess.calls[0]
            assert "--ephemeral" in process.command
            assert "--approve-for-me" in process.command
            assert "resume" not in process.command
            assert process.timeout == 15
            assert "protected proposal text" not in process.prompt
            assert "Optional evidence should remain blank" in process.prompt
            assert not (root / ReadyDispatcher.LOCK_PATH).exists()
    finally:
        codex_module.shutil.which = original_which
        codex_module.subprocess.Popen = original_popen


def test_codex_context_and_committed_sync_gates_are_independent():
    analysis = correction_analysis()
    task = PhiSafeImplementationTaskService().build(
        opaque_case_id="7" * 64,
        proposal_generation=1,
        business_context_version=BUSINESS_CONTEXT_VERSION,
        analysis=analysis,
    )
    parsed = {
        "changed_layers": ["Deterministic Code"],
        "business_context_version_before": BUSINESS_CONTEXT_VERSION,
        "business_context_version_after": BUSINESS_CONTEXT_VERSION,
        "analysis_contract_version": 2,
    }
    assert ReadyDispatcher._valid_context_result(parsed, task)
    parsed["changed_layers"] = ["Business Context"]
    assert not ReadyDispatcher._valid_context_result(parsed, task)
    parsed["business_context_version_after"] = BUSINESS_CONTEXT_VERSION + 1
    assert ReadyDispatcher._valid_context_result(parsed, task)

    dispatcher = BoundedCodexDispatcher()
    calls = []
    expected_sha = "a" * 40
    responses = {
        ("status", "--porcelain"): "",
        ("rev-parse", "HEAD"): expected_sha,
        ("rev-parse", "origin/main"): expected_sha,
        ("rev-list", "--left-right", "--count", "HEAD...origin/main"): "0 0",
    }
    dispatcher._git = lambda *arguments: (
        calls.append(arguments) or responses[arguments]
    )
    assert dispatcher._verified_committed_sync(expected_sha)
    assert len(calls) == 4
    assert not dispatcher._verified_committed_sync("not-a-sha")


class WaitingDispatcher(BoundedCodexDispatcher):
    def _repository_ready(self):
        return False


def test_repository_preflight_blocks_before_codex_process_or_credit():
    task = PhiSafeImplementationTaskService().build(
        opaque_case_id="8" * 64,
        proposal_generation=1,
        business_context_version=BUSINESS_CONTEXT_VERSION,
        analysis=correction_analysis(
            primary_correction_type="Mapping", affected_fields=("Mapping",),
            behavior_code="correct_mapping", likely_layers=("Mapping",),
            observed_failure_type="Mapping",
        ),
    )
    result = WaitingDispatcher(enabled=True).dispatch(task)
    assert result.status == "codex_repository_waiting"
    assert not result.attempt_started


def test_codex_dispatcher_has_no_retry_resume_or_destructive_git_cleanup():
    source = inspect.getsource(BoundedCodexDispatcher)
    for prohibited in (
        "git reset", "git checkout", "git clean", "exec resume", "while True"
    ):
        assert prohibited not in source
    assert source.count("subprocess.Popen(") == 1


class MemoryRepository:
    def __init__(self):
        self.case = None

    def load_or_create(self, *, source_scope, row_id):
        if self.case is None:
            self.case = CorrectionCase("c" * 64, row_id, source_scope, "now", "now")
        return self.case

    def save(self, correction_case, **kwargs):
        self.case = correction_case

    def list_cases(self):
        return () if self.case is None else (self.case,)


class FlowReader:
    def __init__(self):
        self.values = {title: None for title in REQUIRED_COLUMNS}
        self.values[AI_CORRECTION] = True
        self.comments = (CorrectionComment(1, 1, "t", "t", "reviewer", "protected"),)

    def read_rows(self, **kwargs):
        return (CorrectionRow(20, dict(self.values), 1),)

    def read_row(self, **kwargs):
        return CorrectionRow(20, dict(self.values), 1)

    def read_context_row(self, **kwargs):
        return CorrectionRow(20, dict(self.values), 1)

    def read_comments(self, **kwargs):
        return self.comments


class FlowWriter:
    def __init__(self, reader):
        self.reader = reader
        self.written_titles = []

    def write(self, *, updates, **kwargs):
        assert set(updates) <= WORKFLOW_OWNED_COLUMNS
        self.written_titles.extend(updates)
        self.reader.values.update(updates)
        return SimpleNamespace(success=True, status="workflow_write_reconciled")


class ReconciledFlowWriter:
    def __init__(self, reader):
        self.reader = reader
        self.external_calls = 0

    def write(self, *, updates, expected_proposal_hash_values=None, **kwargs):
        assert set(updates) <= WORKFLOW_OWNED_COLUMNS
        expected = expected_proposal_hash_values or {}
        assert all(self.reader.values.get(title) == value for title, value in expected.items())
        if all(self.reader.values.get(title) == value for title, value in updates.items()):
            return SimpleNamespace(
                success=True,
                status="workflow_write_already_reconciled",
                request_attempted=False,
            )
        self.external_calls += 1
        self.reader.values.update(updates)
        return SimpleNamespace(
            success=True,
            status="workflow_write_reconciled",
            request_attempted=True,
        )


class FlowAnalyzer:
    def analyze(self, **kwargs):
        return correction_analysis()


class CapturingFlowAnalyzer(FlowAnalyzer):
    def __init__(self):
        self.calls = []

    def analyze(self, **kwargs):
        self.calls.append(kwargs)
        return super().analyze(**kwargs)


def test_analysis_envelope_separates_prior_and_current_feedback():
    reader = FlowReader()
    reader.comments = (
        CorrectionComment(1, 1, "a", "a", "reviewer", "synthetic prior"),
        CorrectionComment(2, 2, "b", "b", "reviewer", "synthetic current"),
    )
    analyzer = CapturingFlowAnalyzer()
    service = DocumentProcessorTrainingApplicationService(
        schema_service=SimpleNamespace(read=schema_result),
        reader=reader,
        repository=MemoryRepository(),
        analyzer=analyzer,
        writer=ForbiddenWriter(),
        task_service=PhiSafeImplementationTaskService(),
        dispatcher=ForbiddenDispatcher(),
        mode="read_only",
    )
    service.run_cycle()
    context = analyzer.calls[0]["protected_context"]
    assert len(context["prior_reviewer_feedback"]) == 1
    assert context["current_reviewer_feedback"]["comment_id"] == 2
    assert "comments" not in context


def test_legacy_analysis_basis_reanalyzes_once_without_dispatch():
    reader = FlowReader()
    repository = MemoryRepository()
    initial = DocumentProcessorTrainingApplicationService(
        schema_service=SimpleNamespace(read=schema_result),
        reader=reader,
        repository=repository,
        analyzer=FlowAnalyzer(),
        writer=ForbiddenWriter(),
        task_service=PhiSafeImplementationTaskService(),
        dispatcher=ForbiddenDispatcher(),
        mode="read_only",
    )
    initial.run_cycle()
    correction_case = repository.case
    identity = correction_case.case_id
    correction_case.proposal_generation = 2
    correction_case.status = "Needs More Information"
    correction_case.analysis_contract_version = 1
    correction_case.business_context_version = 0
    correction_case.analysis_attempt_key = ""
    correction_case.analysis_attempt_state = "none"
    correction_case.correction_approval_baseline_seen = True
    correction_case.correction_approval_previous = False
    correction_case.proposal_hash = stable_digest({
        "input": correction_case.input_digest,
        "generation": 2,
        "type": correction_case.correction_type,
        "proposal": correction_case.proposal_text,
    })
    reader.values[APPROVE_AI_CORRECTION] = True
    analyzer = CapturingFlowAnalyzer()
    writer = ReconciledFlowWriter(reader)
    upgraded = DocumentProcessorTrainingApplicationService(
        schema_service=SimpleNamespace(read=schema_result),
        reader=reader,
        repository=repository,
        analyzer=analyzer,
        writer=writer,
        task_service=PhiSafeImplementationTaskService(),
        dispatcher=ForbiddenDispatcher(),
        mode="proposal_write",
    )
    upgraded.run_cycle()
    assert correction_case.case_id == identity
    assert correction_case.proposal_generation == 3
    assert correction_case.analysis_contract_version == 2
    assert correction_case.business_context_version == BUSINESS_CONTEXT_VERSION
    assert correction_case.correction_approval_baseline_seen is False
    assert correction_case.implementation_attempt_count == 0
    assert correction_case.implementation_job_id == ""
    assert len(analyzer.calls) == 1 and writer.external_calls == 1
    upgraded.run_cycle()
    assert correction_case.proposal_generation == 3
    assert len(analyzer.calls) == 1 and writer.external_calls == 1


class FlowDispatcher:
    def dispatch(self, task, *, on_started):
        on_started()
        return CodexDispatchResult(True, "codex_implemented", True, True, True, "d" * 40)


def test_current_proposal_and_result_require_separate_human_edges():
    reader = FlowReader()
    repository = MemoryRepository()
    service = DocumentProcessorTrainingApplicationService(
        schema_service=SimpleNamespace(read=schema_result),
        reader=reader,
        repository=repository,
        analyzer=FlowAnalyzer(),
        writer=FlowWriter(reader),
        task_service=PhiSafeImplementationTaskService(),
        dispatcher=FlowDispatcher(),
        mode="approval_dispatch",
    )
    first = service.run_cycle()
    assert repository.case.status == "Analysis Ready"
    assert repository.case.correction_approval_baseline_seen
    assert first.analysis_ready_count == 1

    reader.values[APPROVE_AI_CORRECTION] = True
    service.run_cycle()
    assert repository.case.status == "Retest Required"
    assert repository.case.implementation_attempt_count == 1
    assert repository.case.resolution_approval_baseline_seen

    reader.values[APPROVE_AI_RESOLUTION] = True
    service.run_cycle()
    assert repository.case.status == "Resolved"
    assert repository.case.implementation_attempt_count == 1
    assert reader.values[APPROVE_AI_CORRECTION] is True
    assert reader.values[APPROVE_AI_RESOLUTION] is True


def build_flow_service(*, reader=None, mode="approval_dispatch", dispatcher=None):
    reader = reader or FlowReader()
    repository = MemoryRepository()
    service = DocumentProcessorTrainingApplicationService(
        schema_service=SimpleNamespace(read=schema_result),
        reader=reader,
        repository=repository,
        analyzer=FlowAnalyzer(),
        writer=FlowWriter(reader),
        task_service=PhiSafeImplementationTaskService(),
        dispatcher=dispatcher or FlowDispatcher(),
        mode=mode,
    )
    return service, reader, repository


def test_stale_true_requires_human_uncheck_then_recheck():
    reader = FlowReader()
    reader.values[APPROVE_AI_CORRECTION] = True
    service, _, repository = build_flow_service(reader=reader)
    service.run_cycle()
    service.run_cycle()
    assert repository.case.status == "Analysis Ready"
    assert repository.case.implementation_attempt_count == 0
    reader.values[APPROVE_AI_CORRECTION] = False
    service.run_cycle()
    reader.values[APPROVE_AI_CORRECTION] = True
    service.run_cycle()
    assert repository.case.status == "Retest Required"
    assert repository.case.implementation_attempt_count == 1


def test_stale_resolution_true_requires_human_uncheck_then_recheck():
    reader = FlowReader()
    reader.values[APPROVE_AI_RESOLUTION] = True
    service, _, repository = build_flow_service(reader=reader)
    service.run_cycle()
    reader.values[APPROVE_AI_CORRECTION] = True
    service.run_cycle()
    service.run_cycle()
    assert repository.case.status == "Retest Required"
    reader.values[APPROVE_AI_RESOLUTION] = False
    service.run_cycle()
    reader.values[APPROVE_AI_RESOLUTION] = True
    service.run_cycle()
    assert repository.case.status == "Resolved"


def test_new_comment_reopens_same_case_and_requires_new_approval_edge():
    service, reader, repository = build_flow_service()
    service.run_cycle()
    identity = repository.case.case_id
    reader.values[APPROVE_AI_CORRECTION] = True
    service.run_cycle()
    assert repository.case.status == "Retest Required"
    reader.comments = reader.comments + (
        CorrectionComment(1, 2, "u", "u", "reviewer", "new protected feedback"),
    )
    service.run_cycle()
    assert repository.case.case_id == identity
    assert repository.case.status == "Analysis Ready"
    assert repository.case.implementation_attempt_count == 1
    assert "reopened" in reader.values[AI_RESOLUTION_RESULT].lower()
    reader.values[APPROVE_AI_CORRECTION] = False
    service.run_cycle()
    reader.values[APPROVE_AI_CORRECTION] = True
    service.run_cycle()
    assert repository.case.implementation_attempt_count == 2


class ForbiddenReader:
    def read_rows(self, **kwargs):
        raise AssertionError("row values were read")


class WithdrawnBeforeContextReader(FlowReader):
    def read_context_row(self, **kwargs):
        values = dict(self.values)
        values[AI_CORRECTION] = False
        return CorrectionRow(20, values, 2)

    def read_comments(self, **kwargs):
        raise AssertionError("comments were read after the flag was withdrawn")


def test_schema_only_mode_stops_before_row_or_comment_access():
    service = DocumentProcessorTrainingApplicationService(
        schema_service=SimpleNamespace(read=schema_result),
        reader=ForbiddenReader(),
        repository=MemoryRepository(),
        analyzer=FlowAnalyzer(),
        writer=SimpleNamespace(),
        task_service=PhiSafeImplementationTaskService(),
        dispatcher=BoundedCodexDispatcher(enabled=False),
        mode="schema_only",
    )
    result = service.run_cycle()
    assert result.polling_result == "schema_ready"
    assert result.effective_mode == "schema_only"


def test_invalid_direct_mode_is_rejected_instead_of_downgraded():
    try:
        DocumentProcessorTrainingApplicationService(
            schema_service=SimpleNamespace(read=schema_result),
            reader=ForbiddenReader(),
            repository=MemoryRepository(),
            analyzer=FlowAnalyzer(),
            writer=SimpleNamespace(),
            task_service=PhiSafeImplementationTaskService(),
            dispatcher=BoundedCodexDispatcher(enabled=False),
            mode="invalid",
        )
    except ValueError as error:
        assert str(error) == "training_mode_invalid"
    else:
        raise AssertionError("Invalid mode silently downgraded")


def test_flag_is_reverified_before_comment_or_context_processing():
    reader = WithdrawnBeforeContextReader()
    service, _, repository = build_flow_service(reader=reader, mode="read_only")
    result = service.run_cycle()
    assert result.flagged_case_count == 1
    assert repository.case is None


class ForbiddenWriter:
    def write(self, **kwargs):
        raise AssertionError("Smartsheet write was attempted")


class ForbiddenDispatcher:
    def dispatch(self, *args, **kwargs):
        raise AssertionError("Codex dispatch was attempted")


def test_read_only_mode_analyzes_without_smartsheet_write_or_codex():
    reader = FlowReader()
    repository = MemoryRepository()
    service = DocumentProcessorTrainingApplicationService(
        schema_service=SimpleNamespace(read=schema_result),
        reader=reader,
        repository=repository,
        analyzer=FlowAnalyzer(),
        writer=ForbiddenWriter(),
        task_service=PhiSafeImplementationTaskService(),
        dispatcher=ForbiddenDispatcher(),
        mode="read_only",
    )
    result = service.run_cycle()
    assert repository.case.status == "Analysis Ready"
    assert result.analysis_ready_count == 1
    assert reader.values[AI_PROPOSED_CORRECTION] is None


def test_proposal_write_publishes_existing_read_only_generation_once():
    reader = FlowReader()
    repository = MemoryRepository()
    read_only = DocumentProcessorTrainingApplicationService(
        schema_service=SimpleNamespace(read=schema_result),
        reader=reader,
        repository=repository,
        analyzer=FlowAnalyzer(),
        writer=ForbiddenWriter(),
        task_service=PhiSafeImplementationTaskService(),
        dispatcher=ForbiddenDispatcher(),
        mode="read_only",
    )
    read_only.run_cycle()
    assert repository.case.proposal_generation == 1
    repository.case.implementation_state = HISTORICAL_ACCEPTANCE_IMPLEMENTATION_STATE
    repository.case.resolution_result = HISTORICAL_ACCEPTANCE_RESULT
    writer = ReconciledFlowWriter(reader)
    proposal_write = DocumentProcessorTrainingApplicationService(
        schema_service=SimpleNamespace(read=schema_result),
        reader=reader,
        repository=repository,
        analyzer=ForbiddenAnalyzer(),
        writer=writer,
        task_service=PhiSafeImplementationTaskService(),
        dispatcher=ForbiddenDispatcher(),
        mode="proposal_write",
    )
    human_before = {
        title: reader.values[title]
        for title in (AI_CORRECTION, APPROVE_AI_CORRECTION, APPROVE_AI_RESOLUTION)
    }
    proposal_write.run_cycle()
    assert repository.case.proposal_generation == 1
    assert writer.external_calls == 1
    assert reader.values[AI_PROPOSED_CORRECTION] == repository.case.proposal_text
    assert reader.values[AI_CORRECTION_TYPE] == repository.case.correction_type
    assert reader.values[AI_CORRECTION_STATUS] == repository.case.status
    assert reader.values[AI_RESOLUTION_RESULT] == HISTORICAL_ACCEPTANCE_RESULT
    assert human_before == {title: reader.values[title] for title in human_before}
    proposal_write.run_cycle()
    assert repository.case.proposal_generation == 1
    assert writer.external_calls == 1


def test_proposal_write_never_authorizes_or_dispatches_an_approval_edge():
    service, reader, repository = build_flow_service(
        mode="proposal_write", dispatcher=ForbiddenDispatcher()
    )
    service.run_cycle()
    reader.values[APPROVE_AI_CORRECTION] = True
    service.run_cycle()
    assert repository.case.status == "Analysis Ready"
    assert repository.case.implementation_state == "none"
    assert repository.case.implementation_job_id == ""
    assert repository.case.implementation_attempt_count == 0
    assert repository.case.correction_approval_consumed_generation == 0
    assert reader.values[APPROVE_AI_CORRECTION] is True


def test_historical_acceptance_block_survives_approval_dispatch_mode():
    service, reader, repository = build_flow_service(
        mode="proposal_write", dispatcher=ForbiddenDispatcher()
    )
    service.run_cycle()
    repository.case.implementation_state = HISTORICAL_ACCEPTANCE_IMPLEMENTATION_STATE
    repository.case.resolution_result = HISTORICAL_ACCEPTANCE_RESULT
    service.mode = "approval_dispatch"
    reader.values[APPROVE_AI_CORRECTION] = True
    service.run_cycle()
    assert repository.case.status == "Analysis Ready"
    assert repository.case.implementation_state == HISTORICAL_ACCEPTANCE_IMPLEMENTATION_STATE
    assert repository.case.implementation_job_id == ""
    assert repository.case.implementation_attempt_count == 0
    assert repository.case.correction_approval_consumed_generation == 0


class ForbiddenAnalyzer:
    def analyze(self, **kwargs):
        raise AssertionError("analysis should not run without a comment")


def test_comment_free_flagged_case_needs_more_information():
    reader = FlowReader()
    reader.comments = ()
    repository = MemoryRepository()
    service = DocumentProcessorTrainingApplicationService(
        schema_service=SimpleNamespace(read=schema_result),
        reader=reader,
        repository=repository,
        analyzer=ForbiddenAnalyzer(),
        writer=FlowWriter(reader),
        task_service=PhiSafeImplementationTaskService(),
        dispatcher=BoundedCodexDispatcher(enabled=False),
        mode="proposal_write",
    )
    service.run_cycle()
    assert repository.case.status == "Needs More Information"
    assert reader.values[AI_CORRECTION_STATUS] == "Needs More Information"


def test_human_withdrawal_rejects_only_before_implementation():
    service, reader, repository = build_flow_service(mode="proposal_write")
    service.run_cycle()
    reader.values[AI_CORRECTION] = False
    service.run_cycle()
    assert repository.case.status == "Rejected"
    assert reader.values[AI_CORRECTION_STATUS] == "Rejected"


def test_pending_workflow_write_is_reconciled_before_future_actions():
    service, reader, repository = build_flow_service(mode="proposal_write")
    correction_case = repository.load_or_create(
        source_scope="ai-destination", row_id=20
    )
    correction_case.proposal_generation = 1
    correction_case.write_intent = {
        "generation": 1,
        "field_names": [AI_CORRECTION_STATUS],
        "value_digest": stable_digest({AI_CORRECTION_STATUS: "Analysis Ready"}),
        "values": {AI_CORRECTION_STATUS: "Analysis Ready"},
        "state": "pending",
    }
    reader.values[AI_CORRECTION_STATUS] = "Analysis Ready"
    assert service._reconcile_write_intent(
        correction_case=correction_case, schema=schema_result()
    )
    assert correction_case.write_intent["state"] == "reconciled"
    correction_case.write_intent["state"] = "pending"
    reader.values[AI_CORRECTION_STATUS] = "New"
    assert not service._reconcile_write_intent(
        correction_case=correction_case, schema=schema_result()
    )
    assert correction_case.write_intent["state"] == "workflow_write_outcome_unresolved"


class MultiRepository:
    def __init__(self):
        self.cases = {}

    def load_or_create(self, *, source_scope, row_id):
        if row_id not in self.cases:
            self.cases[row_id] = CorrectionCase(
                ("a" if row_id == 51 else "b") * 64,
                row_id,
                source_scope,
                "now",
                "now",
            )
        return self.cases[row_id]

    def save(self, correction_case, **kwargs):
        self.cases[correction_case.row_id] = correction_case

    def list_cases(self):
        return tuple(self.cases.values())


class MultiReader:
    def __init__(self):
        self.values = {
            row_id: {
                **{title: None for title in REQUIRED_COLUMNS},
                AI_CORRECTION: True,
            }
            for row_id in (51, 52)
        }

    def read_rows(self, **kwargs):
        return tuple(
            CorrectionRow(row_id, dict(values), 1)
            for row_id, values in self.values.items()
        )

    def read_row(self, *, row_id, **kwargs):
        return CorrectionRow(row_id, dict(self.values[row_id]), 1)

    def read_context_row(self, *, row_id, **kwargs):
        return self.read_row(row_id=row_id)

    def read_comments(self, *, row_id):
        return (
            CorrectionComment(1, row_id, "t", "t", "reviewer", "protected"),
        )


class MultiWriter:
    def __init__(self, reader):
        self.reader = reader

    def write(self, *, row_id, updates, **kwargs):
        assert set(updates) <= WORKFLOW_OWNED_COLUMNS
        self.reader.values[row_id].update(updates)
        return SimpleNamespace(success=True, status="workflow_write_reconciled")


class CountingDispatcher:
    def __init__(self):
        self.calls = 0

    def dispatch(self, task, *, on_started):
        self.calls += 1
        on_started()
        return CodexDispatchResult(
            True, "codex_implemented", True, True, True, "e" * 40
        )


def test_only_one_implementation_job_starts_per_training_cycle():
    reader = MultiReader()
    repository = MultiRepository()
    dispatcher = CountingDispatcher()
    service = DocumentProcessorTrainingApplicationService(
        schema_service=SimpleNamespace(read=schema_result),
        reader=reader,
        repository=repository,
        analyzer=FlowAnalyzer(),
        writer=MultiWriter(reader),
        task_service=PhiSafeImplementationTaskService(),
        dispatcher=dispatcher,
        mode="approval_dispatch",
    )
    service.run_cycle()
    for values in reader.values.values():
        values[APPROVE_AI_CORRECTION] = True
    first_approved_cycle = service.run_cycle()
    assert dispatcher.calls == 1
    assert first_approved_cycle.implementation_started_count == 1
    second_approved_cycle = service.run_cycle()
    assert dispatcher.calls == 2
    assert second_approved_cycle.implementation_started_count == 1
    assert all(case.implementation_attempt_count == 1 for case in repository.cases.values())


def test_prefect_deployment_and_operator_contracts_are_exact():
    config = yaml.safe_load((ROOT / "prefect.yaml").read_text(encoding="utf-8"))
    deployments = {item["name"]: item for item in config["deployments"]}
    assert set(deployments) == {
        "prefect-control-room-test",
        "document-processor-manual",
        "document-processor-live",
        "document-processor-training",
    }
    training = deployments["document-processor-training"]
    assert training["schedule"] is None and training["parameters"] == {}
    assert training["concurrency_limit"] == {"limit": 1, "collision_strategy": "CANCEL_NEW"}
    assert training["work_pool"]["name"] == "lthhc-dp-training-process"
    source = (ROOT / "scripts/invoke_prefect_control_room.ps1").read_text(encoding="utf-8-sig")
    installer = (ROOT / "scripts/install_prefect_control_room_commands.ps1").read_text(encoding="utf-8-sig")
    for command, action in (
        ("startdptraining", "StartDPTraining"),
        ("statusdptraining", "StatusDPTraining"),
        ("stopdptraining", "StopDPTraining"),
    ):
        assert f"{command} = '{action}'" in installer
        assert action in source
    assert "startfeedback" not in installer


def test_cycle_summary_has_only_approved_safe_fields():
    assert tuple(field.name for field in fields(TrainingCycleSummary)) == (
        "effective_mode", "business_context_version", "analysis_contract_version",
        "flagged_case_count", "new_case_count", "updated_case_count",
        "analysis_ready_count", "awaiting_approval_count",
        "implementation_authorized_count", "implementation_started_count",
        "implementation_completed_count", "implementation_failed_count",
        "retest_required_count", "resolved_count",
        "needs_more_information_count", "requires_external_system_count",
        "polling_result", "failure_category", "recoverable", "retryable",
    )


if __name__ == "__main__":
    tests = [value for name, value in tuple(globals().items()) if name.startswith("test_")]
    passed = 0
    for test in tests:
        test()
        passed += 1
    print(f"Passed: {passed}")
    print("Failed: 0")
    print("Classification: synthetic deterministic/mock/local protected state")
    print("External integrations: not called")
    print("PHI handling: synthetic values only; protected content was encrypted or memory-only")
