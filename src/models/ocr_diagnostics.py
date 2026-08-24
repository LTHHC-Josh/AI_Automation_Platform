from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(repr=False)
class OCRRunDiagnostics:
    """PHI-safe operational measurements for one OCR provider request."""

    provider: str = "paddle"
    input_type: str = "unknown"
    file_size_bucket: str = "unknown"
    cache_category: str = "unknown"
    fingerprint_seconds: float | None = None
    cache_lookup_seconds: dict[str, float] = field(default_factory=dict)
    engine_creation_count: int = 0
    engine_init_seconds: float | None = None
    paddle_version: str = "unknown"
    paddleocr_version: str = "unknown"
    model_family: str = "default_unpinned_en"
    configuration: dict[str, Any] = field(default_factory=dict)
    device_type: str = "unknown"
    thread_counts: dict[str, int | None] = field(default_factory=dict)
    global_flags_use_mkldnn: bool | None = None
    effective_paddleocr_enable_mkldnn: bool | None = None
    effective_cpu_threads: int | None = None
    effective_mkldnn_cache_capacity: int | None = None
    effective_inference_engine: str = "unknown"
    predict_call_count: int = 0
    document_submission_count: int = 0
    predict_return_seconds: float | None = None
    result_behavior: str = "not_run"
    result_consumption_seconds: float | None = None
    result_count: int = 0
    page_ordinals_unique: bool = True
    page_timings: list[dict[str, Any]] = field(default_factory=list)
    batch_metadata: dict[str, Any] = field(default_factory=dict)
    render_metadata: dict[str, Any] = field(default_factory=dict)
    result_conversion_count: int = 0
    result_conversion_seconds: float = 0.0
    recognized_text_traversal_count: int = 0
    recognized_text_traversal_seconds: float = 0.0
    visited_container_count: int = 0
    recognized_block_count: int = 0
    page_block_construction_seconds: float = 0.0
    flat_text_assembly_seconds: float = 0.0
    flat_cache_write_seconds: float | None = None
    structured_serialization_seconds: float | None = None
    structured_cache_write_seconds: float | None = None
    flat_serialized_size_bucket: str = "not_written"
    structured_serialized_size_bucket: str = "not_written"
    extra_predict_calls_during_cache_writes: int = 0
    application_source_rereads_during_cache_writes: int = 0
    repeated_prediction_detected: bool = False
    repeated_conversion_detected: bool = False

    def to_safe_dict(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "input_type": self.input_type,
            "file_size_bucket": self.file_size_bucket,
            "cache_category": self.cache_category,
            "fingerprint_seconds": self.fingerprint_seconds,
            "cache_lookup_seconds": dict(self.cache_lookup_seconds),
            "engine_creation_count": self.engine_creation_count,
            "engine_init_seconds": self.engine_init_seconds,
            "paddle_version": self.paddle_version,
            "paddleocr_version": self.paddleocr_version,
            "model_family": self.model_family,
            "configuration": dict(self.configuration),
            "device_type": self.device_type,
            "thread_counts": dict(self.thread_counts),
            "global_flags_use_mkldnn": self.global_flags_use_mkldnn,
            "effective_paddleocr_enable_mkldnn": (
                self.effective_paddleocr_enable_mkldnn
            ),
            "effective_cpu_threads": self.effective_cpu_threads,
            "effective_mkldnn_cache_capacity": (
                self.effective_mkldnn_cache_capacity
            ),
            "effective_inference_engine": self.effective_inference_engine,
            "predict_call_count": self.predict_call_count,
            "document_submission_count": self.document_submission_count,
            "predict_return_seconds": self.predict_return_seconds,
            "result_behavior": self.result_behavior,
            "result_consumption_seconds": self.result_consumption_seconds,
            "result_count": self.result_count,
            "page_ordinals_unique": self.page_ordinals_unique,
            "page_timings": [dict(item) for item in self.page_timings],
            "batch_metadata": dict(self.batch_metadata),
            "render_metadata": dict(self.render_metadata),
            "result_conversion_count": self.result_conversion_count,
            "result_conversion_seconds": self.result_conversion_seconds,
            "recognized_text_traversal_count": self.recognized_text_traversal_count,
            "recognized_text_traversal_seconds": self.recognized_text_traversal_seconds,
            "visited_container_count": self.visited_container_count,
            "recognized_block_count": self.recognized_block_count,
            "page_block_construction_seconds": self.page_block_construction_seconds,
            "flat_text_assembly_seconds": self.flat_text_assembly_seconds,
            "flat_cache_write_seconds": self.flat_cache_write_seconds,
            "structured_serialization_seconds": self.structured_serialization_seconds,
            "structured_cache_write_seconds": self.structured_cache_write_seconds,
            "flat_serialized_size_bucket": self.flat_serialized_size_bucket,
            "structured_serialized_size_bucket": self.structured_serialized_size_bucket,
            "extra_predict_calls_during_cache_writes": (
                self.extra_predict_calls_during_cache_writes
            ),
            "application_source_rereads_during_cache_writes": (
                self.application_source_rereads_during_cache_writes
            ),
            "repeated_prediction_detected": self.repeated_prediction_detected,
            "repeated_conversion_detected": self.repeated_conversion_detected,
        }
