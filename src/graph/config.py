from dataclasses import dataclass
import os

from dotenv import load_dotenv


load_dotenv(override=True)


@dataclass(frozen=True)
class GraphConfig:
    tenant_id: str
    client_id: str
    client_secret: str
    mailbox: str


def load_graph_config() -> GraphConfig:
    config = GraphConfig(
        tenant_id=os.getenv("GRAPH_TENANT_ID", "").strip(),
        client_id=os.getenv("GRAPH_CLIENT_ID", "").strip(),
        client_secret=os.getenv("GRAPH_CLIENT_SECRET", "").strip(),
        mailbox=os.getenv("GRAPH_MAILBOX", "").strip(),
    )

    missing = [
        name
        for name, value in {
            "GRAPH_TENANT_ID": config.tenant_id,
            "GRAPH_CLIENT_ID": config.client_id,
            "GRAPH_CLIENT_SECRET": config.client_secret,
            "GRAPH_MAILBOX": config.mailbox,
        }.items()
        if not value
    ]

    if missing:
        raise RuntimeError(
            "Missing Microsoft Graph configuration: "
            + ", ".join(missing)
        )

    return config