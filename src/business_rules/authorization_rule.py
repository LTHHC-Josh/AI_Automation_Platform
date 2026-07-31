from datetime import date, datetime
from typing import Any

from src.business_rules.provider_registration import register_rule
from src.business_rules.rule import Rule
from src.models.document import Document


class BaseAuthorizationRule(Rule):
    """
    Shared validation rules for initial and renewal authorizations.

    Authorizations may approve visits, sessions, service units,
    equipment quantities, or recurring monthly services. A valid
    authorization is not required to contain approved visits when
    another approved quantity is present.
    """

    SUCCESS_ACTION = "Authorization validated successfully"

    def execute(
        self,
        document: Document,
    ) -> list:
        actions: list[str] = []
        data = document.extracted_data

        self._require_text(
            data=data,
            field_name="patient_name",
            message="Missing patient name",
            actions=actions,
        )

        self._require_text(
            data=data,
            field_name="authorization_number",
            message="Missing authorization number",
            actions=actions,
        )

        self._require_text(
            data=data,
            field_name="payer",
            message="Missing payer",
            actions=actions,
        )

        self._validate_status(
            data=data,
            actions=actions,
        )

        self._validate_authorized_quantity(
            data=data,
            actions=actions,
        )

        self._validate_dates(
            data=data,
            actions=actions,
        )

        self._validate_member_id(
            data=data,
            actions=actions,
        )

        self._validate_provider_npi(
            data=data,
            actions=actions,
        )

        if not actions:
            actions.append(
                self.SUCCESS_ACTION
            )

        return actions

    def _require_text(
        self,
        data: dict,
        field_name: str,
        message: str,
        actions: list[str],
    ) -> None:
        value = data.get(field_name)

        if value is None:
            actions.append(message)
            return

        if isinstance(value, str) and not value.strip():
            actions.append(message)

    def _validate_status(
        self,
        data: dict,
        actions: list[str],
    ) -> None:
        status = str(
            data.get(
                "authorization_status",
                "",
            )
        ).strip().lower()

        if not status:
            actions.append(
                "Missing authorization status"
            )
            return

        approved_statuses = {
            "approved",
            "partially approved",
            "partial approval",
        }

        if status not in approved_statuses:
            actions.append(
                "Authorization status is not approved"
            )

    def _validate_authorized_quantity(
        self,
        data: dict,
        actions: list[str],
    ) -> None:
        approved_visits = self._positive_quantity(
            data.get("approved_visits")
        )

        authorized_units = self._positive_quantity(
            data.get("authorized_units")
        )

        if (
            approved_visits is None
            and authorized_units is None
        ):
            actions.append(
                "Missing approved visits or authorized units"
            )

    def _validate_dates(
        self,
        data: dict,
        actions: list[str],
    ) -> None:
        start_value = data.get("start_date")
        end_value = data.get("end_date")

        if not start_value:
            actions.append(
                "Missing authorization start date"
            )

        if not end_value:
            actions.append(
                "Missing authorization end date"
            )

        if not start_value or not end_value:
            return

        start_date = self._parse_date(
            start_value
        )

        end_date = self._parse_date(
            end_value
        )

        if start_date is None:
            actions.append(
                "Invalid authorization start date"
            )

        if end_date is None:
            actions.append(
                "Invalid authorization end date"
            )

        if (
            start_date is not None
            and end_date is not None
            and end_date < start_date
        ):
            actions.append(
                "Authorization end date is before start date"
            )

    def _validate_member_id(
        self,
        data: dict,
        actions: list[str],
    ) -> None:
        member_id = data.get("member_id")

        if member_id is None:
            actions.append(
                "Missing member ID"
            )
            return

        normalized_member_id = "".join(
            character
            for character in str(member_id)
            if character.isalnum()
        )

        if not normalized_member_id:
            actions.append(
                "Missing member ID"
            )

    def _validate_provider_npi(
        self,
        data: dict,
        actions: list[str],
    ) -> None:
        provider_npi = data.get("provider_npi")

        if provider_npi is None:
            return

        normalized_npi = "".join(
            character
            for character in str(provider_npi)
            if character.isdigit()
        )

        if len(normalized_npi) != 10:
            actions.append(
                "Provider NPI must contain 10 digits"
            )

    def _positive_quantity(
        self,
        value: Any,
    ) -> float | None:
        if value is None:
            return None

        if isinstance(value, list):
            quantities = [
                self._positive_quantity(item)
                for item in value
            ]

            valid_quantities = [
                quantity
                for quantity in quantities
                if quantity is not None
            ]

            if not valid_quantities:
                return None

            return sum(valid_quantities)

        if isinstance(value, dict):
            possible_values = [
                value.get("units"),
                value.get("quantity"),
                value.get("value"),
            ]

            for possible_value in possible_values:
                quantity = self._positive_quantity(
                    possible_value
                )

                if quantity is not None:
                    return quantity

            return None

        try:
            quantity = float(value)
        except (TypeError, ValueError):
            return None

        if quantity <= 0:
            return None

        return quantity

    def _parse_date(
        self,
        value: Any,
    ) -> date | None:
        if isinstance(value, datetime):
            return value.date()

        if isinstance(value, date):
            return value

        text_value = str(value).strip()

        supported_formats = (
            "%Y-%m-%d",
            "%m/%d/%Y",
        )

        for date_format in supported_formats:
            try:
                return datetime.strptime(
                    text_value,
                    date_format,
                ).date()
            except ValueError:
                continue

        return None


@register_rule("authorization")
class AuthorizationRule(
    BaseAuthorizationRule
):
    """
    Business rules for initial authorizations.
    """

    document_type = "authorization"


@register_rule("authorization_renewal")
class AuthorizationRenewalRule(
    BaseAuthorizationRule
):
    """
    Business rules for renewal, extension, continuation, and
    amendment authorizations.
    """

    document_type = "authorization_renewal"

    def execute(
        self,
        document: Document,
    ) -> list:
        actions = super().execute(
            document
        )

        if (
            self.SUCCESS_ACTION
            in actions
        ):
            request_type = str(
                document.extracted_data.get(
                    "request_type",
                    "",
                )
            ).strip().lower()

            renewal_terms = {
                "renewal",
                "extension",
                "amendment",
                "continuation",
                "extension/renewal/amendment",
            }

            if request_type not in renewal_terms:
                actions.remove(
                    self.SUCCESS_ACTION
                )

                actions.append(
                    "Renewal type requires verification"
                )

        return actions