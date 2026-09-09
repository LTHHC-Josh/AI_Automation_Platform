"""Protected source binding and evidence-only correction replay.

This adapter never creates rows, writes comments, executes code, or trusts model
proposals as source evidence. Uncertain external updates are readback-only.
"""
from pathlib import Path
import smartsheet
from src.services.local_correction_memory_service import LocalCorrectionStore
from src.services.document_fingerprint_service import DocumentFingerprintService
from src.services.document_attachment_naming_service import DocumentAttachmentNamingService
from src.services.smartsheet_review_configuration_service import SmartsheetReviewConfigurationService
from src.services.smartsheet_review_row_mapping_service import SmartsheetReviewRowMappingService
from src.services.smartsheet_destination_validation_service import SmartsheetDestinationValidationService
from src.models.smartsheet_mapping import SmartsheetRowMappingResult
from src.services.smartsheet_feedback_case_storage_service import stable_digest

class LocalCorrectionSource:
    ROOT = Path(__file__).resolve().parents[2]
    def __init__(self, store=None):
        self.store = store or LocalCorrectionStore()

    def bind(self, *, row_id, work_item, state):
        path = Path(work_item.local_path).resolve()
        if not path.is_relative_to(self.ROOT / "data/incoming"):
            raise ValueError("correction_source_outside_scope")
        fingerprint = DocumentFingerprintService().calculate(path)
        if not fingerprint.success or fingerprint.fingerprint != work_item.document_key:
            raise ValueError("correction_source_identity_unproven")
        if state.stage != "attachment_written" or state.smartsheet_row_id != row_id:
            raise ValueError("correction_row_identity_unproven")
        old = self.store.load("source", str(row_id))
        record = {"job_key":work_item.job_key, "fingerprint":fingerprint.fingerprint,
                  "path":str(path), "attachment_name":state.attachment_filename}
        if old and any(old.get(k) != v for k,v in record.items()):
            raise ValueError("correction_source_binding_conflict")
        self.store.save("source", str(row_id), record)

    def get(self, row_id):
        record = self.store.load("source", str(row_id))
        if not record:
            record = self._index_existing(row_id)
        path = Path(record["path"]).resolve()
        if not path.is_relative_to(self.ROOT / "data/incoming"):
            raise ValueError("correction_source_outside_scope")
        result = DocumentFingerprintService().calculate(path)
        if not result.success or result.fingerprint != record["fingerprint"]:
            raise ValueError("correction_source_changed")
        return record

    def _index_existing(self, row_id):
        from src.services.mailbox_document_job_state_service import MailboxDocumentJobStateService, MailboxDocumentWorkItem
        jobs = MailboxDocumentJobStateService(self.ROOT / "data/mailbox_processing_state/jobs")
        matches = []
        # Migration only: subsequent correction generations use the direct sealed index.
        for path in jobs.state_dir.glob("*.json"):
            loaded = jobs.load(path.stem)
            if not loaded.success:
                raise ValueError("correction_legacy_state_unprovable")
            if loaded.state.smartsheet_row_id == row_id:
                matches.append(loaded.state)
        if len(matches) != 1 or matches[0].stage != "attachment_written":
            raise ValueError("correction_legacy_identity_unproven")
        state = matches[0]
        paths = []
        incoming = self.ROOT / "data/incoming"
        # Acquisition's committed path contract is fingerprint + safe extension.
        # Probe only those bounded exact paths, never scan every patient's file.
        for extension in sorted(DocumentAttachmentNamingService.SAFE_EXTENSIONS):
            path = incoming / (state.document_key + extension)
            if (not path.is_file() or path.suffix.lower() not in DocumentAttachmentNamingService.SAFE_EXTENSIONS
                    or not path.resolve().is_relative_to(incoming)):
                continue
            result = DocumentFingerprintService().calculate(path)
            if result.success and result.fingerprint == state.document_key:
                paths.append(path)
                if len(paths) > 1:
                    break
        if len(paths) != 1:
            raise ValueError("correction_legacy_source_unproven")
        item = MailboxDocumentWorkItem(
            state.job_key, state.message_key, state.attachment_key,
            state.document_key, paths[0])
        self.bind(row_id=row_id, work_item=item, state=state)
        return self.store.load("source", str(row_id))

