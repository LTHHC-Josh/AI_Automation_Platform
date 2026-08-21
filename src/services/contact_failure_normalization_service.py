from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Any


@dataclass(frozen=True, repr=False)
class ContactFailureNormalizationResult:
    value: str | None
    confidence: float
    source_text: str = field(repr=False)
    supported: bool
    review_required: bool
    status: str


class ContactFailureNormalizationService:
    """Normalize explicitly supported contact-failure wording only."""

    CONTACT_TERMS = {
        "call", "called", "calling", "contact", "phone", "reach", "reached",
        "telephone",
    }
    MEMBER_TERMS = {
        "client", "consumer", "individual", "member", "patient", "recipient",
    }
    FAILURE_TERMS = {
        "attempt", "attempted", "cannot", "difficult", "difficulty", "failed",
        "failure", "tried", "trying", "unable", "unreachable", "unsuccessful",
    }
    RESPONSE_TERMS = {"answer", "answered", "respond", "responded", "response"}
    NEGATION_TERMS = {"no", "not", "without"}
    REQUEST_TERMS = {"attempt", "attempted", "please", "request", "requested"}
    CONDITION_TERMS = {"cannot", "failure", "failed", "if", "unless", "without"}
    SERVICE_TERMS = {"authorization", "benefit", "benefits", "care", "case", "service", "services"}
    CONSEQUENCE_TERMS = {
        "cancel", "cancelled", "close", "closed", "closure", "delay", "delayed",
        "deny", "denied", "discontinue", "discontinued", "end", "ended", "loss",
        "lose", "stop", "stopped", "suspend", "suspended", "terminate",
        "terminated", "termination",
    }

    def normalize(
        self,
        *,
        source_text: Any,
        confidence: Any,
    ) -> ContactFailureNormalizationResult:
        evidence = str(source_text or "")
        normalized_confidence = self._confidence(confidence)
        clauses = self._clauses(evidence)

        contact_evidence = any(
            self._contact_failure_clause(clause)
            or self._supported_contact_request_clause(clause)
            for clause in clauses
        )
        consequence_evidence = any(
            self._conditional_service_consequence_clause(clause)
            for clause in clauses
        )

        if contact_evidence:
            return ContactFailureNormalizationResult(
                value="contact_failure",
                confidence=normalized_confidence,
                source_text=evidence,
                supported=True,
                review_required=False,
                status=(
                    "supported_with_service_consequence"
                    if consequence_evidence
                    else "supported"
                ),
            )

        return ContactFailureNormalizationResult(
            value=None,
            confidence=normalized_confidence,
            source_text=evidence,
            supported=False,
            review_required=True,
            status="unknown",
        )

    @classmethod
    def _contact_failure_clause(cls, tokens: set[str]) -> bool:
        if not tokens & cls.CONTACT_TERMS or not tokens & cls.MEMBER_TERMS:
            return False
        explicit_failure = bool(tokens & cls.FAILURE_TERMS)
        missing_response = bool(tokens & cls.NEGATION_TERMS) and bool(
            tokens & cls.RESPONSE_TERMS
        )
        return explicit_failure or missing_response

    @classmethod
    def _supported_contact_request_clause(cls, tokens: set[str]) -> bool:
        return (
            bool(tokens & cls.REQUEST_TERMS)
            and bool(tokens & cls.CONTACT_TERMS)
            and bool(tokens & cls.MEMBER_TERMS)
            and (
                bool(tokens & cls.FAILURE_TERMS)
                or (
                    bool(tokens & cls.NEGATION_TERMS)
                    and bool(tokens & cls.RESPONSE_TERMS)
                )
            )
        )

    @classmethod
    def _conditional_service_consequence_clause(cls, tokens: set[str]) -> bool:
        return (
            bool(tokens & cls.CONDITION_TERMS)
            and bool(tokens & cls.CONTACT_TERMS)
            and bool(tokens & cls.SERVICE_TERMS)
            and bool(tokens & cls.CONSEQUENCE_TERMS)
        )

    @staticmethod
    def _clauses(value: str) -> list[set[str]]:
        clauses = re.split(r"[\r\n.!?;]+", value.lower())
        return [
            set(re.findall(r"[a-z0-9]+", clause))
            for clause in clauses
            if clause.strip()
        ]

    @staticmethod
    def _confidence(value: Any) -> float:
        try:
            normalized = float(value)
        except (TypeError, ValueError):
            return 0.0
        return max(0.0, min(normalized, 1.0))
