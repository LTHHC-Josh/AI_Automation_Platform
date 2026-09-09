"""Synthetic date normalization and service-line ownership; no external calls."""
from pathlib import Path
from src.models.document import Document, AuthorizationServiceLine
from src.services.evidence_validation_service import EvidenceValidationService
from src.services.filename_policy_service import FilenamePolicyService

def test_short_year_matches_approved_filename_parser():
    service=EvidenceValidationService()
    for source in ('02/03/26','02-03-26','02/03/2026','2026-02-03'):
        assert service._parse_date(source)=='2026-02-03'
        assert service._source_supports_date('2026-02-03','Synthetic service '+source)
    assert service._parse_date('02/03/26')==FilenamePolicyService._parse_date('02/03/26').date().isoformat()

def test_invalid_or_different_evidence_stays_unsupported():
    service=EvidenceValidationService()
    assert not service._source_supports_date('2026-02-03','Other service 02/04/26')
    assert not service._source_supports_date('2026-02-03','No date stated')
    assert service._parse_date('02/30/26') is None
    assert not service._source_supports_date('2026-02-03','Malformed 02/03/260')

def test_century_and_four_digit_year_parity():
    service=EvidenceValidationService()
    for source in ('02/03/1968','02/03/2068','02/03/68','02/03/69'):
        expected=FilenamePolicyService._parse_date(source).date().isoformat()
        assert service._parse_date(source)==expected
        assert service._source_supports_date(expected,source)

def test_two_services_retain_independently_supported_short_year_dates():
    document=Document(file_path=Path('synthetic.pdf'))
    document.service_lines=[
        AuthorizationServiceLine(service_code='SYNTH1',start_date='2026-02-03',end_date='2026-03-04',confidence=.95,source_text='SYNTH1 02/03/26 03/04/26'),
        AuthorizationServiceLine(service_code='SYNTH2',start_date='2026-04-05',end_date='2026-05-06',confidence=.95,source_text='SYNTH2 04/05/26 05/06/26'),
    ]
    actions=EvidenceValidationService().validate(document)
    assert all('date' not in a.lower() for a in actions)
    assert [(x.start_date,x.end_date) for x in document.service_lines]==[('2026-02-03','2026-03-04'),('2026-04-05','2026-05-06')]
    assert all(x.confidence==.95 for x in document.service_lines)

def test_other_line_date_cannot_supply_missing_own_support():
    document=Document(file_path=Path('synthetic.pdf'))
    document.service_lines=[
        AuthorizationServiceLine(service_code='SYNTH1',start_date='2026-02-03',confidence=.95,source_text='SYNTH1 02/03/26'),
        AuthorizationServiceLine(service_code='SYNTH2',start_date='2026-02-03',confidence=.95,source_text='SYNTH2 04/05/26'),
    ]
    actions=EvidenceValidationService().validate(document)
    assert document.service_lines[0].start_date=='2026-02-03'
    assert document.service_lines[1].start_date is None
    assert any('start date' in a and 'source evidence' in a for a in actions)

if __name__=='__main__':
    tests=[v for k,v in list(globals().items()) if k.startswith('test_')]
    for test in tests: test()
    print(f'Passed: {len(tests)}; Failed: 0; synthetic deterministic; no external operations')
