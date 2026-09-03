import os
import unittest
from unittest.mock import MagicMock
from unittest.mock import patch

from src.clients.smartsheet_client import (
    SmartsheetClient,
    _DefaultTimeoutSession,
)


class TestSmartsheetSheetRouting(
    unittest.TestCase
):

    def setUp(self):
        self.environment = {
            "SMARTSHEET_API_TOKEN": (
                "synthetic-test-token"
            ),
            "SMARTSHEET_SHEET_ID": (
                "1111111111111111"
            ),
            "SMARTSHEET_AI_DESTINATION_SHEET_ID": (
                "2222222222222222"
            ),
            "SMARTSHEET_HTTP_TIMEOUT_SECONDS": "30",
        }

    def _build_client(
        self,
        sheet_id_env_var=None,
    ):
        sdk_client = MagicMock()

        with patch.dict(
            os.environ,
            self.environment,
            clear=False,
        ):
            with patch(
                "src.clients.smartsheet_client."
                "load_dotenv"
            ):
                with patch(
                    "src.clients.smartsheet_client."
                    "smartsheet.Smartsheet",
                    return_value=sdk_client,
                ):
                    if sheet_id_env_var is None:
                        client = SmartsheetClient()
                    else:
                        client = SmartsheetClient(
                            sheet_id_env_var=(
                                sheet_id_env_var
                            )
                        )

        return client, sdk_client

    def test_default_uses_project_tracker_sheet(
        self,
    ):
        client, _ = self._build_client()

        self.assertEqual(
            client.sheet_id,
            "1111111111111111",
        )

    def test_explicit_destination_uses_ai_sheet(
        self,
    ):
        client, _ = self._build_client(
            "SMARTSHEET_AI_DESTINATION_SHEET_ID"
        )

        self.assertEqual(
            client.sheet_id,
            "2222222222222222",
        )

    def test_get_sheet_uses_selected_sheet(
        self,
    ):
        client, sdk_client = (
            self._build_client(
                "SMARTSHEET_AI_DESTINATION_SHEET_ID"
            )
        )

        client.get_sheet()

        sdk_client.Sheets.get_sheet.assert_called_once_with(
            "2222222222222222"
        )

    def test_default_transport_timeout_is_installed(self):
        client, sdk_client = self._build_client()

        self.assertIsInstance(client.client._session, _DefaultTimeoutSession)
        self.assertEqual(
            client.client._session._timeout_seconds,
            SmartsheetClient.DEFAULT_HTTP_TIMEOUT_SECONDS,
        )

    def test_invalid_transport_timeout_fails_closed(self):
        environment = dict(self.environment)
        environment["SMARTSHEET_HTTP_TIMEOUT_SECONDS"] = "invalid"

        with patch.dict(os.environ, environment, clear=True):
            with patch("src.clients.smartsheet_client.load_dotenv"):
                with patch("src.clients.smartsheet_client.smartsheet.Smartsheet"):
                    with self.assertRaisesRegex(ValueError, "positive number"):
                        SmartsheetClient()

    def test_missing_selected_variable_fails(
        self,
    ):
        environment = dict(
            self.environment
        )

        environment.pop(
            "SMARTSHEET_AI_DESTINATION_SHEET_ID"
        )

        with patch.dict(
            os.environ,
            environment,
            clear=True,
        ):
            with patch(
                "src.clients.smartsheet_client."
                "load_dotenv"
            ):
                with patch(
                    "src.clients.smartsheet_client."
                    "smartsheet.Smartsheet"
                ):
                    with self.assertRaisesRegex(
                        ValueError,
                        (
                            "SMARTSHEET_AI_"
                            "DESTINATION_SHEET_ID "
                            "not found"
                        ),
                    ):
                        SmartsheetClient(
                            sheet_id_env_var=(
                                "SMARTSHEET_AI_"
                                "DESTINATION_SHEET_ID"
                            )
                        )

    def test_blank_environment_name_fails(
        self,
    ):
        with patch.dict(
            os.environ,
            self.environment,
            clear=False,
        ):
            with patch(
                "src.clients.smartsheet_client."
                "load_dotenv"
            ):
                with self.assertRaises(
                    ValueError
                ):
                    SmartsheetClient(
                        sheet_id_env_var="   "
                    )


if __name__ == "__main__":
    unittest.main()
