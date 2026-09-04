from __future__ import annotations

from dataclasses import dataclass

from src.models.document_processor_business_context import (
    DOCUMENT_PROCESSOR_BUSINESS_CONTEXT,
)


@dataclass(frozen=True)
class DocumentFamilyDefinition:
    """One reusable document-family classification definition."""

    family: str
    subtypes: frozenset[str]
    legacy_routes: tuple[tuple[str, str], ...] = ()
    neutral_rule: bool = False

    def legacy_route(self, subtype: str) -> str:
        routes = dict(self.legacy_routes)
        return routes.get(subtype, self.family)


class DocumentTaxonomyRegistry:
    """Authoritative family/subtype compatibility and legacy routing."""

    UNKNOWN = "unknown"
    DEFINITIONS = tuple(
        DocumentFamilyDefinition(
            family=item.family,
            subtypes=frozenset(item.subtypes),
            legacy_routes=item.legacy_routes,
            neutral_rule=item.neutral_rule,
        )
        for item in DOCUMENT_PROCESSOR_BUSINESS_CONTEXT.document_taxonomy
    )
    _BY_FAMILY = {definition.family: definition for definition in DEFINITIONS}

    @classmethod
    def families(cls) -> tuple[str, ...]:
        return tuple(definition.family for definition in cls.DEFINITIONS)

    @classmethod
    def subtypes(cls) -> tuple[str, ...]:
        return tuple(sorted({
            subtype
            for definition in cls.DEFINITIONS
            for subtype in definition.subtypes
        }))

    @classmethod
    def definition(cls, family: str) -> DocumentFamilyDefinition | None:
        return cls._BY_FAMILY.get(cls.normalize_label(family))

    @classmethod
    def normalize_family(cls, value) -> str:
        normalized = cls.normalize_label(value)
        return normalized if normalized in cls._BY_FAMILY else cls.UNKNOWN

    @classmethod
    def normalize_subtype(cls, family, subtype) -> str:
        definition = cls.definition(cls.normalize_family(family))
        normalized = cls.normalize_label(subtype)
        if definition is None or normalized not in definition.subtypes:
            return cls.UNKNOWN
        return normalized

    @classmethod
    def legacy_route(cls, family, subtype) -> str:
        normalized_family = cls.normalize_family(family)
        definition = cls.definition(normalized_family)
        if definition is None:
            return cls.UNKNOWN
        return definition.legacy_route(
            cls.normalize_subtype(normalized_family, subtype)
        )

    @staticmethod
    def normalize_label(value) -> str:
        return str(value or "unknown").strip().lower() or "unknown"
