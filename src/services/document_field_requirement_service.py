from typing import Any


class DocumentFieldRequirementService:
    """Authoritative, source-agnostic requiredness for final field state."""

    AUTHORIZATION_REQUIRED_FIELDS = frozenset({
        "patient_name",
        "authorization_number",
        "payer",
        "member_id",
        "authorization_status",
        "start_date",
    })

    def is_required(self, document: Any, field_name: str) -> bool:
        category = str(getattr(document, "document_category", "") or "").lower()
        document_type = str(getattr(document, "document_type", "") or "").lower()
        is_authorization = (
            category == "authorization"
            or document_type in {"authorization", "authorization_renewal"}
        )
        return (
            is_authorization
            and str(field_name) in self.AUTHORIZATION_REQUIRED_FIELDS
        )
