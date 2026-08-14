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

    def __init__(self) -> None:
        super().__init__(
            "Microsoft Graph request failed."
        )
