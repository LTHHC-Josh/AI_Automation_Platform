from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class FilenameCompositionPolicy:
    separator: str
    extension: str = ".pdf"
    component_order: tuple[str, ...] = ("person_name", "payer_token", "service_token", "document_type_token", "date_token")


@dataclass(frozen=True)
class ReferenceFilenameResult:
    success: bool
    filename: str | None
    review_required: bool
    status: str


class ReferenceFilenameBuilderService:
    """Compose only resolved components under an explicitly supplied policy."""
    COMPONENTS = {"person_name", "payer_token", "service_token", "document_type_token", "date_token"}

    def build(self, *, person_name: Any, payer_token: Any, service_token: Any, document_type_token: Any, date_token: Any, policy: FilenameCompositionPolicy | None = None) -> ReferenceFilenameResult:
        if not isinstance(policy, FilenameCompositionPolicy):
            return ReferenceFilenameResult(False, None, True, "composition_policy_unconfigured")
        if not policy.separator or any(character in policy.separator for character in "\\/\r\n") or not policy.extension.startswith("."):
            return ReferenceFilenameResult(False, None, True, "invalid_composition_policy")
        values = {name: str(value or "").strip() for name, value in {
            "person_name": person_name, "payer_token": payer_token, "service_token": service_token,
            "document_type_token": document_type_token, "date_token": date_token,
        }.items()}
        if set(policy.component_order) != self.COMPONENTS or any(not values[name] for name in policy.component_order):
            return ReferenceFilenameResult(False, None, True, "component_unresolved")
        if any(any(character in values[name] for character in "\\/\r\n") for name in policy.component_order):
            return ReferenceFilenameResult(False, None, True, "component_invalid")
        filename = policy.separator.join(values[name] for name in policy.component_order) + policy.extension
        return ReferenceFilenameResult(True, filename, False, "composed")
