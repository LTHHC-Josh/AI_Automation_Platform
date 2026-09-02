import re
from typing import Iterable


class ReviewReasonSummaryService:
    """Build a deterministic, PHI-safe staff summary of technical reasons."""

    INTERNAL_ONLY_REASONS = frozenset({
        "filename payer could not be resolved.",
        "filename service could not be resolved.",
        "filename document type could not be resolved.",
        "filename date could not be determined.",
    })

    EXACT_REASON_CODES = {
        "authorization quantity requires verification": (
            "authorization_quantity_requires_verification"
        ),
        "authorization subtype requires verification": (
            "document_subtype_unknown"
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
            "document_subtype_unknown"
        ),
        "2067 subtype could not be deterministically determined.": (
            "document_subtype_unknown"
        ),
        "authorization or service termination subtype could not be determined.": (
            "document_subtype_unknown"
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
        "missing authorization quantity": "authorized_units_missing_required",
        "authorized_units is not supported by its source evidence": (
            "authorized_units_unverified"
        ),
        "start_date is not supported by its source evidence": (
            "authorization_start_date_unverified"
        ),
        "start_date has no source evidence": "authorization_start_date_unverified",
        "start_date could not be normalized": "authorization_start_date_invalid",
        "start_date contains multiple date values": (
            "authorization_start_date_conflicting"
        ),
        "invalid authorization start date": "authorization_start_date_invalid",
        "end_date is not supported by its source evidence": (
            "authorization_end_date_unverified"
        ),
        "end_date has no source evidence": "authorization_end_date_unverified",
        "end_date could not be normalized": "authorization_end_date_invalid",
        "end_date contains multiple date values": "authorization_end_date_conflicting",
        "invalid authorization end date": "authorization_end_date_invalid",
        "authorization end date is before start date": (
            "authorization_date_range_conflicting"
        ),
        "authorization status requires verification": (
            "authorization_status_unverified"
        ),
        "filename person components could not be resolved.": "filename_person_unknown",
        "filename source extension is unsupported.": "filename_extension_unsupported",
        "business filename could not be composed safely.": "filename_composition_failed",
    }

    SERVICE_LINE_RULES = (
        (r"service line \d+ modifier .*source evidence", "service_line_modifier_unclear_source_support"),
        (r"service line \d+ quantity .*source evidence", "service_line_quantity_unclear_source_support"),
        (r"service line \d+ (start|end) date .*source evidence", "service_line_date_unclear_source_support"),
        (r"service line \d+ (start|end) date .*normalized", "service_line_date_invalid"),
        (r"service line \d+ status .*source evidence", "service_line_status_unclear_source_support"),
        (r"service line \d+ service code .*source evidence", "service_line_service_code_unclear_source_support"),
        (r"service line \d+ .*confidence", "service_line_low_confidence"),
        (r"service line \d+ has no source evidence", "service_line_source_unavailable"),
    )

    CATEGORY_RULES = (
        ("service codes", ("service code", "hcpcs", "bill code")),
        ("modifiers", ("modifier",)),
        ("document subtype", ("document subtype", "subtype")),
        ("authorization status", ("authorization status", "checkbox", "approval status")),
        ("authorization start date", ("authorization start date", "start_date", "start date")),
        ("authorization end date", ("authorization end date", "end_date", "end date")),
        ("authorized units", ("authorized_units", "authorization quantity")),
        ("authorization number", ("authorization number",)),
        ("member id", ("member id", "member identifier")),
        ("patient name", ("patient name",)),
        ("payer", ("payer",)),
        ("quantity", ("quantity", "units", "visits")),
        ("document type", ("document type", "document category", "classification")),
        ("dates", ("date", "effective period")),
        ("identifiers", ("identifier", "authorization number", "member id")),
        ("extracted fields", ("extracted field", "structured data")),
    )

    OPERATOR_REASONS = {
        "authorization_quantity_requires_verification": "Authorization quantity meaning requires verification",
        "document_subtype_unknown": "AI Document Subtype: Unknown",
        "classification_confidence_below_required_threshold": "Document classification confidence is below the required threshold",
        "classification_confidence_below_recommended_threshold": "Document classification confidence is below the recommended threshold",
        "extraction_field_confidence_below_threshold": "Extracted field confidence is below the acceptance threshold",
        "structured_data_unavailable": "No supported structured information was found",
        "document_type_unknown": "Document type could not be determined",
        "document_category_unknown": "Document category could not be determined",
        "document_category_unsupported": "Document category is not supported",
        "classification_category_subtype_incompatible": "Document category and workflow are inconsistent",
        "document_category_requires_confirmation": "Document category requires confirmation",
        "classification_support_reason_missing": "Document classification evidence is incomplete",
        "modifier_ownership_unresolved": "Modifier: Could not be assigned",
        "service_line_modifier_unclear_source_support": "Service-line Modifier: Could not be verified",
        "service_line_quantity_unclear_source_support": "Service-line Quantity: Could not be verified",
        "service_line_date_unclear_source_support": "Service-line Date: Could not be verified",
        "service_line_date_invalid": "Service-line Date: Invalid",
        "service_line_status_unclear_source_support": "Service-line Status: Could not be verified",
        "service_line_service_code_unclear_source_support": "Service-line Service Code: Could not be verified",
        "service_line_low_confidence": "Service-line: Below confidence threshold",
        "service_line_source_unavailable": "Service-line: Could not be verified",
        "authorization_status_unclear_source_support": "Authorization Status: Could not be verified",
        "authorization_status_unverified": "Authorization Status: Could not be verified",
        "authorization_status_missing_required": "Authorization Status: Missing",
        "authorization_number_missing_required": "Authorization Number: Missing",
        "member_id_missing_required": "Member ID: Missing",
        "payer_missing_required": "Payer: Missing",
        "patient_name_missing_required": "Patient Name: Missing",
        "authorization_start_date_missing_required": "Authorization Start Date: Missing",
        "authorization_start_date_unverified": "Authorization Start Date: Could not be verified",
        "authorization_start_date_invalid": "Authorization Start Date: Invalid",
        "authorization_start_date_conflicting": "Authorization Start Date: Conflicting",
        "authorization_end_date_unverified": "Authorization End Date: Could not be verified",
        "authorization_end_date_invalid": "Authorization End Date: Invalid",
        "authorization_end_date_conflicting": "Authorization End Date: Conflicting",
        "authorization_date_range_conflicting": "Authorization Date Range: Conflicting",
        "authorized_units_missing_required": "Authorized Units: Missing",
        "authorized_units_unverified": "Authorized Units: Could not be verified",
        "modifiers_unclear_source_support": "Modifier: Could not be verified",
        "quantity_unclear_source_support": "Authorized Units: Could not be verified",
        "dates_unclear_source_support": "Date: Could not be verified",
        "identifiers_unclear_source_support": "Identifier: Could not be verified",
        "service_codes_unclear_source_support": "Service Code: Could not be verified",
        "service_codes_low_confidence": "Service Code: Below confidence threshold",
        "service_codes_confidence_unavailable": "Service Code: Confidence unavailable",
        "modifiers_low_confidence": "Modifier: Below confidence threshold",
        "filename_person_unknown": "Filename Person Components: Unknown",
        "filename_extension_unsupported": "Attachment File Type: Unsupported for business naming",
        "filename_composition_failed": "Business Filename: Could not be composed safely",
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
        normalized = str(code or "document_requires_review")
        suffixes = (
            ("_confidence_unavailable", "Confidence unavailable"),
            ("_low_confidence", "Below confidence threshold"),
            ("_unclear_source_support", "Could not be verified"),
            ("_missing_required", "Missing"),
            ("_invalid", "Invalid"),
            ("_ambiguous", "Ambiguous"),
            ("_conflicting", "Conflicting"),
        )
        for suffix, problem in suffixes:
            if normalized.endswith(suffix):
                category = normalized[:-len(suffix)]
                break
        else:
            category = normalized
            problem = "Requires review"
        label = category.replace("_", " ").strip().title()
        label = label.replace("Service Line", "Service-line")
        return f"{label}: {problem}"

    def _reason_codes(self, reasons: list[str]) -> list[str]:
        codes: list[str] = []
        for reason in reasons:
            if reason in self.INTERNAL_ONLY_REASONS:
                continue
            if reason.startswith(("request_type ", "request type ")):
                continue
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
        superseded = set()
        if any(code in codes for code in {
            "authorization_start_date_unverified",
            "authorization_start_date_invalid",
            "authorization_start_date_ambiguous",
            "authorization_start_date_conflicting",
        }):
            superseded.add("authorization_start_date_missing_required")
        if "authorized_units_unverified" in codes:
            superseded.add("authorized_units_missing_required")
        if "service_line_quantity_unclear_source_support" in codes:
            superseded.update({
                "authorized_units_missing_required",
                "authorized_units_unverified",
                "quantity_unclear_source_support",
            })
        codes = [code for code in codes if code not in superseded]
        if any(not code.startswith("document_details_") for code in codes):
            codes = [code for code in codes if not code.startswith("document_details_")]
        return codes

    @staticmethod
    def _cause(reasons: list[str]) -> str:
        if any("confidence is unavailable" in reason for reason in reasons):
            return "confidence unavailable"
        low_confidence = any("confidence" in reason for reason in reasons)
        if low_confidence:
            return "low confidence"
        if any("missing" in reason for reason in reasons):
            return "missing required"
        if any("ambiguous" in reason for reason in reasons):
            return "ambiguous"
        if any("conflict" in reason or "multiple" in reason for reason in reasons):
            return "conflicting"
        if any("invalid" in reason or "could not be normalized" in reason for reason in reasons):
            return "invalid"
        if any(
            re.search(r"unsupported|support|evidence|verify|verification|unclear|unknown", reason)
            for reason in reasons
        ):
            return "unclear source support"
        return "requires review"

    @staticmethod
    def _join(values: list[str]) -> str:
        if len(values) == 1:
            return values[0]
        if len(values) == 2:
            return f"{values[0]} and {values[1]}"
        return f"{', '.join(values[:-1])}, and {values[-1]}"
