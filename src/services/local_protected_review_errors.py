class ProtectedReviewUnavailableError(Exception):
    """The approved local protected-review surface is unavailable."""


class ProtectedReviewFailedError(Exception):
    """The approved local protected-review surface failed safely."""
