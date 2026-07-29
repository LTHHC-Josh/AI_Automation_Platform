from src.business_rules.provider_registration import register_rule
from src.business_rules.rule import Rule
from src.models.document import Document


@register_rule("authorization")
class AuthorizationRule(Rule):
    """
    Business rules for Authorization documents.
    """

    document_type = "authorization"

    def execute(self, document: Document) -> list:
        """
        Execute business rules for an authorization document.
        """

        actions = []

        data = document.extracted_data

        if not data.get("patient_name"):
            actions.append("Missing patient name")

        if not data.get("authorization_number"):
            actions.append("Missing authorization number")

        approved_visits = data.get("approved_visits", 0)

        try:
            approved_visits = int(approved_visits)
        except (TypeError, ValueError):
            approved_visits = 0

        if approved_visits <= 0:
            actions.append("No approved visits")

        if not actions:
            actions.append("Authorization validated successfully")

        return actions