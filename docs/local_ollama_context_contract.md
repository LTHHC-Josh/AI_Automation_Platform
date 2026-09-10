# Local Ollama complete-input contract

All production local-model roles share request contract 1. No cloud model or
new model download is introduced. Before sending protected content, the provider
verifies the loopback endpoint, local model identity, supported context capacity
and the installed API contract. Currently verified Ollama version: **0.33.3**.
Another version fails closed until its no-truncation semantics are verified.

Each native `/api/chat` request explicitly supplies:

- `options.num_ctx`: `OLLAMA_CONTEXT_TOKENS`, default **8192**.
- `options.num_predict`: `OLLAMA_MAX_OUTPUT_TOKENS`, default **4096**.
- `truncate: false`: never silently discard input messages or document tokens.
- `shift: false`: never discard earlier context during generation.

The positive integer budgets are operational configuration, not acceptance or
confidence thresholds. Output must fit within the configured context, which
must fit the model's authoritative capacity. The 8K default accommodates the
observed complete retry input (4,426 tokens) and response (1,337 tokens); it does
not guarantee every future document fits. Larger supported documents may require
an explicitly configured larger budget after local memory/performance testing.
Do not change the model server's global defaults or shorten/truncate a document
as an automatic fallback. No automatic context escalation or extra retry occurs.

Only `done=true` and `done_reason=stop` responses can become candidates.
Incomplete output, context overflow, unverified API versions and transport errors
fail with fixed PHI-safe categories. Values, response bodies and exception text
are not diagnostics. Safe metrics retain the request contract, budgets, token
counts and no-truncate/no-shift flags. The two extraction candidates remain
independent; validation thresholds and reference/naming policy are unchanged.

The retained failed retry was matched to an Ollama truncation event: 4,426 input
tokens became 2,050. A successful-looking response did not prove complete input.
Post-fix synthetic local checks prove oversized input is rejected and a valid
request runs with a read-back runtime context of 8192. Model-quality and live
correction acceptance are separate checks, not implied by those API probes.

Preparation contract 6 permits one reserved same-case re-entry only for a
version-5 blocked authorization filename case with no plan, the unrelated-field
failure, and applicable subtype/service correction scope. Both human approvals
must be unchecked. Existing intent may be reused, but document evidence must
be revalidated under the corrected input contract. Reservation precedes inference;
failure or interruption cannot cause unchanged polling to repeat it. Applied,
uncertain or other failure scopes are not rearmed. Comments and approval controls
are never rewritten, and source-only re-entry does not refresh the review snapshot.

## API evidence

- [Ollama context configuration](https://docs.ollama.com/faq#how-can-i-specify-the-context-window-size)
- [Verified 0.33.3 request fields](https://github.com/ollama/ollama/blob/v0.33.3/api/types.go)
- [Verified 0.33.3 chat handling](https://github.com/ollama/ollama/blob/v0.33.3/server/routes.go)
