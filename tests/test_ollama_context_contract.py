"""Synthetic no-truncation request boundary; no real inference/network."""
import json
import tempfile
from types import SimpleNamespace as N
from unittest.mock import patch
import requests

from src.ai.llm.providers.ollama_provider import OllamaProvider
from src.services.local_document_correction_workflow import preparation_failure_category


def provider():
    p=object.__new__(OllamaProvider)
    p.base_url='http://localhost:11434'; p.model='synthetic-model'; p.timeout=30
    p.context_tokens=8192; p.max_output_tokens=4096; p._last_request_metrics={}
    return p


def response(data, status=200):
    def raise_for_status():
        if status>=400: raise requests.HTTPError('PRIVATE_RESPONSE')
    return N(status_code=status,json=lambda:data,raise_for_status=raise_for_status)


def call(p=None, *, version='0.33.3', metadata=None, result=None, error=None):
    p=p or provider(); calls=[]
    def post(url,**kwargs):
        calls.append((url,kwargs))
        if url.endswith('/api/show'):
            return response(metadata if metadata is not None else {'model_info':{'llama.context_length':131072}})
        if error: raise error
        return result or response({'done':True,'done_reason':'stop','message':{'content':'{"ok":true}'},'prompt_eval_count':4426,'eval_count':1337})
    with tempfile.TemporaryDirectory() as directory, patch.object(p, '_queue_directory', directory, create=True), patch('src.ai.llm.providers.ollama_provider.requests.post',side_effect=post), patch(
            'src.ai.llm.providers.ollama_provider.requests.get',return_value=response({'version':version})):
        try:
            output=p._chat('Synthetic instructions','Synthetic evidence',{},42)
            return p, output, calls, None
        except RuntimeError as failure:
            return p,None,calls,failure


def test_explicit_full_context_and_no_shift_or_truncation():
    p,result,calls,error=call()
    assert error is None and result=={'ok':True}
    payload=calls[-1][1]['json']
    assert payload['options']['num_ctx']==8192 and payload['options']['num_predict']==4096
    assert payload['truncate'] is False and payload['shift'] is False
    assert len(payload['messages'])==2 and payload['messages'][1]['content']=='Synthetic evidence'
    assert p._last_request_metrics['context_contract_version']==1
    assert p._last_request_metrics['input_truncation_allowed'] is False
    assert 'Synthetic' not in json.dumps(p._last_request_metrics)


def test_legacy_unknown_or_malformed_version_fails_before_protected_prompt():
    for version in ('0.1.0','0.33.2','0.34.0','PRIVATE_VERSION',None,{},False):
        _,_,calls,error=call(version=version)
        assert str(error)=='local_model_context_contract_unproven'
        assert len(calls)==1 and calls[0][0].endswith('/api/show')


def test_context_budget_must_fit_authoritative_model_capacity():
    for capacity in (None,True,'131072',0,4096):
        _,_,calls,error=call(metadata={'model_info':{'llama.context_length':capacity}})
        assert str(error)=='local_model_context_configuration_invalid' and len(calls)==1


def test_multiple_model_capacities_fail_closed_at_smaller_cap():
    _,_,calls,error=call(metadata={'model_info':{'a.context_length':131072,'b.context_length':4096}})
    assert error and len(calls)==1


def test_remote_model_is_rejected_before_prompt():
    _,_,calls,error=call(metadata={'model_info':{'a.context_length':131072},'remote_host':'cloud.invalid'})
    assert str(error)=='local_model_identity_unproven' and len(calls)==1


def test_configured_budgets_are_explicit_and_not_server_defaults():
    p=provider();p.context_tokens=16384;p.max_output_tokens=2048
    _,_,calls,error=call(p)
    assert error is None and calls[-1][1]['json']['options']['num_ctx']==16384
    assert calls[-1][1]['json']['options']['num_predict']==2048


def test_invalid_budget_cannot_reach_inference():
    for name,value in (('context_tokens',True),('context_tokens',0),('max_output_tokens',-1),('max_output_tokens',8193)):
        p=provider();setattr(p,name,value)
        _,_,calls,error=call(p)
        assert str(error)=='local_model_context_configuration_invalid' and len(calls)==1


def test_token_configuration_is_strict_and_safe():
    for value in ('0','-1','8192.0',' 8192','PRIVATE_CONFIGURATION','9'*5000,'８１９２'):
        with patch.dict('os.environ',{'OLLAMA_CONTEXT_TOKENS':value}):
            try: OllamaProvider._positive_token_setting('OLLAMA_CONTEXT_TOKENS',8192)
            except RuntimeError as error: assert str(error)=='local_model_context_configuration_invalid'
            else: raise AssertionError('invalid setting accepted')
    with patch.dict('os.environ',{'OLLAMA_CONTEXT_TOKENS':'16384'}):
        assert OllamaProvider._positive_token_setting('OLLAMA_CONTEXT_TOKENS',8192)==16384


def test_incomplete_output_never_becomes_an_extraction_candidate():
    for done,reason in ((False,'stop'),(True,'length'),(True,None),(True,'PRIVATE_REASON')):
        _,result,_,error=call(result=response({'done':done,'done_reason':reason,'message':{'content':'{"ok":true}'}}))
        assert result is None and str(error)=='local_model_response_incomplete'


def test_http_rejection_is_fixed_without_response_or_exception_leakage():
    _,result,_,error=call(result=response({'error':'PRIVATE_RESPONSE'},400))
    assert result is None and str(error)=='local_model_http_error' and error.__suppress_context__


def test_transport_failures_are_safe_and_never_retried():
    for failure,expected in ((requests.Timeout('PRIVATE_TIMEOUT'),'local_model_request_timeout'),
                             (requests.ConnectionError('PRIVATE_URL'),'local_model_unavailable')):
        _,_,calls,error=call(error=failure)
        assert str(error)==expected and len(calls)==2 and error.__suppress_context__


def test_failure_categories_survive_preparation_safely():
    for code in ('local_model_context_configuration_invalid','local_model_context_contract_unproven','local_model_response_incomplete','local_model_request_timeout'):
        assert preparation_failure_category(RuntimeError(code))==code
    assert preparation_failure_category(RuntimeError('PRIVATE_DATA'))=='correction_preparation_unavailable'


def test_failed_preflight_cannot_expose_stale_previous_metrics():
    p=provider(); p._last_request_metrics={'old':True}
    p,_,_,error=call(p,version='unverified')
    assert error and p._last_request_metrics=={}


if __name__=='__main__':
    tests=[v for k,v in list(globals().items()) if k.startswith('test_')]
    failed=0
    for test in tests:
        try:test()
        except Exception as error:
            failed+=1;print('FAIL:',test.__name__,type(error).__name__)
    print('Passed:',len(tests)-failed);print('Failed:',failed)
    print('Classification: synthetic/mock; no external operations')
    raise SystemExit(bool(failed))
