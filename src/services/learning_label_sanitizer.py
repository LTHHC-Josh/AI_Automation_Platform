from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any


@dataclass(frozen=True)
class SafeLearningLabel:
    label: str
    disposition: str


class LearningLabelSanitizer:
    """Convert proposed semantic labels to a non-PHI report representation."""

    SAFE_TOKENS = {
        "annual", "approval", "approved", "assessment", "authorization",
        "business", "change", "checkbox", "claim", "communication",
        "contact", "continuation", "date", "denial", "direction",
        "document", "due", "effective", "end", "extension", "failure",
        "field", "form", "free", "header", "identifier", "inbound",
        "initial", "locate", "missing", "modifier", "narrative", "no",
        "notice", "outbound", "past", "posted", "purpose", "quantity",
        "reach", "referral", "renewal", "request", "requested", "review",
        "service", "start", "status", "table", "termination", "text",
        "to", "unable", "units", "unknown", "unmodeled", "visits",
        "workflow", "utl",
    }

    def sanitize(
        self,
        value: Any,
        *,
        category: str,
        ordinal: int,
    ) -> SafeLearningLabel:
        slug = re.sub(r"[^a-z0-9]+", "_", str(value or "").lower()).strip("_")
        tokens = slug.split("_") if slug else []
        if (
            slug and len(slug) <= 64
            and all(token in self.SAFE_TOKENS or token == "2067" for token in tokens)
        ):
            return SafeLearningLabel(slug, "accepted")

        safe_category = category if category in {
            "business", "date", "document", "field", "form", "service",
            "workflow", "free_text", "other",
        } else "other"
        return SafeLearningLabel(
            f"novel_{safe_category}_concept_{ordinal}",
            "generalized",
        )
