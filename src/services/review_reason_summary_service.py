import re
from typing import Iterable


class ReviewReasonSummaryService:
    """Build a deterministic, PHI-safe staff summary of technical reasons."""

    EXACT_REASON_CODES = {
        "authorization quantity requires verification": (
            "authorization_quantity_requires_verification"
        ),
        "authorization subtype requires verification": (
            "authorization_subtype_requires_verification"
        ),
        "document classification confidence is below 75%.": (
            "classification_confidence_below_required_threshold"
        ),
        "document classification confidence is below 90%.": (
            "classification_confidence_below_recommended_threshold"
        ),
        "one or more extracted fields have confidence below 85%.": (
            "extraction_field_confidence_below_threshold"
        ),
        "no structured data was extracted from the document.": (
            "structured_data_unavailable"
        ),
        "document type could not be determined.": "document_type_unknown",
        "document category could not be determined.": "document_category_unknown",
        "document category is not supported by the classification contract.": (
            "document_category_unsupported"
        ),
        "authorization subtype could not be determined.": (
            "authorization_subtype_unknown"
        ),
        "authorization or service termination subtype could not be determined.": (
            "termination_subtype_unknown"
        ),
        "document category and subtype are incompatible.": (
            "classification_category_subtype_incompatible"
        ),
        "document category requires human confirmation.": (
            "document_category_requires_confirmation"
        ),
        "document classification has no supporting reason.": (
            "classification_support_reason_missing"
        ),
    }

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

        codes = self._reason_codes(normalized)
        return "; ".join(codes)

    def _reason_codes(self, reasons: list[str]) -> list[str]:
        codes: list[str] = []
        for reason in reasons:
            exact = self.EXACT_REASON_CODES.get(reason)
            if exact:
                codes.append(exact)
                continue
            categories = [
                label.replace(" ", "_")
                for label, keywords in self.CATEGORY_RULES
                if any(keyword in reason for keyword in keywords)
            ]
            category = categories[0] if categories else "document_details"
            cause = self._cause([reason]).replace(" ", "_")
            codes.append(f"{category}_{cause}")
        return list(dict.fromkeys(codes))

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
