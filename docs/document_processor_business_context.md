# Document Processor Business Context

`DocumentProcessorBusinessContext` is the PHI-free, immutable, versioned
business vocabulary shared by the live Document Processor and DP Training.
The structured Python source is
`src/models/document_processor_business_context.py`; the validating and
role-specific renderer is
`src/services/document_processor_business_context_service.py`.

The context explains business meaning and model constraints. It does not move
authority into the model. Classification resolution, evidence validation,
business rules, filename assembly, review decisions, and external writes
remain deterministic code boundaries.

## Version governance

`BUSINESS_CONTEXT_VERSION` is a positive integer. Increment it only when the
semantic digest changes because an approved generalized business rule,
taxonomy, naming rule, external dependency, or inference prohibition changes.
Formatting-only renderer changes do not require an increment. A semantic
change requires the structured source change, deterministic enforcement where
applicable, synthetic regressions, tracker/continuity updates, Git safety, and
a real retest when production behavior is affected.

The safe version is associated with classification and extraction request
metrics, intake naming/filename results, Prefect DP Training summaries,
protected correction proposals, and sanitized implementation tasks. Prompt or
rendered-context text is never written to Prefect or ordinary logs.

## Role integration

| Model role | Prompt owner | Shared view | Role-specific responsibility |
| --- | --- | --- | --- |
| Document classification | `OllamaProvider._classification_prompt` | `classification` | Return one candidate family/subtype and independent confidences. |
| Extraction attempts 1 and 2 | `OllamaProvider._extraction_prompt` | `extraction` | Extract each attempt independently; never merge attempts or replace validation. |
| Intake naming/subtype | Extraction candidate plus `IntakeDocumentNamingService` | `intake_naming_subtype` vocabulary is authoritative to deterministic naming; extraction receives the overlapping subtype rules | Resolve canonical intake tokens and filename outcomes deterministically. There is no separate naming model call. |
| Structural learning | `OllamaProvider._learning_analysis_prompt` | `structural_learning` | Produce protected structural observations only. |
| DP Training correction | `OllamaProvider.analyze_correction_context` | `dp_training_correction` | Interpret untrusted reviewer intent into the constrained correction contract. |

Each renderer selects only the sections needed for its role. Tests enforce a
compact deterministic rendering and a strict DP Training context-size ceiling.

## Consolidated authority

The shared source owns the canonical document-family vocabulary, top-level
naming tokens, authorization intake subtype tokens and aliases, `AUTH INIT`
external-context declaration, approved filename placeholders and outcomes,
field-state names, confidence policies, quantity/unit vocabulary and default,
correction taxonomy, and training interpretation semantics. Services derive
their constants from this source rather than maintaining prompt-only copies.

Reviewer comments are never incorporated into this source automatically. A
human-approved correction can only change shared context through the bounded
implementation workflow, and Codex must generalize the behavior, identify the
durable layer, add synthetic tests, and report whether the context version was
changed. Patient-specific facts and reviewer-provided values are prohibited.
