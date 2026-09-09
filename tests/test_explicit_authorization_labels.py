"""Synthetic label/evidence/reference regressions; no protected or external calls."""
from pathlib import Path
import runpy

from src.models.document import AuthorizationServiceLine
from src.services.evidence_validation_service import EvidenceValidationService
from src.services.intake_document_naming_service import IntakeDocumentNamingVocabulary
from src.services.reference_table_service import ReferenceTables,ServiceReferenceTable
from src.services.field_validation_diagnostic_service import FieldValidationDiagnosticService
from src.services.review_decision_service import ReviewDecisionService
from src.services.review_reason_summary_service import ReviewReasonSummaryService
from src.services.review_output_service import ReviewOutputService
from src.services.smartsheet_review_row_mapping_service import SmartsheetReviewRowMappingService
from src.ai.llm.providers.ollama_provider import OllamaProvider

fixtures=runpy.run_path(str(Path(__file__).with_name('test_intake_filename_architecture.py')))

def subject(source='Type of Authorization: Initial',confidence=0.95):
    doc=fixtures['authorization'](subtype=None)
    doc.field_evidence['intake_document_subtype']=fixtures['evidence']('INITIAL',confidence,source)
    doc.intake_subtype_support_status='unknown'
    EvidenceValidationService().validate(doc)
    IntakeDocumentNamingVocabulary.apply(doc)
    return doc

def test_explicit_initial_statement_resolves_without_external_inference():
    doc=subject()
    assert doc.intake_document_subtype=='init'
    assert doc.field_evidence['intake_document_subtype']['value']=='init'
    assert doc.field_evidence['intake_document_subtype']['confidence']==0.95
    assert doc.confidence==0.90
    result=fixtures['assemble'](doc)
    assert 'AUTH INIT' in result.policy_result.filename
    assert 'document_subtype' not in result.policy_result.placeholder_categories
    reasons=ReviewReasonSummaryService().summarize(ReviewDecisionService().evaluate(doc).reasons)
    assert 'AI Document Subtype: Unknown' not in reasons
    mapped=SmartsheetReviewRowMappingService().map(ReviewOutputService().build(doc),[],run_type='synthetic')
    assert mapped.values['AI Document Subtype']=='init'

def test_initial_statement_can_span_ocr_lines():
    assert subject('Type of Authorization:\nInitial').intake_document_subtype=='init'

def test_initial_word_without_explicit_statement_still_requires_external_context():
    for source in ('Initial visit','Initial request','Supported INITIAL','No prior service history'):
        assert subject(source).intake_document_subtype=='unknown'

def test_unselected_conflicting_or_negative_initial_statement_fails_closed():
    for source in ('Type of Authorization: Initial / Renewal','Type of Authorization: Not Initial',
                   'Type of Authorization: Initial\nType of Authorization: Renewal',
                   'Type of Authorization: [ ] Initial [ ] Renewal'):
        assert subject(source).intake_document_subtype=='unknown'

def test_low_confidence_initial_does_not_bypass_acceptance():
    assert subject(confidence=0.5).intake_document_subtype=='unknown'


def test_missing_candidate_is_not_restored_from_label_or_legacy_request_type():
    doc=fixtures['authorization'](subtype=None)
    doc.field_evidence['intake_document_subtype']=fixtures['evidence'](
        None,0.95,'Type of Authorization: Initial')
    doc.field_evidence['request_type']=fixtures['evidence'](
        'INITIAL',0.95,'Type of Authorization: Initial')
    EvidenceValidationService().validate(doc)
    assert IntakeDocumentNamingVocabulary.apply(doc).subtype_key=='unknown'


def test_explicit_label_does_not_establish_document_category():
    doc=subject()
    doc.classification_support_status='unknown'
    assert IntakeDocumentNamingVocabulary.resolve(doc).document_type_status=='Placeholder'


def test_candidate_must_match_complete_statement():
    definition,status=IntakeDocumentNamingVocabulary.validate_document_evidence(
        fixtures['evidence']('INIT',0.95,'Type of Authorization: Renewal'))
    assert definition is None and status=='unsupported'

def service_document(*,modifier='U1',source=None):
    doc=fixtures['authorization'](subtype=None)
    doc.service_lines=[AuthorizationServiceLine(service_code='T0000',modifier=modifier,confidence=0.95,
        source_text=source or 'HCPC Code:\nT0000\nModifier(s):\nU1')]
    EvidenceValidationService().validate(doc)
    return doc

def reference():
    base=fixtures['tables']()
    return ReferenceTables(base.payors,ServiceReferenceTable({
        ('T0000','U1','PROGRAM A'):{'SYNTHETIC SERVICE'},
        ('T0000','U2','PROGRAM B'):{'DIFFERENT SERVICE'},
    }))

def test_hcpc_code_and_separate_modifier_labels_reach_unique_naming_token():
    doc=service_document()
    diag=FieldValidationDiagnosticService()
    assert diag.build_service_line(doc,0,'service_code').field_state=='accepted'
    assert diag.build_service_line(doc,0,'modifier').field_state=='accepted'
    assert doc.service_lines[0].modifier=='U1'
    result=fixtures['assemble'](doc,reference_tables=reference())
    assert result.diagnostic.service_lookup_ready
    assert '_SYNTHETIC SERVICE_' in result.policy_result.filename

def test_missing_modifier_keeps_ambiguous_lookup_scoped_to_naming():
    doc=service_document(modifier=None,source='HCPC Code: T0000')
    assert FieldValidationDiagnosticService().build_service_line(doc,0,'service_code').field_state=='accepted'
    result=fixtures['assemble'](doc,reference_tables=reference())
    assert not result.diagnostic.service_lookup_ready
    assert 'service' in result.policy_result.placeholder_categories
    reasons=ReviewReasonSummaryService().summarize(ReviewDecisionService().evaluate(doc).reasons)
    assert 'Service Code: Could not be verified' not in reasons

def test_modifier_from_other_line_is_not_assigned_by_label_recognition():
    doc=service_document(modifier='U2',source='HCPC Code: T0000\nModifier(s): U1')
    assert doc.service_lines[0].modifier is None
    assert FieldValidationDiagnosticService().build_service_line(doc,0,'modifier').field_state!='accepted'

def test_explicit_label_instructions_are_present_without_model_contact():
    prompt=object.__new__(OllamaProvider)._extraction_prompt()
    assert 'HCPC Code' in prompt and 'HCPCS' in prompt and 'Modifier(s)' in prompt
    assert 'Type of Authorization: Initial' in prompt
    assert 'same service' in prompt.lower()

if __name__=='__main__':
    tests=[v for k,v in list(globals().items()) if k.startswith('test_')]
    failed=0
    for test in tests:
        try: test()
        except Exception as error:
            failed+=1; print('FAIL:',test.__name__,type(error).__name__)
    print('Passed:',len(tests)-failed); print('Failed:',failed)
    print('Classification: synthetic/mock; no external operations')
    raise SystemExit(bool(failed))
