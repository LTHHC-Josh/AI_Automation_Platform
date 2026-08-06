from __future__ import annotations

import re
from datetime import datetime
from typing import Any

from src.models.document import (
    AuthorizationServiceLine,
    Document,
)


class EvidenceValidationService:
    """
    Performs deterministic structural validation of extracted evidence.

    This service does not apply payer-specific or LTHHC business rules.

    Responsibilities:

    - normalize clear dates,
    - deduplicate structural lists,
    - reject unsupported checkbox conclusions,
    - reject unsupported approved-visit conclusions,
    - validate structured identifiers against source evidence,
    - validate service-code and modifier structure,
    - validate optional authorization service-line evidence,
    - identify unresolved modifier-to-service-line relationships,
    - downgrade or clear unsupported fields,
    - preserve original source_text.
    """

    DATE_FIELDS = {
        "start_date",
        "end_date",
        "member_dob",
    }

    LIST_FIELDS = {
        "service_codes",
        "authorized_units",
    }

    REQUIRED_SOURCE_FIELDS = {
        "member_id",
        "authorization_number",
        "authorization_status",
        "request_type",
        "service_code",
        "service_codes",
        "modifier",
        "approved_visits",
        "start_date",
        "end_date",
        "member_dob",
        "provider_npi",
        "diagnosis_code",
    }

    EXACT_ALPHANUMERIC_FIELDS = {
        "member_id",
        "authorization_number",
        "provider_npi",
    }

    EXACT_TOKEN_FIELDS = {
        "service_code",
        "service_codes",
        "modifier",
        "diagnosis_code",
    }

    SELECTION_MARKERS = (
        "[x]",
        "[ x ]",
        "\u2612",
        "checked",
        "selected",
        "selection:",
    )

    APPROVAL_TERMS = (
        "approved",
        "authorized",
        "authorization",
        "auth status",
        "line status",
    )

    REQUEST_TERMS = (
        "requested",
        "request",
        "number of visits",
    )

    MODIFIER_PATTERN = re.compile(
        r"^[A-Z0-9]{2}$"
    )

    DATE_PATTERN = re.compile(
        r"\b\d{1,2}[/-]\d{1,2}[/-]\d{4}\b"
        r"|\b\d{4}-\d{2}-\d{2}\b"
    )

    DATE_FORMATS = (
        "%Y-%m-%d",
        "%m/%d/%Y",
        "%m-%d-%Y",
    )

    TOP_LEVEL_MAX_MODEL_CONFIDENCE = 0.95
    SERVICE_LINE_LOW_CONFIDENCE_THRESHOLD = 0.85
    SERVICE_LINE_MAX_MODEL_CONFIDENCE = 0.95
    SERVICE_LINE_UNSUPPORTED_CONFIDENCE = 0.50

    SERVICE_LINE_MODIFIER_RELATIONSHIP_ACTION = (
        "Service-line modifier relationship requires verification"
    )

    def validate(
        self,
        document: Document,
    ) -> list[str]:
        """
        Validate and normalize field and service-line evidence in place.

        Returns:
            Unique validation actions requiring reporting or review.
        """

        actions: list[str] = []

        self._cap_top_level_model_confidences(
            document
        )

        self._validate_required_source_evidence(
            document=document,
            actions=actions,
        )

        for field_name in self.DATE_FIELDS:
            self._normalize_date_field(
                document=document,
                field_name=field_name,
                actions=actions,
            )

        for field_name in self.LIST_FIELDS:
            self._deduplicate_list_field(
                document=document,
                field_name=field_name,
            )

        self._validate_structured_source_support(
            document=document,
            actions=actions,
        )

        self._validate_service_code_consistency(
            document=document,
            actions=actions,
        )

        self._validate_request_type(
            document=document,
            actions=actions,
        )

        self._validate_approved_visits(
            document=document,
            actions=actions,
        )

        self._validate_modifier(
            document=document,
            actions=actions,
        )

        self._validate_service_lines(
            document=document,
            actions=actions,
        )

        self._reconcile_authorized_units_from_service_lines(
            document=document,
            actions=actions,
        )

        self._validate_service_line_modifier_relationship(
            document=document,
            actions=actions,
        )

        self._synchronize_flat_fields(
            document
        )

        return self._remove_duplicates(
            actions
        )

    def _cap_top_level_model_confidences(
        self,
        document: Document,
    ) -> None:
        """
        Normalize confidence for top-level extracted claims.

        A model-reported confidence of 1.0 is capped because model
        certainty is not equivalent to deterministic verification.

        Empty values do not represent extracted claims and retain zero
        confidence. Existing lower confidence is preserved.
        """

        for evidence in document.field_evidence.values():
            if not isinstance(
                evidence,
                dict,
            ):
                continue

            value = evidence.get(
                "value"
            )

            if self._is_empty_value(
                value
            ):
                evidence["confidence"] = 0.0
                continue

            confidence = self._normalize_confidence(
                evidence.get(
                    "confidence",
                    0.0,
                )
            )

            evidence["confidence"] = min(
                confidence,
                self.TOP_LEVEL_MAX_MODEL_CONFIDENCE,
            )

    def _validate_required_source_evidence(
        self,
        document: Document,
        actions: list[str],
    ) -> None:
        """
        Clear structured values that have no claimed source evidence.
        """

        for field_name in self.REQUIRED_SOURCE_FIELDS:
            evidence = document.field_evidence.get(
                field_name
            )

            if not isinstance(
                evidence,
                dict,
            ):
                continue

            value = evidence.get(
                "value"
            )

            if value is None:
                continue

            source_text = str(
                evidence.get(
                    "source_text",
                    "",
                )
                or ""
            ).strip()

            if source_text:
                continue

            self._invalidate_field(
                document=document,
                field_name=field_name,
                reason=(
                    f"{field_name} has no source evidence"
                ),
                actions=actions,
            )

    def _normalize_date_field(
        self,
        document: Document,
        field_name: str,
        actions: list[str],
    ) -> None:
        evidence = document.field_evidence.get(
            field_name
        )

        if not isinstance(
            evidence,
            dict,
        ):
            return

        value = evidence.get(
            "value"
        )

        if value is None:
            return

        if isinstance(
            value,
            list,
        ):
            self._invalidate_field(
                document=document,
                field_name=field_name,
                reason=(
                    f"{field_name} contains multiple date values"
                ),
                actions=actions,
            )
            return

        normalized_date = self._parse_date(
            value
        )

        if normalized_date is None:
            self._invalidate_field(
                document=document,
                field_name=field_name,
                reason=(
                    f"{field_name} could not be normalized"
                ),
                actions=actions,
            )
            return

        source_text = str(
            evidence.get(
                "source_text",
                "",
            )
            or ""
        )

        if not self._source_supports_date(
            normalized_date=normalized_date,
            source_text=source_text,
        ):
            self._invalidate_field(
                document=document,
                field_name=field_name,
                reason=(
                    f"{field_name} is not supported by its source evidence"
                ),
                actions=actions,
            )
            return

        evidence["value"] = normalized_date

    def _validate_structured_source_support(
        self,
        document: Document,
        actions: list[str],
    ) -> None:
        for field_name in self.EXACT_ALPHANUMERIC_FIELDS:
            self._validate_alphanumeric_field(
                document=document,
                field_name=field_name,
                actions=actions,
            )

        for field_name in self.EXACT_TOKEN_FIELDS:
            self._validate_token_field(
                document=document,
                field_name=field_name,
                actions=actions,
            )

    def _validate_alphanumeric_field(
        self,
        document: Document,
        field_name: str,
        actions: list[str],
    ) -> None:
        evidence = document.field_evidence.get(
            field_name
        )

        if not isinstance(
            evidence,
            dict,
        ):
            return

        value = evidence.get(
            "value"
        )

        if value is None:
            return

        source_text = evidence.get(
            "source_text",
            "",
        )

        normalized_value = self._normalize_alphanumeric(
            value
        )

        normalized_source = self._normalize_alphanumeric(
            source_text
        )

        if (
            normalized_value
            and normalized_value in normalized_source
        ):
            return

        self._invalidate_field(
            document=document,
            field_name=field_name,
            reason=(
                f"{field_name} is not supported by its source evidence"
            ),
            actions=actions,
        )

    def _validate_token_field(
        self,
        document: Document,
        field_name: str,
        actions: list[str],
    ) -> None:
        evidence = document.field_evidence.get(
            field_name
        )

        if not isinstance(
            evidence,
            dict,
        ):
            return

        value = evidence.get(
            "value"
        )

        if value is None:
            return

        source_tokens = self._tokenize(
            evidence.get(
                "source_text",
                "",
            )
        )

        values = (
            value
            if isinstance(
                value,
                list,
            )
            else [value]
        )

        unsupported_values = [
            item
            for item in values
            if str(item).strip().upper()
            not in source_tokens
        ]

        if not unsupported_values:
            return

        self._invalidate_field(
            document=document,
            field_name=field_name,
            reason=(
                f"{field_name} is not supported by its source evidence"
            ),
            actions=actions,
        )

    def _deduplicate_list_field(
        self,
        document: Document,
        field_name: str,
    ) -> None:
        evidence = document.field_evidence.get(
            field_name
        )

        if not isinstance(
            evidence,
            dict,
        ):
            return

        value = evidence.get(
            "value"
        )

        if value is None:
            return

        values = (
            value
            if isinstance(
                value,
                list,
            )
            else [value]
        )

        unique_values: list[Any] = []

        for item in values:
            normalized_item = (
                item.strip()
                if isinstance(
                    item,
                    str,
                )
                else item
            )

            if self._is_empty_value(
                normalized_item
            ):
                continue

            if normalized_item not in unique_values:
                unique_values.append(
                    normalized_item
                )

        evidence["value"] = (
            unique_values
            if unique_values
            else None
        )

        if not unique_values:
            evidence["confidence"] = 0.0

    def _validate_service_code_consistency(
        self,
        document: Document,
        actions: list[str],
    ) -> None:
        single_evidence = document.field_evidence.get(
            "service_code"
        )

        multiple_evidence = document.field_evidence.get(
            "service_codes"
        )

        if not isinstance(
            single_evidence,
            dict,
        ):
            return

        if not isinstance(
            multiple_evidence,
            dict,
        ):
            return

        single_value = single_evidence.get(
            "value"
        )

        multiple_values = multiple_evidence.get(
            "value"
        )

        if (
            single_value is None
            or not isinstance(
                multiple_values,
                list,
            )
        ):
            return

        if single_value in multiple_values:
            return

        self._downgrade_field(
            document=document,
            field_name="service_code",
            confidence=0.50,
        )

        actions.append(
            "Service code fields conflict"
        )

    def _validate_request_type(
        self,
        document: Document,
        actions: list[str],
    ) -> None:
        evidence = document.field_evidence.get(
            "request_type"
        )

        if not isinstance(
            evidence,
            dict,
        ):
            return

        value = evidence.get(
            "value"
        )

        if value is None:
            return

        source_text = self._normalized_text(
            evidence.get(
                "source_text"
            )
        )

        has_selection_marker = any(
            marker in source_text
            for marker in self.SELECTION_MARKERS
        )

        if has_selection_marker:
            return

        self._invalidate_field(
            document=document,
            field_name="request_type",
            reason=(
                "Request type requires checkbox or selection verification"
            ),
            actions=actions,
        )

    def _validate_approved_visits(
        self,
        document: Document,
        actions: list[str],
    ) -> None:
        evidence = document.field_evidence.get(
            "approved_visits"
        )

        if not isinstance(
            evidence,
            dict,
        ):
            return

        value = evidence.get(
            "value"
        )

        if value is None:
            return

        source_text = self._normalized_text(
            evidence.get(
                "source_text"
            )
        )

        has_approval_context = any(
            term in source_text
            for term in self.APPROVAL_TERMS
        )

        has_request_context = any(
            term in source_text
            for term in self.REQUEST_TERMS
        )

        if (
            has_approval_context
            and not has_request_context
        ):
            return

        self._invalidate_field(
            document=document,
            field_name="approved_visits",
            reason=(
                "Approved visits are not supported by clear approval evidence"
            ),
            actions=actions,
        )

    def _validate_modifier(
        self,
        document: Document,
        actions: list[str],
    ) -> None:
        evidence = document.field_evidence.get(
            "modifier"
        )

        if not isinstance(
            evidence,
            dict,
        ):
            return

        value = evidence.get(
            "value"
        )

        if value is None:
            return

        if isinstance(
            value,
            list,
        ):
            normalized_modifiers = self._deduplicate_strings(
                value
            )

            invalid_modifiers = [
                modifier
                for modifier in normalized_modifiers
                if not self.MODIFIER_PATTERN.fullmatch(
                    modifier
                )
            ]

            if invalid_modifiers:
                self._invalidate_field(
                    document=document,
                    field_name="modifier",
                    reason=(
                        "Modifier evidence is structurally invalid"
                    ),
                    actions=actions,
                )
                return

            evidence["value"] = normalized_modifiers
            return

        normalized_modifier = str(
            value
        ).strip().upper()

        if not self.MODIFIER_PATTERN.fullmatch(
            normalized_modifier
        ):
            self._invalidate_field(
                document=document,
                field_name="modifier",
                reason=(
                    "Modifier evidence is structurally invalid"
                ),
                actions=actions,
            )
            return

        evidence["value"] = normalized_modifier

    def _validate_service_lines(
        self,
        document: Document,
        actions: list[str],
    ) -> None:
        """
        Validate optional service-line rows without interpreting meaning.

        Unsupported values are cleared from the row. Rows with no
        remaining structured values are removed.
        """

        validated_lines: list[AuthorizationServiceLine] = []

        for line_number, service_line in enumerate(
            document.service_lines,
            start=1,
        ):
            if not isinstance(
                service_line,
                AuthorizationServiceLine,
            ):
                actions.append(
                    f"Service line {line_number} has invalid structure"
                )
                continue

            source_text = str(
                service_line.source_text
                or ""
            ).strip()

            service_line.source_text = source_text
            service_line.confidence = self._normalize_confidence(
                service_line.confidence
            )

            if not source_text:
                actions.append(
                    f"Service line {line_number} has no source evidence"
                )
                continue

            if (
                service_line.confidence
                >= 1.0
            ):
                service_line.confidence = (
                    self.SERVICE_LINE_MAX_MODEL_CONFIDENCE
                )

                actions.append(
                    f"Service line {line_number} confidence "
                    "requires deterministic verification"
                )

            self._validate_service_line_code(
                service_line=service_line,
                line_number=line_number,
                actions=actions,
            )

            self._validate_service_line_modifier(
                service_line=service_line,
                line_number=line_number,
                actions=actions,
            )

            self._validate_service_line_quantity(
                service_line=service_line,
                line_number=line_number,
                actions=actions,
            )

            service_line.start_date = (
                self._validate_service_line_date(
                    value=service_line.start_date,
                    field_name="start date",
                    source_text=source_text,
                    line_number=line_number,
                    service_line=service_line,
                    actions=actions,
                )
            )

            service_line.end_date = (
                self._validate_service_line_date(
                    value=service_line.end_date,
                    field_name="end date",
                    source_text=source_text,
                    line_number=line_number,
                    service_line=service_line,
                    actions=actions,
                )
            )

            self._validate_service_line_status(
                service_line=service_line,
                line_number=line_number,
                actions=actions,
            )

            if (
                service_line.confidence
                < self.SERVICE_LINE_LOW_CONFIDENCE_THRESHOLD
            ):
                actions.append(
                    f"Service line {line_number} has low confidence"
                )

            if not self._service_line_has_value(
                service_line
            ):
                actions.append(
                    f"Service line {line_number} has no supported values"
                )
                continue

            validated_lines.append(
                service_line
            )

        document.service_lines = self._deduplicate_service_lines(
            service_lines=validated_lines,
            actions=actions,
        )

    def _reconcile_authorized_units_from_service_lines(
        self,
        document: Document,
        actions: list[str],
    ) -> None:
        """
        Reconcile flat authorized units from validated row evidence.

        This uses only quantities preserved on service lines within the
        same independently validated candidate. It never combines
        extraction attempts and never interprets quantity meaning.
        """

        supported_lines = [
            service_line
            for service_line in document.service_lines
            if not self._is_empty_value(
                service_line.quantity
            )
        ]

        if not supported_lines:
            return

        row_quantities: list[Any] = []

        for service_line in supported_lines:
            quantity = service_line.quantity

            if quantity not in row_quantities:
                row_quantities.append(
                    quantity
                )

        evidence = document.field_evidence.get(
            "authorized_units"
        )

        if not isinstance(
            evidence,
            dict,
        ):
            return

        existing_value = evidence.get(
            "value"
        )

        if self._is_empty_value(
            existing_value
        ):
            return

        existing_values = (
            existing_value
            if isinstance(
                existing_value,
                list,
            )
            else (
                []
                if self._is_empty_value(
                    existing_value
                )
                else [existing_value]
            )
        )

        normalized_existing = {
            str(value).strip()
            for value in existing_values
            if not self._is_empty_value(
                value
            )
        }

        normalized_rows = {
            str(value).strip()
            for value in row_quantities
            if not self._is_empty_value(
                value
            )
        }

        if normalized_existing == normalized_rows:
            return

        combined_source_parts: list[str] = []

        original_source = str(
            evidence.get(
                "source_text",
                "",
            )
            or ""
        ).strip()

        if original_source:
            combined_source_parts.append(
                original_source
            )

        for service_line in supported_lines:
            row_source = str(
                service_line.source_text
                or ""
            ).strip()

            if (
                row_source
                and row_source not in combined_source_parts
            ):
                combined_source_parts.append(
                    row_source
                )

        supporting_confidences = [
            self._normalize_confidence(
                service_line.confidence
            )
            for service_line in supported_lines
        ]

        existing_confidence = self._normalize_confidence(
            evidence.get(
                "confidence",
                0.0,
            )
        )

        if existing_confidence > 0:
            supporting_confidences.append(
                existing_confidence
            )

        evidence["value"] = row_quantities
        evidence["confidence"] = (
            min(
                supporting_confidences
            )
            if supporting_confidences
            else 0.0
        )
        evidence["source_text"] = "\n".join(
            combined_source_parts
        )

        actions.append(
            "Authorized units were reconciled from "
            "supported service-line evidence"
        )

    def _validate_service_line_modifier_relationship(
        self,
        document: Document,
        actions: list[str],
    ) -> None:
        """
        Require review when a supported top-level modifier cannot be
        connected to a validated service line.

        This method never copies a top-level modifier into a row.
        """

        modifier_evidence = document.field_evidence.get(
            "modifier"
        )

        if not isinstance(
            modifier_evidence,
            dict,
        ):
            return

        modifier_value = modifier_evidence.get(
            "value"
        )

        top_level_modifiers = self._normalize_modifier_values(
            modifier_value
        )

        if not top_level_modifiers:
            return

        row_modifiers = {
            str(
                service_line.modifier
            ).strip().upper()
            for service_line in document.service_lines
            if service_line.modifier
        }

        unresolved_modifiers = (
            top_level_modifiers
            - row_modifiers
        )

        if not unresolved_modifiers:
            return

        actions.append(
            self.SERVICE_LINE_MODIFIER_RELATIONSHIP_ACTION
        )

    def _validate_service_line_code(
        self,
        service_line: AuthorizationServiceLine,
        line_number: int,
        actions: list[str],
    ) -> None:
        if service_line.service_code is None:
            return

        normalized_code = str(
            service_line.service_code
        ).strip().upper()

        source_tokens = self._tokenize(
            service_line.source_text
        )

        if (
            normalized_code
            and normalized_code in source_tokens
        ):
            service_line.service_code = normalized_code
            return

        service_line.service_code = None

        self._downgrade_service_line(
            service_line
        )

        actions.append(
            f"Service line {line_number} service code "
            "is not supported by its source evidence"
        )

    def _validate_service_line_modifier(
        self,
        service_line: AuthorizationServiceLine,
        line_number: int,
        actions: list[str],
    ) -> None:
        if service_line.modifier is None:
            return

        normalized_modifier = str(
            service_line.modifier
        ).strip().upper()

        source_tokens = self._tokenize(
            service_line.source_text
        )

        if not self.MODIFIER_PATTERN.fullmatch(
            normalized_modifier
        ):
            service_line.modifier = None

            self._downgrade_service_line(
                service_line
            )

            actions.append(
                f"Service line {line_number} modifier "
                "is structurally invalid"
            )
            return

        if normalized_modifier not in source_tokens:
            service_line.modifier = None

            self._downgrade_service_line(
                service_line
            )

            actions.append(
                f"Service line {line_number} modifier "
                "is not supported by its source evidence"
            )
            return

        service_line.modifier = normalized_modifier

    def _validate_service_line_quantity(
        self,
        service_line: AuthorizationServiceLine,
        line_number: int,
        actions: list[str],
    ) -> None:
        if service_line.quantity is None:
            return

        normalized_quantity = str(
            service_line.quantity
        ).strip()

        if not normalized_quantity:
            service_line.quantity = None
            return

        source_tokens = self._tokenize(
            service_line.source_text
        )

        if normalized_quantity.upper() in source_tokens:
            service_line.quantity = normalized_quantity
            return

        service_line.quantity = None

        self._downgrade_service_line(
            service_line
        )

        actions.append(
            f"Service line {line_number} quantity "
            "is not supported by its source evidence"
        )

    def _validate_service_line_date(
        self,
        value: str | None,
        field_name: str,
        source_text: str,
        line_number: int,
        service_line: AuthorizationServiceLine,
        actions: list[str],
    ) -> str | None:
        if value is None:
            return None

        normalized_date = self._parse_date(
            value
        )

        if normalized_date is None:
            self._downgrade_service_line(
                service_line
            )

            actions.append(
                f"Service line {line_number} {field_name} "
                "could not be normalized"
            )

            return None

        if not self._source_supports_date(
            normalized_date=normalized_date,
            source_text=source_text,
        ):
            self._downgrade_service_line(
                service_line
            )

            actions.append(
                f"Service line {line_number} {field_name} "
                "is not supported by its source evidence"
            )

            return None

        return normalized_date

    def _validate_service_line_status(
        self,
        service_line: AuthorizationServiceLine,
        line_number: int,
        actions: list[str],
    ) -> None:
        if service_line.status is None:
            return

        normalized_status = str(
            service_line.status
        ).strip()

        normalized_source = self._normalized_text(
            service_line.source_text
        )

        if (
            normalized_status
            and normalized_status.lower() in normalized_source
        ):
            service_line.status = normalized_status
            return

        service_line.status = None

        self._downgrade_service_line(
            service_line
        )

        actions.append(
            f"Service line {line_number} status "
            "is not supported by its source evidence"
        )

    def _service_line_has_value(
        self,
        service_line: AuthorizationServiceLine,
    ) -> bool:
        return any(
            value is not None
            for value in (
                service_line.service_code,
                service_line.modifier,
                service_line.quantity,
                service_line.start_date,
                service_line.end_date,
                service_line.status,
            )
        )

    def _deduplicate_service_lines(
        self,
        service_lines: list[AuthorizationServiceLine],
        actions: list[str],
    ) -> list[AuthorizationServiceLine]:
        unique_lines: list[AuthorizationServiceLine] = []
        seen_keys: set[tuple[Any, ...]] = set()

        for service_line in service_lines:
            line_key = (
                service_line.service_code,
                service_line.modifier,
                service_line.quantity,
                service_line.start_date,
                service_line.end_date,
                service_line.status,
            )

            if line_key in seen_keys:
                actions.append(
                    "Duplicate service-line evidence was removed"
                )
                continue

            seen_keys.add(
                line_key
            )

            unique_lines.append(
                service_line
            )

        return unique_lines

    def _downgrade_service_line(
        self,
        service_line: AuthorizationServiceLine,
    ) -> None:
        service_line.confidence = min(
            self._normalize_confidence(
                service_line.confidence
            ),
            self.SERVICE_LINE_UNSUPPORTED_CONFIDENCE,
        )

    def _source_supports_date(
        self,
        normalized_date: str,
        source_text: str,
    ) -> bool:
        for date_text in self.DATE_PATTERN.findall(
            source_text
        ):
            parsed_date = self._parse_date(
                date_text
            )

            if parsed_date == normalized_date:
                return True

        return False

    def _invalidate_field(
        self,
        document: Document,
        field_name: str,
        reason: str,
        actions: list[str],
    ) -> None:
        evidence = document.field_evidence.get(
            field_name
        )

        if not isinstance(
            evidence,
            dict,
        ):
            return

        evidence["value"] = None
        evidence["confidence"] = 0.0

        actions.append(
            reason
        )

    def _downgrade_field(
        self,
        document: Document,
        field_name: str,
        confidence: float,
    ) -> None:
        evidence = document.field_evidence.get(
            field_name
        )

        if not isinstance(
            evidence,
            dict,
        ):
            return

        current_confidence = self._normalize_confidence(
            evidence.get(
                "confidence",
                0.0,
            )
        )

        evidence["confidence"] = min(
            current_confidence,
            confidence,
        )

    def _synchronize_flat_fields(
        self,
        document: Document,
    ) -> None:
        document.extracted_data = {
            field_name: evidence.get(
                "value"
            )
            for field_name, evidence
            in document.field_evidence.items()
        }

        document.field_confidences = {
            field_name: self._normalize_confidence(
                evidence.get(
                    "confidence",
                    0.0,
                )
            )
            for field_name, evidence
            in document.field_evidence.items()
        }

    def _parse_date(
        self,
        value: Any,
    ) -> str | None:
        text_value = str(
            value
        ).strip()

        for date_format in self.DATE_FORMATS:
            try:
                parsed_date = datetime.strptime(
                    text_value,
                    date_format,
                ).date()

                return parsed_date.isoformat()
            except ValueError:
                continue

        return None

    def _normalize_modifier_values(
        self,
        value: Any,
    ) -> set[str]:
        if value is None:
            return set()

        values = (
            value
            if isinstance(
                value,
                list,
            )
            else [value]
        )

        return {
            str(
                item
            ).strip().upper()
            for item in values
            if str(
                item
            ).strip()
        }

    def _normalize_alphanumeric(
        self,
        value: Any,
    ) -> str:
        return "".join(
            character.upper()
            for character in str(
                value or ""
            )
            if character.isalnum()
        )

    def _tokenize(
        self,
        value: Any,
    ) -> set[str]:
        return {
            token.upper()
            for token in re.findall(
                r"[A-Za-z0-9]+",
                str(
                    value or ""
                ),
            )
        }

    def _normalized_text(
        self,
        value: Any,
    ) -> str:
        return str(
            value or ""
        ).strip().lower()

    def _normalize_confidence(
        self,
        value: Any,
    ) -> float:
        try:
            confidence = float(
                value
            )
        except (TypeError, ValueError):
            return 0.0

        if confidence > 1:
            confidence = confidence / 100

        return max(
            0.0,
            min(
                confidence,
                1.0,
            ),
        )

    def _deduplicate_strings(
        self,
        values: list[Any],
    ) -> list[str]:
        unique_values: list[str] = []

        for value in values:
            normalized_value = str(
                value
            ).strip().upper()

            if (
                normalized_value
                and normalized_value not in unique_values
            ):
                unique_values.append(
                    normalized_value
                )

        return unique_values

    def _is_empty_value(
        self,
        value: Any,
    ) -> bool:
        if value is None:
            return True

        if isinstance(
            value,
            str,
        ):
            return not value.strip()

        if isinstance(
            value,
            list,
        ):
            return len(value) == 0

        return False

    def _remove_duplicates(
        self,
        values: list[str],
    ) -> list[str]:
        unique_values: list[str] = []

        for value in values:
            if value not in unique_values:
                unique_values.append(
                    value
                )

        return unique_values