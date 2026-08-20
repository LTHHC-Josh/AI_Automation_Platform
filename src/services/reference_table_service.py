from dataclasses import dataclass
import json
import os
from pathlib import Path
import tempfile
from typing import Any
from xml.etree import ElementTree
from zipfile import BadZipFile, ZipFile


MAIN_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
OFFICE_REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"


def _key(*values: Any) -> tuple[str, ...]:
    return tuple(" ".join(str(value or "").strip().upper().split()) for value in values)


@dataclass(frozen=True)
class LookupResult:
    resolved: bool
    value: str | None = None
    status: str = "not_resolved"


class PayorReferenceTable:
    def __init__(self, values: dict[tuple[str, str], str]): self._values = dict(values)
    def lookup(self, payor_name: Any, key_field: Any) -> LookupResult:
        value = self._values.get(_key(payor_name, key_field))
        return LookupResult(value is not None, value, "resolved" if value is not None else "not_resolved")


class ServiceReferenceTable:
    def __init__(self, values: dict[tuple[str, str, str], set[str]]):
        self._values = {
            key: frozenset(results)
            for key, results in values.items()
        }

    def lookup(self, code: Any, modifier: Any, program: Any) -> LookupResult:
        values = self._values.get(_key(code, modifier, program))
        if not values:
            return LookupResult(False, None, "not_resolved")
        if len(values) != 1:
            return LookupResult(False, None, "ambiguous")
        return LookupResult(True, next(iter(values)), "resolved")


class DocumentTypeReferenceTable:
    def __init__(self, values: dict[tuple[str], str]): self._values = dict(values)
    def lookup(self, document_type: Any) -> LookupResult:
        value = self._values.get(_key(document_type))
        return LookupResult(value is not None, value, "resolved" if value is not None else "not_resolved")


@dataclass(frozen=True)
class ReferenceTables:
    payors: PayorReferenceTable
    services: ServiceReferenceTable
    document_types: DocumentTypeReferenceTable | None = None


@dataclass(frozen=True)
class ReferenceLoadResult:
    success: bool
    tables: ReferenceTables | None
    status: str
    payor_row_count: int = 0
    service_row_count: int = 0
    document_type_row_count: int = 0


class ReferenceTableLoader:
    REQUIRED = {
        "PAYOR LISTING": ("PAYOR NAME", "KEY FIELD", "RESULTS", "TYPE", "DESCRIPTION"),
        "SERVICES LISTING": ("HCPCS/BILL CODE", "MODIFIERS", "PROGRAM", "DESCRIPTION", "SERVICES GROUP", "CFC OPTION", "WAIVER OPTION", "NAMING CONVENTION"),
    }
    DOCUMENT_COLUMNS = ("DOCUMENT TYPE", "NAMING CONVENTION", "DESCRIPTION")

    def load(self, path: str | Path) -> ReferenceLoadResult:
        try:
            sheets = self._read_xlsx(Path(path))
            if any(name not in sheets for name in self.REQUIRED):
                return self._failure("required_sheet_missing")
            payors = self._build(sheets["PAYOR LISTING"], self.REQUIRED["PAYOR LISTING"], ("PAYOR NAME", "KEY FIELD"), "RESULTS")
            services = self._build_services(sheets["SERVICES LISTING"])
            document_types = None
            document_values = {}
            if "DOCUMENT TYPES" in sheets:
                document_values = self._build(sheets["DOCUMENT TYPES"], self.DOCUMENT_COLUMNS, ("DOCUMENT TYPE",), "NAMING CONVENTION")
                document_types = DocumentTypeReferenceTable(document_values)
            service_mapping_count = sum(len(values) for values in services.values())
            return ReferenceLoadResult(True, ReferenceTables(PayorReferenceTable(payors), ServiceReferenceTable(services), document_types), "valid", len(payors), service_mapping_count, len(document_values))
        except (OSError, ValueError, KeyError, BadZipFile, ElementTree.ParseError):
            return self._failure("reference_invalid")

    @staticmethod
    def _failure(status: str) -> ReferenceLoadResult:
        return ReferenceLoadResult(False, None, status)

    def _build(self, rows, required_columns, key_columns, result_column):
        if not rows:
            raise ValueError("missing header")
        headers = [_key(value)[0] for value in rows[0]]
        if any(column not in headers for column in required_columns):
            raise ValueError("missing column")
        positions = {header: position for position, header in enumerate(headers)}
        values = {}
        for row in rows[1:]:
            padded = list(row) + [""] * (len(headers) - len(row))
            if not any(str(value or "").strip() for value in padded):
                continue
            lookup_key = _key(*(padded[positions[column]] for column in key_columns))
            result = str(padded[positions[result_column]] or "").strip()
            if not lookup_key[0] or not result or lookup_key in values:
                raise ValueError("malformed or ambiguous mapping")
            values[lookup_key] = result
        return values

    def _build_services(self, rows):
        required_columns = self.REQUIRED["SERVICES LISTING"]
        if not rows:
            raise ValueError("missing header")
        headers = [_key(value)[0] for value in rows[0]]
        if any(column not in headers for column in required_columns):
            raise ValueError("missing column")
        positions = {header: position for position, header in enumerate(headers)}
        values: dict[tuple[str, str, str], set[str]] = {}
        for row in rows[1:]:
            padded = list(row) + [""] * (len(headers) - len(row))
            if not any(str(value or "").strip() for value in padded):
                continue
            lookup_key = _key(*(
                padded[positions[column]]
                for column in ("HCPCS/BILL CODE", "MODIFIERS", "PROGRAM")
            ))
            result = str(padded[positions["NAMING CONVENTION"]] or "").strip()
            if not lookup_key[0] or not result:
                raise ValueError("malformed mapping")
            values.setdefault(lookup_key, set()).add(result)
        return values

    def _read_xlsx(self, path: Path) -> dict[str, list[list[str]]]:
        with ZipFile(path) as archive:
            shared = self._shared_strings(archive)
            workbook = ElementTree.fromstring(archive.read("xl/workbook.xml"))
            relationships = ElementTree.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
            targets = {node.attrib["Id"]: node.attrib["Target"] for node in relationships.findall(f"{{{REL_NS}}}Relationship")}
            sheets = {}
            for sheet in workbook.findall(f".//{{{MAIN_NS}}}sheet"):
                relation_id = sheet.attrib[f"{{{OFFICE_REL_NS}}}id"]
                target = targets[relation_id].lstrip("/")
                archive_path = target if target.startswith("xl/") else f"xl/{target}"
                sheets[sheet.attrib["name"].strip().upper()] = self._worksheet(archive.read(archive_path), shared)
            return sheets

    @staticmethod
    def _shared_strings(archive: ZipFile) -> list[str]:
        try: root = ElementTree.fromstring(archive.read("xl/sharedStrings.xml"))
        except KeyError: return []
        return ["".join(node.text or "" for node in item.findall(f".//{{{MAIN_NS}}}t")) for item in root.findall(f"{{{MAIN_NS}}}si")]

    @staticmethod
    def _worksheet(content: bytes, shared: list[str]) -> list[list[str]]:
        root = ElementTree.fromstring(content)
        output = []
        for row in root.findall(f".//{{{MAIN_NS}}}row"):
            values = []
            for cell in row.findall(f"{{{MAIN_NS}}}c"):
                reference = cell.attrib.get("r", "A1")
                column = 0
                for character in reference:
                    if not character.isalpha(): break
                    column = column * 26 + ord(character.upper()) - 64
                while len(values) < column - 1: values.append("")
                value_node = cell.find(f"{{{MAIN_NS}}}v")
                value = "" if value_node is None else value_node.text or ""
                if cell.attrib.get("t") == "s": value = shared[int(value)]
                elif cell.attrib.get("t") == "inlineStr": value = "".join(node.text or "" for node in cell.findall(f".//{{{MAIN_NS}}}t"))
                values.append(value)
            output.append(values)
        return output


