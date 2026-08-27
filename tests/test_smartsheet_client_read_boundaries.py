from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from types import SimpleNamespace

from src.clients.smartsheet_client import SmartsheetClient
from src.services.smartsheet_submission_key_configuration_service import (
    SmartsheetSubmissionKeyConfigurationService,
)


class ForbiddenMutations:
    def __init__(self):
        self.calls = 0

    def __getattr__(self, name):
        if name in {"add_rows", "update_rows", "attach_file_to_row"}:
            def forbidden(*args, **kwargs):
                self.calls += 1
                raise AssertionError("mutation method called")
            return forbidden
        raise AttributeError(name)


class RecordingSheets(ForbiddenMutations):
    def __init__(self, pages=None, columns=None, error=None):
        super().__init__()
        self.pages = pages or []
        self.columns = columns or []
        self.error = error
        self.sheet_calls = []
        self.column_calls = []

    def get_columns(self, *args, **kwargs):
        self.column_calls.append((args, kwargs))
        if self.error:
            raise self.error
        return SimpleNamespace(data=self.columns)

    def get_sheet(self, *args, **kwargs):
        self.sheet_calls.append((args, kwargs))
        if self.error:
            raise self.error
        return self.pages[kwargs["page"] - 1]


class RecordingAttachments(ForbiddenMutations):
    def __init__(self, names=None, error=None):
        super().__init__()
        self.names = names or []
        self.error = error
        self.calls_read = []

    def list_row_attachments(self, *args, **kwargs):
        self.calls_read.append((args, kwargs))
        if self.error:
            raise self.error
        return SimpleNamespace(data=[SimpleNamespace(name=name) for name in self.names])


def client_with(*, sheets, attachments=None):
    client = object.__new__(SmartsheetClient)
    client.sheet_id = "protected-sheet-reference"
    client.client = SimpleNamespace(
        Sheets=sheets,
        Attachments=attachments or RecordingAttachments(),
    )
    return client


def row(row_id, column_id, value):
    return SimpleNamespace(
        id=row_id,
        cells=[SimpleNamespace(column_id=column_id, value=value)],
    )


def test_columns_use_metadata_only_sdk_boundary():
    sheets = RecordingSheets(columns=[SimpleNamespace(id=7, title="Technical")])
    response = client_with(sheets=sheets).get_columns()
    assert len(response.data) == 1
    assert sheets.column_calls == [(("protected-sheet-reference",), {"include_all": True})]
    assert sheets.sheet_calls == []
    assert sheets.calls == 0


def test_exact_title_lookup_requires_one_exact_match():
    sheets = RecordingSheets(columns=[
        SimpleNamespace(id=7, title="Technical"),
        SimpleNamespace(id=8, title="Technical Extra"),
    ], pages=[SimpleNamespace(version=1, total_row_count=0, rows=[])])
    client = client_with(sheets=sheets)
    assert client.find_row_ids_by_exact_column_title_value(
        column_title="Technical", value="key") == []
    assert len(sheets.sheet_calls) == 1

    for columns in ([], [SimpleNamespace(id=7, title="Technical"),
                         SimpleNamespace(id=8, title="Technical")]):
        unavailable = RecordingSheets(columns=columns)
        try:
            client_with(sheets=unavailable).find_row_ids_by_exact_column_title_value(
                column_title="Technical", value="key")
            raise AssertionError("unavailable or ambiguous title accepted")
        except ValueError as error:
            assert "key" not in str(error)
        assert unavailable.sheet_calls == []
        assert unavailable.calls == 0


def test_submission_key_configuration_validation_and_safe_representation():
    environment_variable = "SMARTSHEET_AI_SUBMISSION_KEY_COLUMN_TITLE"
    invalid_values = [None, "", "   ", "line\nbreak", "line\rbreak", "bad\x00value",
                      "x" * 101, 42]
    for value in invalid_values:
        environment = {} if value is None else {environment_variable: value}
        result = SmartsheetSubmissionKeyConfigurationService(environment=environment).resolve()
        assert result.success is False
        assert result.configured is False
        assert result.column_title is None
        if isinstance(value, str) and value:
            assert value not in repr(result)

    configured = SmartsheetSubmissionKeyConfigurationService(environment={
        environment_variable: "  Approved Technical Title  ",
    }).resolve()
    assert configured.success is True
    assert configured.configured is True
    assert configured.column_title == "Approved Technical Title"
    assert "Approved Technical Title" not in repr(configured)


