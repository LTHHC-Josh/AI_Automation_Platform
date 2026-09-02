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
        "service-line modifier relationship requires verification": (
            "modifier_ownership_unresolved"
        ),
        "missing authorization status": "authorization_status_missing_required",
        "missing authorization number": "authorization_number_missing_required",
        "missing member id": "member_id_missing_required",
        "missing payer": "payer_missing_required",
        "missing patient name": "patient_name_missing_required",
        "missing authorization start date": "authorization_start_date_missing_required",
        "missing authorization end date": "authorization_end_date_missing_required",
    }

    SERVICE_LINE_RULES = (
        (r"service line \d+ modifier .*source evidence", "service_line_modifier_unclear_source_support"),
        (r"service line \d+ quantity .*source evidence", "service_line_quantity_unclear_source_support"),
        (r"service line \d+ (start|end) date .*source evidence", "service_line_date_unclear_source_support"),
        (r"service line \d+ status .*source evidence", "service_line_status_unclear_source_support"),
        (r"service line \d+ service code .*source evidence", "service_line_service_code_unclear_source_support"),
        (r"service line \d+ .*confidence", "service_line_low_confidence"),
        (r"service line \d+ has no source evidence", "service_line_source_unavailable"),
    )

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

    OPERATOR_REASONS = {
        "authorization_quantity_requires_verification": "Authorization quantity meaning requires verification",
        "authorization_subtype_requires_verification": "Authorization workflow requires verification",
        "classification_confidence_below_required_threshold": "Document classification confidence is below the required threshold",
        "classification_confidence_below_recommended_threshold": "Document classification confidence is below the recommended threshold",
        "extraction_field_confidence_below_threshold": "Extracted field confidence is below the acceptance threshold",
        "structured_data_unavailable": "No supported structured information was found",
        "document_type_unknown": "Document type could not be determined",
        "document_category_unknown": "Document category could not be determined",
        "document_category_unsupported": "Document category is not supported",
        "authorization_subtype_unknown": "Authorization workflow could not be determined",
        "termination_subtype_unknown": "Termination workflow could not be determined",
        "classification_category_subtype_incompatible": "Document category and workflow are inconsistent",
        "document_category_requires_confirmation": "Document category requires confirmation",
        "classification_support_reason_missing": "Document classification evidence is incomplete",
        "modifier_ownership_unresolved": "A modifier was found but could not be reliably assigned to a service line",
        "service_line_modifier_unclear_source_support": "Service-line modifier could not be verified from document evidence",
        "service_line_quantity_unclear_source_support": "Service-line quantity could not be verified from document evidence",
        "service_line_date_unclear_source_support": "Service-line date could not be verified from document evidence",
        "service_line_status_unclear_source_support": "Service-line status could not be verified from document evidence",
        "service_line_service_code_unclear_source_support": "Service-line code could not be verified from document evidence",
        "service_line_low_confidence": "Service-line confidence is below the required threshold",
        "service_line_source_unavailable": "Service-line source evidence is unavailable",
        "authorization_status_unclear_source_support": "Authorization status could not be verified from document evidence",
        "authorization_status_missing_required": "Required authorization status was not found",
        "authorization_number_missing_required": "Required authorization number was not found",
        "member_id_missing_required": "Required member identifier was not found",
        "payer_missing_required": "Required payer was not found",
        "patient_name_missing_required": "Required patient name was not found",
        "authorization_start_date_missing_required": "Required authorization start date was not found",
        "authorization_end_date_missing_required": "Required authorization end date was not found",
        "modifiers_unclear_source_support": "Modifier could not be verified from document evidence",
        "quantity_unclear_source_support": "Quantity could not be verified from document evidence",
        "dates_unclear_source_support": "Date could not be verified from document evidence",
        "identifiers_unclear_source_support": "Identifier could not be verified from document evidence",
        "request_type_unclear_source_support": "Request type could not be verified from document evidence",
        "service_codes_unclear_source_support": "Service code could not be verified from document evidence",
        "service_codes_low_confidence": "Service code confidence is below the required threshold",
        "modifiers_low_confidence": "Modifier confidence is below the required threshold",
        "document_details_unclear_source_support": "Document information could not be verified",
    }

    def summarize(self, reasons: Iterable[str]) -> str:
        codes = self.summarize_codes(reasons)
        if not codes:
            return ""
        operator_reasons = []
        for code in codes.split("; "):
            reason = self.OPERATOR_REASONS.get(code)
            if reason is None:
                reason = self._humanize_safe_code(code)
            if reason not in operator_reasons:
                operator_reasons.append(reason)
        return "; ".join(operator_reasons)

    def summarize_codes(self, reasons: Iterable[str]) -> str:
        normalized = [
            str(reason).strip().lower()
            for reason in reasons
            if reason is not None and str(reason).strip()
        ]
        if not normalized:
            return ""

        codes = self._reason_codes(normalized)
        return "; ".join(codes)

    @staticmethod
    def _humanize_safe_code(code: str) -> str:
        if str(code).endswith("_low_confidence"):
            category = str(code)[:-len("_low_confidence")].replace("_", " ")
            return f"{category[:1].upper() + category[1:]} confidence is below the acceptance threshold"
        words = str(code or "unresolved_document_information").replace("_", " ")
        return words[:1].upper() + words[1:]

    def _reason_codes(self, reasons: list[str]) -> list[str]:
        codes: list[str] = []
        for reason in reasons:
            exact = self.EXACT_REASON_CODES.get(reason)
            if exact:
                codes.append(exact)
                continue
            service_line_code = next(
                (code for pattern, code in self.SERVICE_LINE_RULES if re.search(pattern, reason)),
                None,
            )
            if service_line_code:
                codes.append(service_line_code)
                continue
            categories = [
                label.replace(" ", "_")
                for label, keywords in self.CATEGORY_RULES
                if any(keyword in reason for keyword in keywords)
            ]
            category = categories[0] if categories else "document_details"
            cause = self._cause([reason]).replace(" ", "_")
            codes.append(f"{category}_{cause}")
        codes = list(dict.fromkeys(codes))
        if any(not code.startswith("document_details_") for code in codes):
            codes = [code for code in codes if not code.startswith("document_details_")]
        return codes

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
