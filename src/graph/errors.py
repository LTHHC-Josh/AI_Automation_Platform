from collections.abc import Iterable


class GraphBoundaryError(RuntimeError):
    """
    Base class for application-owned Microsoft Graph failures.

    Messages and categories are deterministic and must never include
    provider diagnostics, response bodies, credentials, or tokens.
    """

    category = "graph_error"


class GraphConfigurationError(GraphBoundaryError):
    category = "configuration_error"

    def __init__(
        self,
        missing_variables: Iterable[str],
    ) -> None:
        names = tuple(
            str(name)
            for name in missing_variables
        )
        self.missing_variables = names

        super().__init__(
            "Missing Microsoft Graph configuration: "
            + ", ".join(names)
        )


class GraphAuthenticationError(GraphBoundaryError):
    category = "authentication_failed"

    def __init__(self) -> None:
        super().__init__(
            "Microsoft Graph authentication failed."
        )


class GraphAuthorizationError(GraphBoundaryError):
    category = "authorization_failed"

    def __init__(self) -> None:
        super().__init__(
            "Microsoft Graph authorization failed."
        )


class GraphRequestError(GraphBoundaryError):
    category = "graph_request_failed"

    ALLOWED_OPERATION_CATEGORIES = {
        "attachment_enumeration",
        "graph_request",
        "mailbox_enumeration",
        "message_read",
        "message_update",
    }
    ALLOWED_FAILURE_KINDS = {
        "connection",
        "http_error",
        "request_error",
        "response_decode",
        "timeout",
        "unknown",
    }

    def __init__(
        self,
        *,
        status_code=None,
        operation_category=None,
        response_present=False,
        response_content_type=None,
        failure_kind=None,
    ) -> None:
        self.status_code = self._normalize_status_code(
            status_code
        )
        self.operation_category = (
            operation_category
            if operation_category
            in self.ALLOWED_OPERATION_CATEGORIES
            else "graph_request"
        )
        self.response_present = (
            response_present is True
        )
        self.response_content_type_category = (
            self._classify_content_type(
                response_content_type
            )
            if self.response_present
            else "none"
        )
        self.failure_kind = (
            failure_kind
            if failure_kind
            in self.ALLOWED_FAILURE_KINDS
            else "unknown"
        )

        super().__init__(
            "Microsoft Graph request failed."
        )

    @staticmethod
    def _normalize_status_code(value):
        if isinstance(value, bool):
            return None

        try:
            normalized = int(value)
        except (TypeError, ValueError):
            return None

        if normalized < 100 or normalized > 599:
            return None

        return normalized

    @staticmethod
    def _classify_content_type(value):
        normalized = str(
            value
            or ""
        ).strip().lower()

        if not normalized:
            return "empty"

        media_type = normalized.split(
            ";",
            1,
        )[0].strip()

        if (
            media_type == "application/json"
            or media_type.endswith(
                "+json"
            )
        ):
            return "json"

        if media_type.startswith(
            "text/"
        ):
            return "text"

        if (
            media_type.startswith(
                "image/"
            )
            or media_type
            in {
                "application/octet-stream",
                "application/pdf",
            }
        ):
            return "binary"

        return "other"
