from dataclasses import fields
from types import SimpleNamespace

from src.services.smartsheet_destination_schema_service import (
    SmartsheetDestinationSchemaResult,
    SmartsheetDestinationSchemaService,
)


passed = 0
failed = 0


class TruthySystemColumnType:
    def __init__(self, normalized_value):
        self.normalized_value = normalized_value

    def __bool__(self):
        return True

    def __str__(self):
        return str(self.normalized_value)


class RecordingClient:
    def __init__(
        self,
        *,
        columns=None,
        error=None,
    ):
        self.columns = columns
        self.error = error
        self.call_count = 0

    def get_columns(
        self,
    ):
        self.call_count += 1

        if self.error is not None:
            raise self.error

        return SimpleNamespace(data=self.columns)


def run_test(
    name,
    test,
):
    global passed
    global failed

    try:
        test()
        passed += 1
        print(
            f"PASSED: {name}"
        )
    except Exception as error:
        failed += 1
        print(
            f"FAILED: {name}: "
            f"{type(error).__name__}"
        )


def build_columns():
    return [
        SimpleNamespace(
            title="Authorization Status",
            id=1001,
            type="TEXT_NUMBER",
        ),
        SimpleNamespace(
            title="AI Review Status",
            id=1002,
            type="PICKLIST",
        ),
    ]


def test_valid_schema_is_returned():
    client = RecordingClient(
        columns=build_columns()
    )

    service = (
        SmartsheetDestinationSchemaService(
            client=client
        )
    )

    result = service.read()

    assert result.success is True
    assert result.status == "ready"
    assert result.column_count == 2

    assert result.columns == {
        "Authorization Status": 1001,
        "AI Review Status": 1002,
    }
    assert result.column_types == {
        "Authorization Status": "TEXT_NUMBER",
        "AI Review Status": "PICKLIST",
    }

    assert client.call_count == 1


def test_titles_are_trimmed():
    client = RecordingClient(
        columns=[
            SimpleNamespace(
                title=" Authorization Status ",
                id=1001,
            )
        ]
    )

    result = (
        SmartsheetDestinationSchemaService(
            client=client
        )
        .read()
    )

    assert result.columns == {
        "Authorization Status": 1001,
    }


def test_boolean_id_is_rejected():
    result = (
        SmartsheetDestinationSchemaService(
            client=RecordingClient(
                columns=[
                    SimpleNamespace(
                        title="Authorization Status",
                        id=True,
                    )
                ]
            )
        )
        .read()
    )

    assert result.success is False
    assert result.status == "invalid_column_id"


def test_invalid_id_is_rejected():
    result = (
        SmartsheetDestinationSchemaService(
            client=RecordingClient(
                columns=[
                    SimpleNamespace(
                        title="Authorization Status",
                        id=0,
                    )
                ]
            )
        )
        .read()
    )

    assert result.success is False
    assert result.status == "invalid_column_id"


def test_blank_title_is_rejected():
    result = (
        SmartsheetDestinationSchemaService(
            client=RecordingClient(
                columns=[
                    SimpleNamespace(
                        title="   ",
                        id=1001,
                    )
                ]
            )
        )
        .read()
    )

    assert result.success is False

    assert (
        result.status
        == "invalid_column_title"
    )


def test_duplicate_title_is_rejected():
    result = (
        SmartsheetDestinationSchemaService(
            client=RecordingClient(
                columns=[
                    SimpleNamespace(
                        title="Authorization Status",
                        id=1001,
                    ),
                    SimpleNamespace(
                        title="Authorization Status",
                        id=1002,
                    ),
                ]
            )
        )
        .read()
    )

    assert result.success is False

    assert (
        result.status
        == "duplicate_column_title"
    )


def test_empty_schema_is_rejected():
    result = (
        SmartsheetDestinationSchemaService(
            client=RecordingClient(
                columns=[]
            )
        )
        .read()
    )

    assert result.success is False
    assert result.status == "empty_schema"



class IterableColumns:
    def __init__(
        self,
        values,
    ):
        self.values = values

    def __iter__(
        self,
    ):
        return iter(
            self.values
        )


def test_iterable_schema_collection_is_accepted():
    service = SmartsheetDestinationSchemaService(
        client=RecordingClient(
            columns=IterableColumns(
                [
                    SimpleNamespace(
                        title="Authorization Status",
                        id=123,
                    )
                ]
            )
        )
    )

    result = service.read()

    assert result.success is True
    assert result.status == "ready"
    assert result.column_count == 1

    assert result.columns == {
        "Authorization Status": 123
    }


