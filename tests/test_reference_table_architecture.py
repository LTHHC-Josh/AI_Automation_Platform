from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZIP_DEFLATED, ZipFile

from src.services.reference_table_service import (
    ReferenceTableLoader,
    ReferenceTableRefreshService,
)


PAYOR_COLUMNS = ["PAYOR NAME", "KEY FIELD", "RESULTS", "TYPE", "DESCRIPTION"]
SERVICE_COLUMNS = [
    "HCPCS/BILL CODE", "MODIFIERS", "PROGRAM", "DESCRIPTION",
    "SERVICES GROUP", "CFC OPTION", "WAIVER OPTION", "NAMING CONVENTION",
]


def write_workbook(path: Path, sheets: dict[str, list[list[str]]]) -> None:
    shared = []
    index = {}
    for rows in sheets.values():
        for row in rows:
            for value in row:
                if value not in index:
                    index[value] = len(shared)
                    shared.append(value)

    def cell(column, row, value):
        return f'<c r="{column}{row}" t="s"><v>{index[value]}</v></c>'

    def column_name(number):
        result = ""
        while number:
            number, remainder = divmod(number - 1, 26)
            result = chr(65 + remainder) + result
        return result

    workbook_sheets = []
    relationships = []
    with ZipFile(path, "w", ZIP_DEFLATED) as archive:
        archive.writestr(
            "xl/sharedStrings.xml",
            '<?xml version="1.0"?><sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
            + "".join(f"<si><t>{value}</t></si>" for value in shared) + "</sst>",
        )
        for sheet_number, (name, rows) in enumerate(sheets.items(), 1):
            workbook_sheets.append(
                f'<sheet name="{name}" sheetId="{sheet_number}" r:id="rId{sheet_number}"/>'
            )
            relationships.append(
                f'<Relationship Id="rId{sheet_number}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet{sheet_number}.xml"/>'
            )
            xml_rows = []
            for row_number, row in enumerate(rows, 1):
                cells = "".join(
                    cell(column_name(column_number), row_number, value)
                    for column_number, value in enumerate(row, 1)
                )
                xml_rows.append(f'<row r="{row_number}">{cells}</row>')
            archive.writestr(
                f"xl/worksheets/sheet{sheet_number}.xml",
                '<?xml version="1.0"?><worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>'
                + "".join(xml_rows) + "</sheetData></worksheet>",
            )
        archive.writestr(
            "xl/workbook.xml",
            '<?xml version="1.0"?><workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets>'
            + "".join(workbook_sheets) + "</sheets></workbook>",
        )
        archive.writestr(
            "xl/_rels/workbook.xml.rels",
            '<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            + "".join(relationships) + "</Relationships>",
        )


def valid_sheets():
    return {
        "PAYOR LISTING": [PAYOR_COLUMNS, ["SYNTHETIC PAYOR", "", "SP", "MCO", "Synthetic"]],
        "SERVICES LISTING": [SERVICE_COLUMNS, ["T0000", "U1", "SYNTHETIC PROGRAM", "Synthetic", "Group", "", "", "T0000U1"]],
    }


def test_valid_tables_load_and_lookup_deterministically():
    with TemporaryDirectory() as directory:
        path = Path(directory) / "synthetic.xlsx"
        write_workbook(path, valid_sheets())
        result = ReferenceTableLoader().load(path)

    assert result.success is True
    assert result.tables.payors.lookup("synthetic payor", "").value == "SP"
    assert result.tables.services.lookup("t0000", "u1", "synthetic program").value == "T0000U1"
    assert result.tables.document_types is None


def test_optional_document_types_sheet_uses_separate_schema():
    sheets = valid_sheets()
    sheets["DOCUMENT TYPES"] = [
        ["DOCUMENT TYPE", "NAMING CONVENTION", "DESCRIPTION"],
        ["SYNTHETIC NOTICE", "NOTICE", "Synthetic document type"],
    ]
    with TemporaryDirectory() as directory:
        path = Path(directory) / "synthetic.xlsx"
        write_workbook(path, sheets)
        result = ReferenceTableLoader().load(path)

    assert result.success is True
    assert result.tables.document_types.lookup("synthetic notice").value == "NOTICE"


