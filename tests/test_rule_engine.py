from pathlib import Path

from src.business_rules.rule_service import RuleService
from src.document_processing.document_processor import DocumentProcessor


def main():

    processor = DocumentProcessor()
    rules = RuleService()

    document = processor.process(
        Path("sample_authorization.pdf")
    )

    print("=" * 60)
    print("DOCUMENT")
    print("=" * 60)
    print(f"Type: {document.document_type}")
    print()

    actions = rules.execute(document)

    print("=" * 60)
    print("ACTIONS")
    print("=" * 60)

    for action in actions:
        print(f"- {action}")

    print()
    print("SUCCESS")


if __name__ == "__main__":
    main()