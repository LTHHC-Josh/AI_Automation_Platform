"""Synthetic authorization checks; no model, network, or production operations."""
from copy import deepcopy
from src.services.local_code_update_authorization import LocalCodeUpdateAuthorization

class Store:
    def __init__(self): self.data = {}; self.writes = 0
    def load(self, kind, identity): return deepcopy(self.data.get((kind, identity)))
    def save(self, kind, identity, value):
        self.data[kind, identity] = deepcopy(value); self.writes += 1

def request(service, **changes):
    args = dict(receipt="a"*64, family="AUTH", code="correct_filename",
                resolution_verified=True)
    args.update(changes)
    return service.record(**args)

def test_exact_resolution_is_durable_and_idempotent():
    store=Store(); service=LocalCodeUpdateAuthorization(store)
    assert request(service) == "awaiting_verified_isolation"
    assert request(LocalCodeUpdateAuthorization(store)) == "awaiting_verified_isolation"
    assert store.writes == 1
    value=next(iter(store.data.values()))
    assert value["generation_attempt_count"] == value["promotion_attempt_count"] == 0
    assert value["intent"]["family"] == "authorization"

def test_changed_intent_cannot_reuse_resolution():
    store=Store(); service=LocalCodeUpdateAuthorization(store); request(service)
    try: request(service, code="correct_mapping")
    except ValueError as ex: assert str(ex)=="local_update_authorization_conflict"
    else: raise AssertionError("changed intent authorized")
    assert store.writes == 1

def test_no_approval_no_authorization():
    for flag in (False, None, 1, "true"):
        store=Store()
        try: request(LocalCodeUpdateAuthorization(store), resolution_verified=flag)
        except ValueError as ex: assert str(ex)=="local_update_authorization_invalid"
        else: raise AssertionError("unproven approval authorized")
        assert store.writes == 0

def test_untrusted_values_never_persist():
    for key,value in (("family","synthetic-private-marker"),
                      ("code","synthetic-private-marker"),
                      ("receipt","synthetic-private-marker"),
                      ("code","needs_investigation")):
        store=Store()
        try: request(LocalCodeUpdateAuthorization(store), **{key:value})
        except ValueError as ex: assert "synthetic-private-marker" not in str(ex)
        else: raise AssertionError("untrusted input accepted")
        assert store.writes == 0

def test_changed_status_fails_closed():
    store=Store(); service=LocalCodeUpdateAuthorization(store); request(service)
    next(iter(store.data.values()))["status"]="unproven_promoted"
    try: request(service)
    except ValueError as ex: assert str(ex)=="local_update_authorization_conflict"
    else: raise AssertionError("unproven promotion accepted")

if __name__ == "__main__":
    tests=[v for k,v in list(globals().items()) if k.startswith("test_")]
    for test in tests: test()
    print("Passed:",len(tests))
    print("Failed: 0")
