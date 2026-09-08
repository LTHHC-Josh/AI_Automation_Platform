"""Synthetic recovery only; no external integrations or protected real data."""
from contextlib import contextmanager
from copy import deepcopy
from pathlib import Path
import runpy
import tempfile

fixture = runpy.run_path(str(Path(__file__).with_name("test_document_processor_training.py")))
build = fixture["build_flow_service"]
Result = fixture["CodexDispatchResult"]
APPROVAL = fixture["APPROVE_AI_CORRECTION"]
STATUS = fixture["AI_CORRECTION_STATUS"]
PROPOSAL = fixture["AI_PROPOSED_CORRECTION"]
from src.services.document_processor_training_contracts import HUMAN_OWNED_COLUMNS as HUMAN

class Failed:
    def dispatch(self, task, *, on_started):
        on_started()
        return Result(False, "codex_failed", True, False, False, exit_code=1)

def failed():
    app, reader, repo = build(dispatcher=Failed())
    app.run_cycle()
    reader.values[APPROVAL] = True
    app.run_cycle()
    assert repo.case.implementation_attempt_count == 1
    return app, reader, repo

def grant(app, **changes):
    options = dict(operator_authorized=True, runtime_probe_passed=True,
        repair_category="verified_codex_cli_startup_repair", expected_attempt_count=1)
    options.update(changes)
    return app.authorize_runtime_recovery(**options)

def test_recovery_preserves_human_generation_identity_and_consumed_approval():
    app, reader, repo = failed()
    before = deepcopy(repo.case)
    human = {k: reader.values[k] for k in HUMAN}
    comments = deepcopy(reader.comments)
    assert grant(app) == "runtime_recovery_authorized"
    assert repo.case.proposal_generation == before.proposal_generation
    assert repo.case.case_id == before.case_id
    assert repo.case.implementation_job_id == before.implementation_job_id
    assert repo.case.correction_approval_consumed_generation == before.correction_approval_consumed_generation
    assert repo.case.implementation_attempt_count == 1
    assert {k: reader.values[k] for k in HUMAN} == human and reader.comments == comments
    app.dispatcher = fixture["FlowDispatcher"]()
    result = app.run_cycle()
    assert result.implementation_completed_count == 1
    assert repo.case.status == "Retest Required"
    assert repo.case.implementation_attempt_count == 2
    assert app.run_cycle().implementation_started_count == 0
    assert repo.case.implementation_attempt_count == 2

def test_recovery_failure_never_automatically_retries_or_regrants():
    app, _, repo = failed()
    assert grant(app) == "runtime_recovery_authorized"
    app.run_cycle()
    assert repo.case.implementation_attempt_count == 2
    assert app.run_cycle().implementation_started_count == 0
    assert grant(app, expected_attempt_count=2) == "runtime_recovery_already_used"

def test_recovery_requires_explicit_verified_scope_and_exact_attempt():
    for options in ({"operator_authorized":False}, {"runtime_probe_passed":False},
                    {"repair_category":"unknown"}, {"expected_attempt_count":2}):
        app, reader, repo = failed()
        before = deepcopy(repo.case)
        assert grant(app, **options) != "runtime_recovery_authorized"
        assert repo.case == before
    app, _, repo = failed()
    app.mode = "proposal_write"
    assert grant(app) == "runtime_recovery_not_authorized"

def test_stale_proposal_comments_context_or_withdrawn_approval_fail_closed():
    for change in ("proposal", "comments", "context", "approval"):
        app, reader, repo = failed()
        if change == "proposal": reader.values[PROPOSAL] = "changed synthetic proposal"
        if change == "comments": reader.comments = ()
        if change == "context": reader.values["Synthetic Context"] = "changed"
        if change == "approval": reader.values[APPROVAL] = False
        assert grant(app) in {"runtime_recovery_stale_approval", "runtime_recovery_stale_context"}
        assert repo.case.implementation_attempt_count == 1
        assert reader.values[STATUS] == "Cannot Resolve Yet"

def test_non_infrastructure_failure_is_not_eligible():
    for category in ("codex_incomplete", "codex_timeout", "codex_safety_gate_failed"):
        app, _, repo = failed()
        repo.case.implementation_failure_category = category
        assert grant(app) == "runtime_recovery_not_eligible"

def test_uncertain_grant_write_reserves_once_without_dispatch():
    app, _, repo = failed()
    app.writer.write = lambda **kw: fixture["SimpleNamespace"](success=False,status="workflow_write_outcome_unresolved")
    assert grant(app) == "runtime_recovery_write_unresolved"
    assert grant(app) == "runtime_recovery_already_used"
    assert app.run_cycle().implementation_started_count == 0
    assert repo.case.implementation_attempt_count == 1

def test_production_exclusive_lock_and_recovery_audit_survive_restart():
    from src.services.smartsheet_feedback_case_storage_service import ProtectedCorrectionCaseRepository, CorrectionCaseStorageError
    app, _, repo = failed()
    assert grant(app) == "runtime_recovery_authorized"
    with tempfile.TemporaryDirectory() as d:
        storage = ProtectedCorrectionCaseRepository(directory=d, protect=lambda x:x, unprotect=lambda x:x)
        storage.save(repo.case)
        with storage.exclusive_operation():
            try:
                with storage.exclusive_operation(): pass
                raise AssertionError("second lock entered")
            except CorrectionCaseStorageError as e:
                assert e.category == "training_operation_locked"
        restored = storage.load(repo.case.case_id)
        assert restored.transition_history == repo.case.transition_history
        assert restored.correction_approval_consumed_generation == repo.case.correction_approval_consumed_generation
        assert not (Path(d)/".training-operation.lock").exists()

def test_real_writer_checks_approval_without_writing_it():
    from src.services.document_processor_training_codex_service import BoundedCodexDispatcher
    prompt = BoundedCodexDispatcher._prompt("{}")
    assert "Only the approved PHI-safe project tracker" in prompt
    assert "never read/write document or correction rows/comments" in prompt
    schema = fixture["schema_result"]()
    values = {title: None for title in fixture["REQUIRED_COLUMNS"]}
    values[APPROVAL] = True
    values[STATUS] = "Cannot Resolve Yet"
    reader = fixture["WriterReader"](fixture["CorrectionRow"](10, values, 1))
    client = fixture["WriterClient"](reader, schema)
    writer = fixture["SmartsheetCorrectionWriter"](client=client, reader=reader)
    options = dict(row_id=10, updates={STATUS:"Approved for Implementation"},
        schema=schema, expected_proposal_hash_values={APPROVAL:True})
    assert writer.write(**options).success
    assert len(client.calls) == 1
    assert set(client.calls[0][1]) == {schema.column_ids[STATUS]}
    reader.row.values[APPROVAL] = False
    assert writer.write(**options).status == "workflow_write_stale"
    assert len(client.calls) == 1

if __name__ == "__main__":
    tests = [v for k,v in tuple(globals().items()) if k.startswith("test_")]
    for test in tests: test()
    print(f"Passed: {len(tests)}")
    print("Failed: 0")
    print("Classification: synthetic deterministic/mock; no external calls")
