from pathlib import Path
from typing import Callable

from src.business_rules.rule_factory import RuleFactory
from src.business_rules.rule_registry import RuleRegistry
from src.business_rules.rules.authorization_rule import (
    AuthorizationRenewalRule,
    AuthorizationRule,
)


OBSOLETE_RULE_PATH = Path(
    "src/business_rules/authorization_rule.py"
)


def test_obsolete_rule_file_is_removed() -> None:
    assert not OBSOLETE_RULE_PATH.exists()


def test_authorization_factory_uses_plugin_rule() -> None:
    rule = RuleFactory.create(
        "authorization"
    )

    assert isinstance(
        rule,
        AuthorizationRule,
    )

    assert (
        rule.__class__.__module__
        == "src.business_rules.rules.authorization_rule"
    )


def test_renewal_factory_uses_plugin_rule() -> None:
    rule = RuleFactory.create(
        "authorization_renewal"
    )

    assert isinstance(
        rule,
        AuthorizationRenewalRule,
    )

    assert (
        rule.__class__.__module__
        == "src.business_rules.rules.authorization_rule"
    )


def test_authorization_registry_entries_are_exact() -> None:
    registered_rules = RuleRegistry.all()

    assert (
        registered_rules["authorization"]
        is AuthorizationRule
    )

    assert (
        registered_rules["authorization_renewal"]
        is AuthorizationRenewalRule
    )


def test_no_root_level_rule_module_is_registered() -> None:
    authorization_rules = {
        document_type: rule_class
        for document_type, rule_class
        in RuleRegistry.all().items()
        if document_type.startswith(
            "authorization"
        )
    }

    assert authorization_rules

    for rule_class in authorization_rules.values():
        assert (
            rule_class.__module__
            == "src.business_rules.rules.authorization_rule"
        )


def run_test(
    test_name: str,
    test_function: Callable[[], None],
) -> None:
    try:
        test_function()
    except AssertionError:
        print(
            f"FAILED: {test_name}"
        )
        raise

    print(
        f"PASSED: {test_name}"
    )


def main() -> None:
    print("=" * 60)
    print("Testing Authorization Rule Registry")
    print("=" * 60)

    tests = [
        (
            "obsolete rule file is removed",
            test_obsolete_rule_file_is_removed,
        ),
        (
            "authorization factory uses plugin rule",
            test_authorization_factory_uses_plugin_rule,
        ),
        (
            "renewal factory uses plugin rule",
            test_renewal_factory_uses_plugin_rule,
        ),
        (
            "authorization registry entries are exact",
            test_authorization_registry_entries_are_exact,
        ),
        (
            "no root-level rule module is registered",
            test_no_root_level_rule_module_is_registered,
        ),
    ]

    passed = 0
    failed = 0

    for test_name, test_function in tests:
        try:
            run_test(
                test_name,
                test_function,
            )
            passed += 1
        except AssertionError:
            failed += 1

    print()
    print(
        f"Passed: {passed}"
    )
    print(
        f"Failed: {failed}"
    )
    print(
        "Real or mock: Synthetic deterministic test"
    )
    print("=" * 60)

    if failed:
        raise SystemExit(
            1
        )


if __name__ == "__main__":
    main()