def test_invalid_schema_collection_is_rejected():
    result = (
        SmartsheetDestinationSchemaService(
            client=RecordingClient(
                columns=None
            )
        )
        .read()
    )

    assert result.success is False
    assert result.status == "invalid_schema"


def test_client_failure_is_sanitized():
    result = (
        SmartsheetDestinationSchemaService(
            client=RecordingClient(
                error=RuntimeError(
                    "PRIVATE-SYNTHETIC-ERROR"
                )
            )
        )
        .read()
    )

    assert result.success is False
    assert result.status == "schema_read_failed"

    assert (
        "PRIVATE-SYNTHETIC-ERROR"
        not in repr(
            result
        )
    )


def test_result_contract_is_phi_safe():
    field_names = {
        field.name
        for field in fields(
            SmartsheetDestinationSchemaResult
        )
    }

    assert field_names == {
        "column_count",
        "columns",
        "column_types",
        "success",
        "status",
    }

    prohibited_names = {
        "rows",
        "row_values",
        "payload",
        "source_text",
        "ocr_text",
        "filename",
        "file_path",
        "patient",
        "review_output",
    }

    assert field_names.isdisjoint(
        prohibited_names
    )


def test_truthy_none_wrapper_is_not_a_system_column():
    value = TruthySystemColumnType(None)
    assert bool(value) is True
    assert SmartsheetDestinationSchemaService.system_column_type_category(value) == "none"
    assert SmartsheetDestinationSchemaService.is_system_column_type(value) is False


def test_truthy_auto_number_wrapper_is_a_system_column():
    value = TruthySystemColumnType("AUTO_NUMBER")
    assert SmartsheetDestinationSchemaService.system_column_type_category(value) == "AUTO_NUMBER"
    assert SmartsheetDestinationSchemaService.is_system_column_type(value) is True


def test_other_supported_wrappers_are_system_columns():
    for category in ("CREATED_BY", "CREATED_DATE", "MODIFIED_BY", "MODIFIED_DATE"):
        value = TruthySystemColumnType(category)
        assert SmartsheetDestinationSchemaService.system_column_type_category(value) == category
        assert SmartsheetDestinationSchemaService.is_system_column_type(value) is True


def test_plain_none_is_not_a_system_column():
    assert SmartsheetDestinationSchemaService.system_column_type_category(None) == "none"
    assert SmartsheetDestinationSchemaService.is_system_column_type(None) is False


print(
    "=" * 60
)
print(
    "Testing Smartsheet Destination Schema Reader"
)
print(
    "=" * 60
)

run_test(
    "valid schema is returned",
    test_valid_schema_is_returned,
)

run_test(
    "column titles are trimmed",
    test_titles_are_trimmed,
)

run_test(
    "boolean column ID is rejected",
    test_boolean_id_is_rejected,
)

run_test(
    "invalid column ID is rejected",
    test_invalid_id_is_rejected,
)

run_test(
    "blank title is rejected",
    test_blank_title_is_rejected,
)

run_test(
    "duplicate title is rejected",
    test_duplicate_title_is_rejected,
)

run_test(
    "empty schema is rejected",
    test_empty_schema_is_rejected,
)

run_test(
    "iterable schema collection is accepted",
    test_iterable_schema_collection_is_accepted,
)

run_test(
    "invalid schema collection is rejected",
    test_invalid_schema_collection_is_rejected,
)

run_test(
    "client failure is sanitized",
    test_client_failure_is_sanitized,
)

run_test(
    "result contract is PHI-safe",
    test_result_contract_is_phi_safe,
)

run_test(
    "truthy normalized-None wrapper is not a system column",
    test_truthy_none_wrapper_is_not_a_system_column,
)

run_test(
    "AUTO_NUMBER wrapper is a system column",
    test_truthy_auto_number_wrapper_is_a_system_column,
)

run_test(
    "other supported wrappers are system columns",
    test_other_supported_wrappers_are_system_columns,
)

run_test(
    "plain None is not a system column",
    test_plain_none_is_not_a_system_column,
)

print()
print(
    f"Passed: {passed}"
)
print(
    f"Failed: {failed}"
)
print(
    "Real or mock: Synthetic deterministic/mock"
)
print(
    "Smartsheet external API: Not called"
)
print(
    "Smartsheet rows read: 0"
)
print(
    "Smartsheet rows written: 0"
)
print(
    "Microsoft Graph: Not called"
)
print(
    "OCR: Not called"
)
print(
    "Ollama: Not called"
)
print(
    "PHI handling: Column titles and IDs only"
)

if failed:
    raise SystemExit(1)