def test_exact_lookup_paginates_only_requested_column_and_preserves_order():
    column_id = 77
    pages = [
        SimpleNamespace(
            version=9,
            total_row_count=101,
            rows=[row(1000 + index, column_id, "target" if index == 2 else "other")
                  for index in range(100)],
        ),
        SimpleNamespace(version=9, total_row_count=101, rows=[row(2000, column_id, "target")]),
    ]
    sheets = RecordingSheets(pages=pages)
    result = client_with(sheets=sheets).find_row_ids_by_exact_column_value(
        column_id=column_id, value="target")
    assert result == [1002, 2000]
    assert [call[1] for call in sheets.sheet_calls] == [
        {"column_ids": [column_id], "page_size": 100, "page": 1},
        {"column_ids": [column_id], "page_size": 100, "page": 2},
    ]
    assert sheets.calls == 0


def test_exact_lookup_zero_and_exactly_one_categories():
    zero = RecordingSheets(pages=[SimpleNamespace(version=1, total_row_count=1,
                                                   rows=[row(1, 5, "other")])])
    one = RecordingSheets(pages=[SimpleNamespace(version=1, total_row_count=1,
                                                  rows=[row(2, 5, "target")])])
    assert client_with(sheets=zero).find_row_ids_by_exact_column_value(
        column_id=5, value="target") == []
    assert client_with(sheets=one).find_row_ids_by_exact_column_value(
        column_id=5, value="target") == [2]


def test_exact_lookup_rejects_changed_version_and_invalid_pagination():
    changed = RecordingSheets(pages=[
        SimpleNamespace(version=1, total_row_count=2, rows=[row(1, 5, "target")]),
        SimpleNamespace(version=2, total_row_count=2, rows=[row(2, 5, "target")]),
    ])
    try:
        client_with(sheets=changed).find_row_ids_by_exact_column_value(
            column_id=5, value="target")
        raise AssertionError("version change accepted")
    except RuntimeError as error:
        assert "target" not in str(error)

    incomplete = RecordingSheets(pages=[
        SimpleNamespace(version=1, total_row_count=1, rows=[]),
    ])
    try:
        client_with(sheets=incomplete).find_row_ids_by_exact_column_value(
            column_id=5, value="private-value")
        raise AssertionError("incomplete page accepted")
    except RuntimeError as error:
        assert "private-value" not in str(error)


def test_read_failures_do_not_expose_provider_details():
    private = "PRIVATE-PROVIDER-DETAIL"
    sheets = RecordingSheets(error=RuntimeError(private))
    output = StringIO()
    with redirect_stdout(output), redirect_stderr(output):
        try:
            client_with(sheets=sheets).find_row_ids_by_exact_column_value(
                column_id=5, value="PRIVATE-KEY")
        except RuntimeError:
            pass
    assert private not in output.getvalue()
    assert "PRIVATE-KEY" not in output.getvalue()


def test_attachment_metadata_categories_and_sdk_boundary():
    for names, expected in [([], []), (["one.txt"], ["one.txt"]),
                            (["one.txt", "two.txt"], ["one.txt", "two.txt"] )]:
        attachments = RecordingAttachments(names=names)
        sheets = RecordingSheets()
        result = client_with(sheets=sheets, attachments=attachments).list_row_attachment_names(
            row_id=321)
        assert result == expected
        assert attachments.calls_read == [
            (("protected-sheet-reference", 321), {"include_all": True})]
        assert attachments.calls == 0
        assert sheets.calls == 0


def test_attachment_read_failure_has_no_output():
    attachments = RecordingAttachments(error=RuntimeError("PRIVATE-ATTACHMENT-NAME"))
    output = StringIO()
    with redirect_stdout(output), redirect_stderr(output):
        try:
            client_with(sheets=RecordingSheets(), attachments=attachments).list_row_attachment_names(
                row_id=654)
        except RuntimeError:
            pass
    assert "PRIVATE-ATTACHMENT-NAME" not in output.getvalue()
    assert "654" not in output.getvalue()


if __name__ == "__main__":
    tests = [value for name, value in sorted(globals().items())
             if name.startswith("test_") and callable(value)]
    failures = 0
    for test in tests:
        try:
            test()
            print(f"PASSED: {test.__name__}")
        except Exception as error:
            failures += 1
            print(f"FAILED: {test.__name__}: {type(error).__name__}")
    print(f"Passed: {len(tests) - failures}")
    print(f"Failed: {failures}")
    print("Real or mock: Synthetic deterministic/mock")
    print("External Smartsheet API: Not called")
    print("PHI handling: Synthetic technical metadata only")
    if failures:
        raise SystemExit(1)
