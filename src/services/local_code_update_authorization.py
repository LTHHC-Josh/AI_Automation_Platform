"""Durable authorization for local code updates; never executes model-generated code.

The caller holds the correction repository operation lock and proves the exact
human resolution approval. This immutable authorization is not execution status:
its historical status/counters describe the initial reservation only. Execution
and restart outcomes live in the separate local-code-job/release records.
The coordinator requires independent isolation/test/promotion proof.
"""
from src.services.local_correction_memory_service import ApprovedDocumentLessons
from src.services.document_processor_training_contracts import BEHAVIOR_CODES


class LocalCodeUpdateAuthorization:
    CONTRACT_VERSION = 1
    STATUS = "awaiting_verified_isolation"

    def __init__(self, store):
        self.store = store

    def record(self, *, receipt, family, code, resolution_verified):
        family = ApprovedDocumentLessons.family(family)
        if (resolution_verified is not True or family is None
                or code not in BEHAVIOR_CODES
                or code in {"needs_investigation", "external_dependency"}
                or not isinstance(receipt, str) or len(receipt) != 64
                or any(c not in "0123456789abcdef" for c in receipt)):
            raise ValueError("local_update_authorization_invalid")
        # No row values, comments, model text, paths, or executable instructions.
        intent = {
            "contract_version": self.CONTRACT_VERSION,
            "family": family, "behavior_code": code,
            "resolution_approved": True,
        }
        identity = "local-code-update:" + receipt
        existing = self.store.load("audit", identity)
        if existing is not None:
            if existing.get("intent") != intent or existing.get("status") != self.STATUS:
                raise ValueError("local_update_authorization_conflict")
            return self.STATUS
        self.store.save("audit", identity, {
            "intent": intent, "status": self.STATUS,
            "generation_attempt_count": 0, "promotion_attempt_count": 0,
        })
        # No implicit runner and no fallback to the historical Codex dispatcher.
        return self.STATUS
