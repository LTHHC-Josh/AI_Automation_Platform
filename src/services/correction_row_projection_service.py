"""Scope an existing-row patch without merging extraction candidates.

The validated replay remains immutable. Only an unchanged, independently
accepted scalar production value may retain its existing out-of-scope confidence.
All other unrelated differences are still handled by the executor's guard.
"""
from math import isfinite

from src.models.document_processor_business_context import DOCUMENT_PROCESSOR_BUSINESS_CONTEXT
from src.services.review_decision_service import ReviewDecisionService
from src.services.smartsheet_review_configuration_service import APPROVED_DOCUMENT_FIELD_POLICIES


class CorrectionRowProjectionService:
    @staticmethod
    def project(current, replay, *, policies, selected):
        values = dict(replay)
        preserved = set()
        protected_columns = set()
        approved = {(p.source_field, p.column_name, p.confidence_column_name)
                    for p in APPROVED_DOCUMENT_FIELD_POLICIES if p.confidence_column_name}
        minimum = ReviewDecisionService.FIELD_CONFIDENCE_THRESHOLD
        maximum = DOCUMENT_PROCESSOR_BUSINESS_CONTEXT.confidence_policy.model_candidate_maximum

        def accepted_confidence(value):
            return (type(value) in (int, float) and isfinite(value)
                    and minimum <= value <= maximum)

        for policy in policies:
            name, confidence = policy.column_name, policy.confidence_column_name
            if ((policy.source_field, name, confidence) not in approved
                    or not selected or name in selected or confidence in selected
                    or replay.get(name) is None or replay.get(name) == ""
                    or current.get(name) != replay.get(name)
                    or current.get(confidence) == replay.get(confidence)
                    or not accepted_confidence(current.get(confidence))
                    or not accepted_confidence(replay.get(confidence))):
                continue
            values[confidence] = current[confidence]
            preserved.add(confidence)
            protected_columns.update((name, confidence))

        if preserved:
            # Display aggregate, not model/candidate confidence. Use precisely the
            # explicit displayed value/confidence pairs after scoped preservation.
            confidences = [values[p.confidence_column_name] for p in policies
                           if p.confidence_column_name and values.get(p.column_name) is not None
                           and values.get(p.column_name) != ""
                           and accepted_confidence(values.get(p.confidence_column_name))]
            values["AI Minimum Field Confidence"] = min(confidences) if confidences else None
        return values, preserved, protected_columns
