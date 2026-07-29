from src.ai.provider_loader import ProviderLoader

import src.business_rules.rules as rules

from src.business_rules.rule_registry import RuleRegistry


class RuleFactory:
    """
    Creates business rule instances based on document type.
    """

    @staticmethod
    def create(document_type: str):
        """
        Create the appropriate business rule instance.
        """

        ProviderLoader.load(rules)

        rule_class = RuleRegistry.get(document_type)

        if rule_class is None:
            raise ValueError(
                f"No business rule registered for document type "
                f"'{document_type}'."
            )

        return rule_class()