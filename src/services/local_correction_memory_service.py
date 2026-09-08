"""Sealed local correction records and bounded, approved document-type lessons."""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
from uuid import uuid4
from src.services.windows_dpapi_service import protect_current_user, unprotect_current_user
from src.services.document_processor_training_contracts import BEHAVIOR_CODES, DOCUMENT_CATEGORY_CONCEPTS

class LocalCorrectionStore:
    ROOT = Path(__file__).resolve().parents[2] / "data/smartsheet_feedback/local_corrections"
    PURPOSE = b"LTHHC local correction workflow v1"

    def __init__(self, root=None, *, protect=None, unprotect=None):
        self.root = Path(root or self.ROOT)
        self.protect = protect or (lambda b: protect_current_user(b, purpose=self.PURPOSE))
        self.unprotect = unprotect or (lambda b: unprotect_current_user(b, purpose=self.PURPOSE))

    def _path(self, kind, identity):
        if kind not in {"case", "source", "lesson", "audit"}:
            raise ValueError("local_record_kind_invalid")
        digest = hashlib.sha256(str(identity).encode("utf-8")).hexdigest()
        return self.root / kind / (digest + ".sealed")

    def load(self, kind, identity):
        path = self._path(kind, identity)
        if not path.exists():
            return None
        try:
            result = json.loads(self.unprotect(path.read_bytes()).decode("utf-8"))
            if not isinstance(result, dict) or result.get("schema_version") != 1:
                raise ValueError()
            return result
        except Exception:
            raise ValueError("local_record_unavailable") from None

    def save(self, kind, identity, value):
        path = self._path(kind, identity)
        path.parent.mkdir(parents=True, exist_ok=True)
        encoded = self.protect(json.dumps(
            dict(value, schema_version=1), sort_keys=True, ensure_ascii=False,
            allow_nan=False, separators=(",", ":"),
        ).encode("utf-8"))
        temporary = path.with_name("." + uuid4().hex + ".tmp")
        try:
            with temporary.open("xb") as stream:
                stream.write(encoded)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, path)
        finally:
            temporary.unlink(missing_ok=True)

class ApprovedDocumentLessons:
    """One direct-indexed file per family; never scan correction history in inference."""
    MAX_ACTIVE = 8
    MAX_RENDERED_CHARS = 1800

    def __init__(self, store=None):
        self.store = store or LocalCorrectionStore()

    @staticmethod
    def family(value):
        from src.models.document_processor_business_context import DOCUMENT_PROCESSOR_BUSINESS_CONTEXT
        text = str(value or "").strip().lower()
        aliases = {token.lower(): family for family, token in DOCUMENT_PROCESSOR_BUSINESS_CONTEXT.top_level_naming_tokens}
        for item in DOCUMENT_PROCESSOR_BUSINESS_CONTEXT.document_taxonomy:
            aliases.update({route: item.family for _, route in item.legacy_routes})
        text = aliases.get(text, text)
        return text if text in DOCUMENT_CATEGORY_CONCEPTS and text not in {"unknown", "not_applicable", "other"} else None

    def approve(self, *, family, code, receipt, resolution_verified):
        family = self.family(family)
        if family is None or code not in BEHAVIOR_CODES or code in {"needs_investigation", "external_dependency"} or resolution_verified is not True:
            raise ValueError("lesson_not_eligible")
        if not isinstance(receipt, str) or len(receipt) != 64 or any(c not in "0123456789abcdef" for c in receipt):
            raise ValueError("lesson_receipt_invalid")
        data = self.store.load("lesson", family) or {"active": []}
        # Fixed rule vocabulary only. Never model prose, row values, comments, or PHI.
        active = [x for x in data["active"] if x in BEHAVIOR_CODES and x != code]
        active = (active + [code])[-self.MAX_ACTIVE:]
        self.store.save("audit", receipt, {"family": family, "code": code, "approved": True})
        self.store.save("lesson", family, {"active": active})

    def render(self, family):
        family = self.family(family)
        if family is None:
            return ""
        try:
            data = self.store.load("lesson", family)
            if not data:
                return ""
            active = data.get("active")
            if not isinstance(active, list) or len(active) > self.MAX_ACTIVE:
                return ""
            if any(not isinstance(x, str) or x not in BEHAVIOR_CODES for x in active):
                return ""
            lines = []
            for code in dict.fromkeys(active):
                line = BEHAVIOR_CODES[code]
                if len("\n".join(lines + [line])) > self.MAX_RENDERED_CHARS:
                    break
                lines.append(line)
            return "\n".join(lines)
        except Exception:
            # Unavailable learning never weakens the base deterministic validator.
            return ""
