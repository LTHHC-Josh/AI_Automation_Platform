from src.ai.provider_loader import ProviderLoader

import src.business_rules.rules as rules

from src.business_rules.rule_registry import RuleRegistry
from src.business_rules.rules.neutral_rule import NeutralRule


class RuleFactory:
    """
    Creates business rule instances based on document type.

    Recognized categories without specialized business rules use an
    explicit neutral rule. Unsupported internal routing values still
    fail rather than being silently accepted.
    """

    NEUTRAL_DOCUMENT_TYPES = {
        "referral",
        "termination",
        "denial",
        "assessment",
        "plan_of_care",
        "claim",
        "other",
        "unknown",
    }

    @staticmethod
    def create(document_type: str):
        """
        Create the appropriate business-rule instance.
        """

        ProviderLoader.load(rules)

        normalized_document_type = str(
            document_type
            or ""
        ).strip().lower()

        rule_class = RuleRegistry.get(
            normalized_document_type
        )

        if rule_class is not None:
            return rule_class()

        if (
            normalized_document_type
            in RuleFactory.NEUTRAL_DOCUMENT_TYPES
        ):
            return NeutralRule()

        raise ValueError(
            f"No business rule registered for document type "
            f"'{document_type}'."
        )
