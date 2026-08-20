from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class FilenameCompositionPolicy:
    separator: str = "_"
    extension: str = ".pdf"
    component_order: tuple[str, ...] = (
        "person_name", "payer_token", "service_token", "form_type_token",
        "workflow_type_token", "date_token",
    )
    optional_components: tuple[str, ...] = ("service_token", "form_type_token")


@dataclass(frozen=True)
class ReferenceFilenameResult:
    success: bool
    filename: str | None = field(repr=False)
    review_required: bool
    status: str


class ReferenceFilenameBuilderService:
    """Compose resolved filename components without logging their values."""
    COMPONENTS = {
        "person_name", "payer_token", "service_token", "form_type_token",
        "workflow_type_token", "date_token",
    }

    def build(
        self, *, person_name: Any, payer_token: Any, service_token: Any = None,
        form_type_token: Any = None, workflow_type_token: Any = None,
        date_token: Any, policy: FilenameCompositionPolicy | None = None,
        document_type_token: Any = None,
    ) -> ReferenceFilenameResult:
        if not isinstance(policy, FilenameCompositionPolicy):
            return self._failure("composition_policy_unconfigured")
        if not policy.separator or any(character in policy.separator for character in "\\/\r\n") or not policy.extension.startswith("."):
            return self._failure("invalid_composition_policy")
        if set(policy.component_order) != self.COMPONENTS:
            return self._failure("invalid_composition_policy")
        optional = set(policy.optional_components)
        if not optional.issubset(self.COMPONENTS):
            return self._failure("invalid_composition_policy")
        workflow_value = workflow_type_token if workflow_type_token is not None else document_type_token
        values = {name: str(value or "").strip() for name, value in {
            "person_name": person_name, "payer_token": payer_token, "service_token": service_token,
            "form_type_token": form_type_token, "workflow_type_token": workflow_value,
            "date_token": date_token,
        }.items()}
        if any(not values[name] for name in self.COMPONENTS - optional):
            return self._failure("component_unresolved")
        if any(any(character in value for character in "\\/\r\n") for value in values.values() if value):
            return self._failure("component_invalid")
        filename = policy.separator.join(
            values[name] for name in policy.component_order if values[name]
        ) + policy.extension
        return ReferenceFilenameResult(True, filename, False, "composed")

    @staticmethod
    def _failure(status: str) -> ReferenceFilenameResult:
        return ReferenceFilenameResult(False, None, True, status)