def test_missing_sheet_column_duplicate_and_blank_result_fail_safely():
    cases = []
    missing_sheet = valid_sheets(); missing_sheet.pop("SERVICES LISTING"); cases.append(missing_sheet)
    missing_column = valid_sheets(); missing_column["PAYOR LISTING"][0] = PAYOR_COLUMNS[:-1]; cases.append(missing_column)
    duplicate = valid_sheets(); duplicate["PAYOR LISTING"].append(["SYNTHETIC PAYOR", "", "OTHER", "MCO", "Duplicate"]); cases.append(duplicate)
    blank = valid_sheets(); blank["SERVICES LISTING"][1][-1] = ""; cases.append(blank)

    with TemporaryDirectory() as directory:
        for number, sheets in enumerate(cases):
            path = Path(directory) / f"case-{number}.xlsx"
            write_workbook(path, sheets)
            result = ReferenceTableLoader().load(path)
            assert result.success is False
            assert result.tables is None


class Source:
    def __init__(self, version, workbook):
        self.version = version
        self.workbook = workbook
        self.metadata_calls = 0
        self.download_calls = 0

    def get_version(self):
        self.metadata_calls += 1
        return self.version

    def download(self):
        self.download_calls += 1
        return self.workbook.read_bytes()


def test_refresh_uses_version_cache_and_preserves_last_known_good():
    with TemporaryDirectory() as directory:
        root = Path(directory)
        good = root / "good.xlsx"; write_workbook(good, valid_sheets())
        source = Source("v1", good)
        service = ReferenceTableRefreshService(source=source, cache_directory=root / "cache")

        first = service.get_tables()
        second = service.get_tables()
        assert first.refresh_succeeded is True
        assert second.used_cache is True
        assert source.download_calls == 1

        bad = root / "bad.xlsx"; write_workbook(bad, {"PAYOR LISTING": [PAYOR_COLUMNS]})
        source.version = "v2"; source.workbook = bad
        failed = service.get_tables()
        assert failed.status == "reference_invalid"
        assert failed.tables.payors.lookup("SYNTHETIC PAYOR", "").value == "SP"
        assert ReferenceTableLoader().load(service.workbook_path).success is True


def test_missing_and_ambiguous_lookups_never_guess():
    with TemporaryDirectory() as directory:
        path = Path(directory) / "synthetic.xlsx"; write_workbook(path, valid_sheets())
        tables = ReferenceTableLoader().load(path).tables

    assert tables.payors.lookup("UNKNOWN", "").resolved is False
    assert tables.services.lookup("T0000", "", "SYNTHETIC PROGRAM").resolved is False


def test_conflicting_three_part_service_mappings_load_but_lookup_is_ambiguous():
    sheets = valid_sheets()
    sheets["SERVICES LISTING"] = [
        SERVICE_COLUMNS,
        ["T1000", "U1", "PROGRAM", "Priority description one", "Group", "", "", "FIRST TOKEN"],
        ["T1000", "U1", "PROGRAM", "Priority description two", "Group", "", "", "SECOND TOKEN"],
    ]
    with TemporaryDirectory() as directory:
        path = Path(directory) / "ambiguous.xlsx"; write_workbook(path, sheets)
        loaded = ReferenceTableLoader().load(path)

    lookup = loaded.tables.services.lookup("T1000", "U1", "PROGRAM")
    assert loaded.success is True
    assert lookup.resolved is False
    assert lookup.value is None
    assert lookup.status == "ambiguous"


def test_unique_three_part_service_mapping_still_resolves():
    with TemporaryDirectory() as directory:
        path = Path(directory) / "legacy.xlsx"; write_workbook(path, valid_sheets())
        services = ReferenceTableLoader().load(path).tables.services

    result = services.lookup("T0000", "U1", "SYNTHETIC PROGRAM")
    assert result.resolved is True
    assert result.value == "T0000U1"
    assert result.status == "resolved"


def test_description_is_not_a_hidden_service_lookup_discriminator():
    sheets = valid_sheets()
    sheets["SERVICES LISTING"] = [
        SERVICE_COLUMNS,
        ["T1000", "U1", "PROGRAM", "Different description one", "Group", "", "", "SAME TOKEN"],
        ["T1000", "U1", "PROGRAM", "Different description two", "Group", "", "", "SAME TOKEN"],
    ]
    with TemporaryDirectory() as directory:
        path = Path(directory) / "ambiguous.xlsx"; write_workbook(path, sheets)
        loaded = ReferenceTableLoader().load(path)

    lookup = loaded.tables.services.lookup("T1000", "U1", "PROGRAM")
    assert loaded.success is True
    assert lookup.resolved is True
    assert lookup.value == "SAME TOKEN"


if __name__ == "__main__":
    tests = [value for name, value in list(globals().items()) if name.startswith("test_")]
    for test in tests:
        test()
    print(f"Passed: {len(tests)}")
    print("Failed: 0")
    print("Classification: synthetic deterministic/mock")
    print("Live Graph: not called")
    print("PHI handling: business-reference fixtures only")
