from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class FilenameCompositionPolicy:
    separator: str = "_"
    extension: str = ".PDF"
    component_order: tuple[str, ...] = (
        "person_name", "payer_token", "service_token",
        "document_type_token", "date_token",
    )
    optional_components: tuple[str, ...] = ("service_token",)


@dataclass(frozen=True)
class ReferenceFilenameResult:
    success: bool
    filename: str | None = field(repr=False)
    review_required: bool
    status: str


class ReferenceFilenameBuilderService:
    """Compose resolved or fixed-placeholder components without logging values."""

    COMPONENTS = {
        "person_name", "payer_token", "service_token",
        "document_type_token", "date_token",
    }
    WINDOWS_INVALID_CHARACTERS = frozenset('<>:"/\\|?*')
    MAX_COMPONENT_UTF16_UNITS = 255

    def build(
        self, *, person_name: Any, payer_token: Any,
        service_token: Any = None, document_type_token: Any,
        date_token: Any, policy: FilenameCompositionPolicy | None = None,
    ) -> ReferenceFilenameResult:
        if not isinstance(policy, FilenameCompositionPolicy):
            return self._failure("composition_policy_unconfigured")
        if (
            not policy.separator
            or self._invalid_text(policy.separator)
            or not policy.extension.startswith(".")
        ):
            return self._failure("invalid_composition_policy")
        if set(policy.component_order) != self.COMPONENTS:
            return self._failure("invalid_composition_policy")
        optional = set(policy.optional_components)
        if not optional.issubset(self.COMPONENTS):
            return self._failure("invalid_composition_policy")
        values = {
            name: str(value or "").strip()
            for name, value in {
                "person_name": person_name,
                "payer_token": payer_token,
                "service_token": service_token,
                "document_type_token": document_type_token,
                "date_token": date_token,
            }.items()
        }
        if any(not values[name] for name in self.COMPONENTS - optional):
            return self._failure("component_unresolved")
        if any(self._invalid_text(value) for value in values.values() if value):
            return self._failure("component_invalid")
        filename = policy.separator.join(
            values[name] for name in policy.component_order if values[name]
        ) + policy.extension
        if (
            filename.endswith((" ", "."))
            or len(filename.encode("utf-16-le")) // 2
            > self.MAX_COMPONENT_UTF16_UNITS
        ):
            return self._failure("component_invalid")
        return ReferenceFilenameResult(True, filename, False, "composed")

    @classmethod
    def _invalid_text(cls, value: str) -> bool:
        return any(
            character in cls.WINDOWS_INVALID_CHARACTERS or ord(character) < 32
            for character in value
        )

    @staticmethod
    def _failure(status: str) -> ReferenceFilenameResult:
        return ReferenceFilenameResult(False, None, True, status)
