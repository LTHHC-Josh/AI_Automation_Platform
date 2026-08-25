from dataclasses import dataclass, field
import os
from typing import Any
from dotenv import load_dotenv


@dataclass(frozen=True, repr=False)
class SmartsheetSubmissionKeyConfiguration:
    column_title: str | None = field(default=None, repr=False)
    configured: bool = False
    success: bool = False
    status: str = "submission_key_configuration_missing"


class SmartsheetSubmissionKeyConfigurationService:
    ENVIRONMENT_VARIABLE = "SMARTSHEET_AI_SUBMISSION_KEY_COLUMN_TITLE"

    def __init__(self, *, environment: dict[str, str] | None = None):
        if environment is None:
            load_dotenv()
        self.environment = environment if environment is not None else os.environ

    def resolve(self, value: Any = None) -> SmartsheetSubmissionKeyConfiguration:
        candidate = self.environment.get(self.ENVIRONMENT_VARIABLE) if value is None else value
        if not isinstance(candidate, str) or not candidate.strip():
            return SmartsheetSubmissionKeyConfiguration()
        title = candidate.strip()
        if len(title) > 100 or any(character in title for character in "\r\n\x00"):
            return SmartsheetSubmissionKeyConfiguration(status="submission_key_configuration_invalid")
        return SmartsheetSubmissionKeyConfiguration(title, True, True, "configured")
