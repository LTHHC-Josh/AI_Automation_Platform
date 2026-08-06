from src.models.document import Document


class NeutralRule:
    """
    Explicit no-op rule for recognized document categories without
    specialized business rules.

    No rule actions does not mean the document is verified. Validation,
    classification confidence, and human-review decisions remain
    separate.
    """

    def execute(
        self,
        document: Document,
    ) -> list[str]:
        """
        Return no category-specific business-rule actions.
        """

        return []
