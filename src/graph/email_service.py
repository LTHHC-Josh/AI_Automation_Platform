from .client import GraphClient
from .config import load_graph_config


class EmailService:
    def __init__(self):
        self.client = GraphClient()
        self.config = load_graph_config()

    def get_unread_messages(self, top: int = 10):
        endpoint = f"/users/{self.config.mailbox}/mailFolders/inbox/messages"

        params = {
            "$filter": "isRead eq false",
            "$orderby": "receivedDateTime asc",
            "$top": top,
            "$select": (
                "id,"
                "subject,"
                "from,"
                "receivedDateTime,"
                "hasAttachments"
            ),
        }

        response = self.client.get(endpoint, params=params)
        return response.get("value", [])