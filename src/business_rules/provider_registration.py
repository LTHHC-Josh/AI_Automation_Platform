from typing import Type

from src.business_rules.rule import Rule
from src.business_rules.rule_registry import RuleRegistry


def register_rule(document_type: str):
    """
    Decorator used to register a business rule.

    Example:

        @register_rule("authorization")
        class AuthorizationRule(Rule):
            ...
    """

    def decorator(rule_class: Type[Rule]) -> Type[Rule]:
        RuleRegistry.register(document_type, rule_class)
        return rule_class

    return decorator