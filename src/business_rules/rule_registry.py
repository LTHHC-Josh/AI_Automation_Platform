from typing import Dict, Optional, Type

from src.business_rules.rule import Rule


class RuleRegistry:
    """
    Registry for business rule plugins.
    """

    _rules: Dict[str, Type[Rule]] = {}

    @classmethod
    def register(
        cls,
        document_type: str,
        rule_class: Type[Rule],
    ) -> None:
        """
        Register a business rule.
        """

        key = document_type.lower()

        if key in cls._rules:
            raise ValueError(
                f"Rule already registered for document type '{document_type}'."
            )

        cls._rules[key] = rule_class

    @classmethod
    def get(
        cls,
        document_type: str,
    ) -> Optional[Type[Rule]]:
        """
        Retrieve a registered rule class.
        """

        return cls._rules.get(document_type.lower())

    @classmethod
    def all(cls) -> Dict[str, Type[Rule]]:
        """
        Return all registered rules.
        """

        return cls._rules.copy()