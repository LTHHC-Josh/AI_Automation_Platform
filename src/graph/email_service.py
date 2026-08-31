from .client import GraphClient
from .config import load_graph_config


class EmailService:
    def __init__(self):
        self.client = GraphClient()
        self.config = load_graph_config()

    def get_unread_messages(
        self,
        top: int = 10,
    ) -> list[dict]:
        endpoint = (
            f"/users/{self.config.mailbox}"
            "/mailFolders/inbox/messages"
        )

        params = {
            "$filter": "isRead eq false",
            "$orderby": "receivedDateTime desc",
            "$top": top,
            "$select": (
                "id,"
                "subject,"
                "from,"
                "receivedDateTime,"
                "hasAttachments,"
                "isRead"
            ),
        }

        response = self.client.get(
            endpoint,
            params=params,
            operation_category=(
                "mailbox_enumeration"
            ),
        )

        return response.get("value", [])

    def get_recent_messages(
        self,
        top: int = 10,
    ) -> list[dict]:
        endpoint = (
            f"/users/{self.config.mailbox}"
            "/mailFolders/inbox/messages"
        )

        params = {
            "$orderby": "receivedDateTime desc",
            "$top": top,
            "$select": (
                "id,"
                "subject,"
                "receivedDateTime,"
                "isRead"
            ),
        }

        response = self.client.get(
            endpoint,
            params=params,
        )

        return response.get("value", [])

    def get_recent_attachment_messages(
        self,
        top: int,
    ) -> list[dict]:
        endpoint = (
            f"/users/{self.config.mailbox}"
            "/mailFolders/inbox/messages"
        )
        response = self.client.get(
            endpoint,
            params={
                "$orderby": "receivedDateTime desc",
                "$top": top,
                "$select": "id,receivedDateTime,hasAttachments",
            },
            operation_category="mailbox_enumeration",
        )
        return response.get("value", [])

    def get_message(
        self,
        message_id: str,
    ) -> dict:
        if not message_id:
            raise ValueError(
                "A message ID is required."
            )

        endpoint = (
            f"/users/{self.config.mailbox}"
            f"/messages/{message_id}"
        )

        params = {
            "$select": (
                "id,"
                "subject,"
                "receivedDateTime,"
                "isRead,"
                "parentFolderId"
            ),
        }

        return self.client.get(
            endpoint,
            params=params,
        )

    def get_unread_inbox_message(
        self,
        message_id: str,
    ) -> dict:
        """Re-fetch one exact Inbox message for manual acceptance verification."""
        if not message_id:
            raise ValueError(
                "A message ID is required."
            )

        endpoint = (
            f"/users/{self.config.mailbox}"
            f"/mailFolders/inbox/messages/{message_id}"
        )
        params = {
            "$select": (
                "id,"
                "subject,"
                "from,"
                "receivedDateTime,"
                "hasAttachments,"
                "isRead"
            ),
        }
        return self.client.get(
            endpoint,
            params=params,
            operation_category="mailbox_enumeration",
        )

    def mark_as_read(
        self,
        message_id: str,
    ) -> bool:
        if not message_id:
            raise ValueError(
                "A message ID is required."
            )

        endpoint = (
            f"/users/{self.config.mailbox}"
            f"/messages/{message_id}"
        )

        self.client.patch(
            endpoint,
            payload={
                "isRead": True,
            },
        )

        updated_message = self.get_message(
            message_id
        )

        return updated_message.get(
            "isRead",
            False,
        ) is True