@dataclass(frozen=True)
class ReferenceRefreshResult:
    tables: ReferenceTables | None
    source_available: bool
    refresh_attempted: bool
    refresh_succeeded: bool
    used_cache: bool
    status: str
    version: str | None = None


class ReferenceTableRefreshService:
    """Refresh an ignored local last-known-good workbook by source version."""
    def __init__(self, *, source, cache_directory: str | Path = "data/reference_cache", loader=None):
        self.source = source
        self.cache_directory = Path(cache_directory)
        self.loader = loader or ReferenceTableLoader()
        self.workbook_path = self.cache_directory / "reference_tables.xlsx"
        self.metadata_path = self.cache_directory / "metadata.json"

    def get_tables(self) -> ReferenceRefreshResult:
        cached = self.loader.load(self.workbook_path) if self.workbook_path.exists() else None
        cached_version = self._cached_version()
        try: version = str(self.source.get_version()).strip()
        except Exception:
            return ReferenceRefreshResult(cached.tables if cached and cached.success else None, False, True, False, bool(cached and cached.success), "reference_refresh_failed", cached_version)
        if cached and cached.success and version and version == cached_version:
            return ReferenceRefreshResult(cached.tables, True, False, False, True, "cache_current", version)
        try: content = self.source.download()
        except Exception:
            return ReferenceRefreshResult(cached.tables if cached and cached.success else None, True, True, False, bool(cached and cached.success), "reference_refresh_failed", cached_version)
        self.cache_directory.mkdir(parents=True, exist_ok=True)
        temporary = None
        try:
            handle, temporary_name = tempfile.mkstemp(suffix=".xlsx", dir=self.cache_directory)
            os.close(handle); temporary = Path(temporary_name); temporary.write_bytes(content)
            loaded = self.loader.load(temporary)
            if not loaded.success:
                return ReferenceRefreshResult(cached.tables if cached and cached.success else None, True, True, False, bool(cached and cached.success), "reference_invalid", cached_version)
            os.replace(temporary, self.workbook_path); temporary = None
            self.metadata_path.write_text(json.dumps({"version": version}), encoding="utf-8", newline="\n")
            return ReferenceRefreshResult(loaded.tables, True, True, True, False, "refreshed", version)
        finally:
            if temporary and temporary.exists(): temporary.unlink()

    def _cached_version(self):
        try: return str(json.loads(self.metadata_path.read_text(encoding="utf-8")).get("version") or "").strip() or None
        except (OSError, ValueError, TypeError): return None
