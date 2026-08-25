from dataclasses import dataclass

from src.models.smartsheet_mapping import (
    SmartsheetColumnPolicy,
)


@dataclass(frozen=True)
class SmartsheetMappingPolicyResult:
    policy_count: int
    policies: tuple[SmartsheetColumnPolicy, ...]
    success: bool
    status: str


class SmartsheetMappingPolicyService:
    """
    Provides explicitly approved Smartsheet mapping policies for the
    shared document-processing platform.

    The current approved value mappings are a Phase 1 configuration,
    not a fixed final schema. New fields are added only through this
    explicit configuration boundary after destination approval.

    No payer-, service-code-, modifier-, subtype-, or fixture-specific
    mapping is inferred.

    Production policies must be registered explicitly by an approved
    configuration boundary.
    """

    def __init__(
        self,
        *,
        policies_by_document_type=None,
        default_policies=None,
    ) -> None:
        self._policies = {}
        self._default_policies = None

        if policies_by_document_type is not None:
            self._load(
                policies_by_document_type
            )

        if default_policies is not None:
            self._default_policies = self._normalize_policies(
                default_policies
            )

    def get(
        self,
        *,
        document_type=None,
        document_family=None,
        document_subtype=None,
    ) -> SmartsheetMappingPolicyResult:
        family = self._normalize_key(document_family)
        subtype = self._normalize_key(document_subtype)
        legacy_type = self._normalize_key(document_type)

        candidate_keys = []
        if family and subtype:
            candidate_keys.append(f"{family}/{subtype}")
        if family:
            candidate_keys.append(family)
        if legacy_type:
            candidate_keys.append(legacy_type)

        if not candidate_keys and self._default_policies is None:
            return self._failure("invalid_document_type")

        policies = None
        for key in self._deduplicate(candidate_keys):
            policies = self._policies.get(key)
            if policies is not None:
                break

        if policies is None:
            policies = self._default_policies

        if policies is None:
            return self._failure(
                "policy_not_configured"
            )

        if not policies:
            return self._failure(
                "empty_policy"
            )

        return SmartsheetMappingPolicyResult(
            policy_count=len(
                policies
            ),
            policies=policies,
            success=True,
            status="ready",
        )

    def _load(
        self,
        policies_by_document_type,
    ) -> None:
        if not isinstance(
            policies_by_document_type,
            dict,
        ):
            raise ValueError(
                "Mapping policy configuration must be a dictionary."
            )

        for document_type, policies in (
            policies_by_document_type.items()
        ):
            normalized_type = self._normalize_key(
                document_type
            )

            if not normalized_type:
                raise ValueError(
                    "Mapping policy document type is invalid."
                )

            if not isinstance(
                policies,
                (list, tuple),
            ):
                raise ValueError(
                    "Mapping policies must be a list or tuple."
                )

            self._policies[
                normalized_type
            ] = self._normalize_policies(
                policies
            )

    def _normalize_policies(
        self,
        policies,
    ) -> tuple[SmartsheetColumnPolicy, ...]:
        if not isinstance(policies, (list, tuple)):
            raise ValueError("Mapping policies must be a list or tuple.")

        normalized_policies = []
        seen_source_fields = set()
        seen_column_names = set()

        for policy in policies:
            if not isinstance(policy, SmartsheetColumnPolicy):
                raise ValueError("Mapping policy entry is invalid.")

            source_field = self._normalize_key(policy.source_field)
            column_name = self._normalize_column_name(policy.column_name)
            confidence_column_name = (
                self._normalize_column_name(policy.confidence_column_name)
                if policy.confidence_column_name is not None
                else ""
            )

            if not source_field:
                raise ValueError("Mapping policy source field is invalid.")
            if not column_name:
                raise ValueError("Mapping policy column name is invalid.")
            if source_field in seen_source_fields:
                raise ValueError("Duplicate mapping policy source field.")
            if column_name in seen_column_names:
                raise ValueError("Duplicate mapping policy column name.")
            if (
                confidence_column_name
                and confidence_column_name in seen_column_names
            ):
                raise ValueError(
                    "Duplicate mapping policy confidence column name."
                )

            seen_source_fields.add(source_field)
            seen_column_names.add(column_name)
            if confidence_column_name:
                seen_column_names.add(confidence_column_name)

            normalized_policies.append(
                SmartsheetColumnPolicy(
                    source_field=source_field,
                    column_name=column_name,
                    required=bool(policy.required),
                    review_only=bool(policy.review_only),
                    confidence_column_name=confidence_column_name or None,
                    confidence_column_supports_text=bool(
                        policy.confidence_column_supports_text
                    ),
                )
            )

        return tuple(normalized_policies)

    @staticmethod
    def _deduplicate(values):
        return tuple(dict.fromkeys(values))

    @staticmethod
    def _normalize_key(
        value,
    ) -> str:
        return str(
            value
            or ""
        ).strip().lower()

    @staticmethod
    def _normalize_column_name(
        value,
    ) -> str:
        return str(
            value
            or ""
        ).strip()

    @staticmethod
    def _failure(
        status: str,
    ) -> SmartsheetMappingPolicyResult:
        return SmartsheetMappingPolicyResult(
            policy_count=0,
            policies=(),
            success=False,
            status=status,
        )
