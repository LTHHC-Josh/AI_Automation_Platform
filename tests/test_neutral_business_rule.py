from pathlib import Path

from src.business_rules.rule_factory import RuleFactory
from src.business_rules.rules.neutral_rule import NeutralRule
from src.models.document import Document


passed = 0
failed = 0


def run_test(
    name,
    test,
):
    global passed
    global failed

    try:
        test()
        passed += 1
        print(
            f"PASSED: {name}"
        )
    except Exception as error:
        failed += 1
        print(
            f"FAILED: {name}: "
            f"{type(error).__name__}"
        )


def test_recognized_categories_use_neutral_rule():
    document_types = [
        "referral",
        "termination",
        "denial",
        "assessment",
        "plan_of_care",
        "claim",
        "other",
        "unknown",
    ]

    for document_type in document_types:
        rule = RuleFactory.create(
            document_type
        )

        assert isinstance(
            rule,
            NeutralRule,
        )


def test_neutral_rule_returns_no_actions():
    rule = NeutralRule()

    result = rule.execute(
        Document(
            file_path=Path(
                "synthetic-document.pdf"
            )
        )
    )

    assert result == []


def test_unrecognized_document_type_still_fails():
    try:
        RuleFactory.create(
            "unsupported_internal_type"
        )
    except ValueError:
        return

    raise AssertionError(
        "Unrecognized document type did not fail."
    )


def test_blank_document_type_still_fails():
    try:
        RuleFactory.create(
            ""
        )
    except ValueError:
        return

    raise AssertionError(
        "Blank document type did not fail."
    )


def test_authorization_rule_is_preserved():
    rule = RuleFactory.create(
        "authorization"
    )

    assert not isinstance(
        rule,
        NeutralRule,
    )


def test_authorization_renewal_rule_is_preserved():
    rule = RuleFactory.create(
        "authorization_renewal"
    )

    assert not isinstance(
        rule,
        NeutralRule,
    )


print(
    "=" * 60
)
print(
    "Testing Neutral Business Rule Routing"
)
print(
    "=" * 60
)

run_test(
    "recognized categories use neutral rule",
    test_recognized_categories_use_neutral_rule,
)
run_test(
    "neutral rule returns no actions",
    test_neutral_rule_returns_no_actions,
)
run_test(
    "unrecognized type still fails",
    test_unrecognized_document_type_still_fails,
)
run_test(
    "blank type still fails",
    test_blank_document_type_still_fails,
)
run_test(
    "authorization rule is preserved",
    test_authorization_rule_is_preserved,
)
run_test(
    "authorization renewal rule is preserved",
    test_authorization_renewal_rule_is_preserved,
)

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
print(
    "PHI handling: No document values printed"
)

if failed:
    raise SystemExit(
        1
    )
