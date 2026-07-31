from msal import ConfidentialClientApplication

from .config import load_graph_config


class GraphAuthenticator:
    def __init__(self):
        self.config = load_graph_config()

        self._app = ConfidentialClientApplication(
            client_id=self.config.client_id,
            client_credential=self.config.client_secret,
            authority=f"https://login.microsoftonline.com/{self.config.tenant_id}",
        )

    def get_access_token(self) -> str:
        result = self._app.acquire_token_for_client(
            scopes=["https://graph.microsoft.com/.default"]
        )

        if "access_token" not in result:
            raise RuntimeError(
                f"Microsoft Graph authentication failed: {result.get('error_description')}"
            )

        return result["access_token"]