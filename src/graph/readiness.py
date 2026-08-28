"""PHI-safe Graph authentication readiness shared by operator boundaries."""

from collections.abc import Callable

from .auth import GraphAuthenticator


def graph_auth_ready(
    authenticator_factory: Callable[[], GraphAuthenticator] = GraphAuthenticator,
) -> bool:
    """Return only whether the approved Graph authenticator can acquire a token."""
    token = None
    try:
        token = authenticator_factory().get_access_token()
        return isinstance(token, str) and bool(token.strip())
    except Exception:
        return False
    finally:
        token = None