class EvidenceOnlyCorrectionExecutor:
    FIELD_COLUMNS = {
        "Authorization Number":("Authorization #", "Authorization # Conf."),
        "Authorization Status":("Authorization Status",),
        "Service Code":("Service Codes", "Service Codes Conf."),
        "Diagnosis":("Diagnosis Codes", "Diagnosis Codes Conf."),
        "Start Date":("Start Date", "Start Date Conf."),
        "End Date":("End Date", "End Date Conf."),
        "Authorized Units":("Authorized Units", "Authorized Units Conf."),
        "Authorization Unit":("Authorized Units", "Authorized Units Conf."),
        "Hours":("Hours", "Hours Conf."),
        "Days Per Week":("Days Per Week", "Days Per Week Conf."),
        "Document Category":("AI Document Category", "AI Classification Confidence"),
        "Document Subtype":("AI Document Subtype",),
        "Review Status":("AI Review Status", "AI Review Required"),
        "Review Reason":("AI Review Reasons",),
        # Service lines have no editable row-shaped production column. Revalidate
        # their evidence and review projection; never flatten their child values
        # into top-level quantity/date/status fields.
        "Service Line":("AI Review Reasons", "AI Review Status", "AI Review Required"),
        "Filename":(),
    }
    NAMING_ONLY_FIELDS = frozenset({
        "Patient Name", "Payer", "Service Description", "Program", "Modifier", "Posted Date",
    })
    def __init__(self, *, client, source=None, processor_factory=None, configuration=None):
        self.client = client
        self.source = source or LocalCorrectionSource()
        self.processor_factory = processor_factory or self._processor
        self.configuration = configuration or SmartsheetReviewConfigurationService()
        self.naming = DocumentAttachmentNamingService()

    @staticmethod
    def _processor():
        from src.document_processing.document_processor import DocumentProcessor
        return DocumentProcessor()

    def _values(self, row_id, columns):
        if not columns:
            return {}
        _, row = self.client.get_selected_row(row_id=row_id, column_ids=list(columns.values()))
        raw = {c.column_id:c.value for c in row.cells}
        return {name:raw.get(column) for name,column in columns.items()}

    def prepare(self, row_id, context, analysis):
        naming_only = self.NAMING_ONLY_FIELDS if "Filename" in analysis.affected_fields else frozenset()
        if not analysis.affected_fields or any(
                x not in self.FIELD_COLUMNS and x not in naming_only for x in analysis.affected_fields):
            raise ValueError("correction_field_not_mapped")
        binding = self.source.get(row_id)
        # Use the existing full local pipeline; no direct raw candidate mapping.
        processor = self.processor_factory()
        # Only a fixed, PHI-free guidance code, not reviewer prose or values.
        provider = getattr(getattr(processor, "llm", None), "provider", None)
        if provider is not None:
            provider.correction_guidance_code = analysis.behavior_code
        document = processor.process(Path(binding["path"]), ocr_cache_only=True)
        config = self.configuration.resolve(document_type=document.document_type)
        if not config.success:
            raise ValueError("correction_schema_unavailable")
        mapping = SmartsheetReviewRowMappingService().map(
            document.review_output, list(config.policies), run_type=context.get("Run Type", ""))
        if not mapping.ready_for_write:
            raise ValueError("correction_mapping_unavailable")
        selected = {name for field in analysis.affected_fields for name in self.FIELD_COLUMNS.get(field, ())}
        # Shared final review/minimum must agree with recomputed selected production
        # values. Do not recompute aggregate metadata over a mixed old/new row.
        dependent = {"AI Minimum Field Confidence", "AI Review Reasons", "AI Review Status", "AI Review Required"}
        if selected:
            all_production = set(mapping.values) | set(mapping.omitted_columns)
            unchanged = all_production - selected - dependent - {"AI Correction", "Run Type"}
            if any(context.get(name) != mapping.values.get(name) for name in unchanged):
                raise ValueError("correction_unrelated_field_change")
            selected |= dependent
        desired = {name:mapping.values.get(name) for name in selected}
        before = self._values(row_id, {n:config.available_columns[n] for n in selected})
        updates = {name:value for name,value in desired.items() if before.get(name) != value}
        self._validate(updates, config)
        plan = {"updates":updates, "before":before, "attachment":None,
                "source_fingerprint":binding["fingerprint"]}
        if "Filename" in analysis.affected_fields:
            prepared = self.naming.prepare(source_path=binding["path"],
                                          filename_policy_result=document.filename_assembly_result.policy_result)
            if not prepared.success:
                raise ValueError("correction_filename_unavailable")
            try:
                name = prepared.temporary_path.name
            finally:
                self.naming.cleanup(prepared.temporary_path)
            attachments = self._attachments(row_id)
            expected_name = binding.get("current_attachment_name", binding["attachment_name"])
            matches = [a for a in attachments if a["name"] == expected_name
                       and (not binding.get("current_attachment_id")
                            or a["id"] == binding["current_attachment_id"])]
            if len(matches) != 1:
                raise ValueError("correction_attachment_identity_unproven")
            if name != matches[0]["name"]:
                plan["attachment"] = {"id":matches[0]["id"], "before_name":matches[0]["name"], "name":name}
        if not updates and plan["attachment"] is None:
            raise ValueError("correction_no_verified_change")
        return plan

    def _validate(self, updates, config):
        if not updates:
            return
        # Null explicitly clears a formerly populated approved production cell.
        allowed = {n for names in self.FIELD_COLUMNS.values() for n in names} | {
            "AI Minimum Field Confidence", "AI Review Reasons", "AI Review Status", "AI Review Required"}
        if not set(updates) <= allowed:
            raise ValueError("correction_write_scope_invalid")
        surrogate = {}
        for name,value in updates.items():
            kind = config.available_column_types.get(name)
            if value is None:
                if kind not in {"TEXT_NUMBER", "DATE", "CHECKBOX"}:
                    raise ValueError("correction_clear_type_invalid")
                surrogate[name] = {"TEXT_NUMBER":"", "DATE":"2000-01-01", "CHECKBOX":False}[kind]
            else:
                surrogate[name] = value
        result = SmartsheetDestinationValidationService().validate(
            SmartsheetRowMappingResult(values=surrogate, ready_for_write=True),
            config.available_columns, config.available_column_types, config.available_system_column_types)
        if not result.ready_for_write:
            raise ValueError("correction_type_validation_failed")

    def _attachments(self, row_id):
        response = self.client.client.Attachments.list_row_attachments(
            self.client.sheet_id, row_id, include_all=True)
        data = getattr(response, "data", None)
        if not isinstance(data, list):
            raise ValueError("correction_attachment_response_invalid")
        items = []
        for a in data:
            if getattr(a, "attachment_type", None) != "FILE":
                continue
            identity, name = getattr(a, "id", None), getattr(a, "name", None)
            if type(identity) is not int or identity <= 0 or not isinstance(name, str):
                raise ValueError("correction_attachment_response_invalid")
            items.append({"id":identity,"name":name})
        return items

    def apply(self, row_id, plan):
        binding = self.source.get(row_id)
        if binding["fingerprint"] != plan["source_fingerprint"]:
            raise ValueError("correction_source_changed")
        config = self.configuration.resolve()
        if not config.success:
            raise ValueError("correction_schema_unavailable")
        self._validate(plan["updates"], config)
        columns = {n:config.available_columns[n] for n in plan["before"]}
        transaction_key = stable_digest({"row":row_id, "plan":plan})
        transaction = self.source.store.load("audit", transaction_key) or {
            "row_intent":False, "row_confirmed":False, "attachment_intent":False}
        expected = dict(plan["before"], **plan["updates"])
        current_values = self._values(row_id, columns)
        if current_values == expected:
            transaction["row_confirmed"] = True
            self.source.store.save("audit", transaction_key, transaction)
        elif current_values != plan["before"]:
            raise ValueError("correction_row_changed")
        elif transaction["row_intent"]:
            raise ValueError("correction_row_outcome_unresolved")
        if plan["updates"] and not transaction["row_confirmed"]:
            transaction["row_intent"] = True
            self.source.store.save("audit", transaction_key, transaction)
            self.client.update_row(row_id, {
                config.available_columns[n]:(smartsheet.models.ExplicitNull() if v is None else v)
                for n,v in plan["updates"].items()})
            if self._values(row_id, {n:columns[n] for n in plan["updates"]}) != plan["updates"]:
                raise ValueError("correction_row_outcome_unresolved")
            transaction["row_confirmed"] = True
            self.source.store.save("audit", transaction_key, transaction)
        attachment = plan["attachment"]
        if attachment:
            if transaction["attachment_intent"]:
                if self.verify(row_id, plan):
                    return
                raise ValueError("correction_attachment_outcome_unresolved")
            current = [a for a in self._attachments(row_id) if a["id"] == attachment["id"]]
            if len(current) != 1 or current[0]["name"] != attachment["before_name"]:
                raise ValueError("correction_attachment_changed")
            prepared = self.naming.prepare_technical(source_path=binding["path"], technical_name=attachment["name"])
            if not prepared.success:
                raise ValueError("correction_copy_unavailable")
            try:
                transaction["attachment_intent"] = True
                self.source.store.save("audit", transaction_key, transaction)
                with prepared.temporary_path.open("rb") as stream:
                    result = self.client.client.Attachments.attach_new_version(
                        self.client.sheet_id, attachment["id"], stream)
                item = getattr(result, "result", None)
                identity = getattr(item, "id", None)
                if type(identity) is not int or getattr(item, "name", None) != attachment["name"]:
                    raise ValueError("correction_attachment_outcome_unresolved")
                # Persist confirmation separately before workflow transition.
                self.source.store.save("audit", "attachment:" + str(row_id) + ":" + str(attachment["id"]),
                                       {"confirmed_id":identity, "name":attachment["name"]})
            finally:
                self.naming.cleanup(prepared.temporary_path)

    def resume(self, row_id, plan):
        # Each boundary has its own pre-call reservation. Re-entry can reconcile
        # a proven row and advance an unattempted attachment, never repeat a
        # reserved but unresolved request.
        self.apply(row_id, plan)

    def verify(self, row_id, plan):
        try:
            config = self.configuration.resolve()
            if not config.success:
                return False
            expected = dict(plan["before"], **plan["updates"])
            if self._values(row_id, {n:config.available_columns[n] for n in expected}) != expected:
                return False
            attachment = plan["attachment"]
            if attachment:
                # Lost upload response is NEVER retried based on a filename match.
                receipt = self.source.store.load("audit", "attachment:" + str(row_id) + ":" + str(attachment["id"]))
                if not receipt or receipt["name"] != attachment["name"]:
                    return False
                matches = [a for a in self._attachments(row_id)
                           if a["id"] == receipt["confirmed_id"] and a["name"] == receipt["name"]]
                if len(matches) != 1:
                    return False
                binding = self.source.get(row_id)
                binding["current_attachment_name"] = receipt["name"]
                binding["current_attachment_id"] = receipt["confirmed_id"]
                self.source.store.save("source", str(row_id), binding)
            return True
        except Exception:
            return False
