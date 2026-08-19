import re
from typing import Iterable


class ReviewReasonSummaryService:
    """Build a deterministic, PHI-safe staff summary of technical reasons."""

    CATEGORY_RULES = (
        ("service codes", ("service code", "hcpcs", "bill code")),
        ("modifiers", ("modifier",)),
        ("authorization status", ("authorization status", "checkbox", "approval status")),
        ("quantity", ("quantity", "units", "visits")),
        ("request type", ("request type", "subtype", "renewal", "initial request")),
        ("document type", ("document type", "document category", "classification")),
        ("dates", ("date", "effective period")),
        ("identifiers", ("identifier", "authorization number", "member id")),
        ("extracted fields", ("extracted field", "structured data")),
    )

    def summarize(self, reasons: Iterable[str]) -> str:
        normalized = [
            str(reason).strip().lower()
            for reason in reasons
            if reason is not None and str(reason).strip()
        ]
        if not normalized:
            return ""

        categories = []
        for label, keywords in self.CATEGORY_RULES:
            if any(keyword in reason for reason in normalized for keyword in keywords):
                categories.append(label)

        if not categories:
            categories = ["document details"]

        subject = self._join(categories)
        cause = self._cause(normalized)
        return f"Manual review needed for {subject} due to {cause}."

    @staticmethod
    def _cause(reasons: list[str]) -> str:
        low_confidence = any("confidence" in reason for reason in reasons)
        unclear_support = any(
            re.search(r"unsupported|support|evidence|verify|verification|unclear|ambiguous|conflict|missing|unknown", reason)
            for reason in reasons
        )
        if low_confidence and unclear_support:
            return "low confidence or unclear source support"
        if low_confidence:
            return "low confidence"
        if unclear_support:
            return "unclear source support"
        return "unresolved document information"

    @staticmethod
    def _join(values: list[str]) -> str:
        if len(values) == 1:
            return values[0]
        if len(values) == 2:
            return f"{values[0]} and {values[1]}"
        return f"{', '.join(values[:-1])}, and {values[-1]}"
