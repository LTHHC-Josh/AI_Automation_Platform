from src.services.reference_workbook_source_service import (
    GraphReferenceWorkbookSource,
    ReferenceWorkbookSourceConfig,
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


if __name__ == "__main__":
    tests = [value for name, value in list(globals().items()) if name.startswith("test_")]
    for test in tests:
        test()
    print(f"Passed: {len(tests)}")
    print("Failed: 0")
    print("Classification: synthetic deterministic/mock")
    print("Microsoft Graph: mocked; live integration not called")
    print("PHI handling: identifiers are synthetic and not printed")
