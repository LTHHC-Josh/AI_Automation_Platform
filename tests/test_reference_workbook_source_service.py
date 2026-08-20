import os

from src.services.reference_workbook_source_service import (
    GraphReferenceWorkbookSource,
    ReferenceWorkbookSourceConfig,
    load_reference_workbook_source_config,
)


class Client:
    def __init__(self):
        self.operations = []

    def get(self, endpoint, params=None, operation_category=None):
        self.operations.append(operation_category)
        return {"eTag": "synthetic-version"}

    def get_content(self, endpoint, operation_category=None):
        self.operations.append(operation_category)
        return b"SYNTHETIC-WORKBOOK"


def test_graph_source_uses_metadata_then_binary_download_boundary():
    client = Client()
    source = GraphReferenceWorkbookSource(
        client=client,
        config=ReferenceWorkbookSourceConfig("synthetic-drive", "synthetic-item"),
    )
    assert source.get_version() == "synthetic-version"
    assert source.download() == b"SYNTHETIC-WORKBOOK"
    assert client.operations == ["reference_metadata", "reference_download"]


def test_graph_source_rejects_missing_safe_version():
    client = Client()
    client.get = lambda *args, **kwargs: {}
    source = GraphReferenceWorkbookSource(
        client=client,
        config=ReferenceWorkbookSourceConfig("synthetic-drive", "synthetic-item"),
    )
    try:
        source.get_version()
    except ValueError:
        pass
    else:
        raise AssertionError("Missing version must fail safely.")


def test_environment_contract_requires_drive_and_item_without_exposing_values():
    names = ("GRAPH_REFERENCE_DRIVE_ID", "GRAPH_REFERENCE_ITEM_ID")
    previous = {name: os.environ.get(name) for name in names}
    try:
        os.environ[names[0]] = "SYNTHETIC-PRIVATE-DRIVE"
        os.environ[names[1]] = "SYNTHETIC-PRIVATE-ITEM"
        config = load_reference_workbook_source_config()
        assert config.drive_id == "SYNTHETIC-PRIVATE-DRIVE"
        assert config.item_id == "SYNTHETIC-PRIVATE-ITEM"
        assert "SYNTHETIC-PRIVATE" not in repr(config)

        del os.environ[names[1]]
        try:
            load_reference_workbook_source_config()
        except ValueError as error:
            message = str(error)
            assert names[0] in message and names[1] in message
            assert "SYNTHETIC-PRIVATE" not in message
        else:
            raise AssertionError("Incomplete reference configuration must fail.")
    finally:
        for name, value in previous.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value


def test_last_modified_metadata_is_safe_version_fallback():
    client = Client()
    client.get = lambda *args, **kwargs: {
        "lastModifiedDateTime": "2026-01-01T00:00:00Z"
    }
    source = GraphReferenceWorkbookSource(
        client=client,
        config=ReferenceWorkbookSourceConfig("synthetic-drive", "synthetic-item"),
    )
    assert source.get_version() == "2026-01-01T00:00:00Z"


if __name__ == "__main__":
    tests = [value for name, value in list(globals().items()) if name.startswith("test_")]
    for test in tests:
        test()
    print(f"Passed: {len(tests)}")
    print("Failed: 0")
    print("Classification: synthetic deterministic/mock")
    print("Microsoft Graph: mocked; live integration not called")
    print("PHI handling: identifiers are synthetic and not printed")
