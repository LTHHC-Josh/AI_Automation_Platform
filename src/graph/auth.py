from msal import ConfidentialClientApplication

from .config import load_graph_config
from .errors import GraphAuthenticationError


class GraphAuthenticator:
    def __init__(self):
        self.config = load_graph_config()

        application = None

        try:
            application = ConfidentialClientApplication(
                client_id=self.config.client_id,
                client_credential=self.config.client_secret,
                authority=(
                    "https://login.microsoftonline.com/"
                    f"{self.config.tenant_id}"
                ),
            )
        except Exception:
            pass

        if application is None:
            raise GraphAuthenticationError()

        self._app = application

    def get_access_token(self) -> str:
        result = None

        try:
            result = self._app.acquire_token_for_client(
                scopes=[
                    "https://graph.microsoft.com/.default"
                ]
            )
        except Exception:
            pass

        if not isinstance(
            result,
            dict,
        ):
            raise GraphAuthenticationError()

        access_token = result.get(
            "access_token"
        )

        if (
            not isinstance(
                access_token,
                str,
            )
            or not access_token.strip()
        ):
            raise GraphAuthenticationError()

        return access_token
