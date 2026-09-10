# Program Compliance Monitor — authoritative service plan and state

## Authority and resume contract

This document preserves the approved service plan, full user requirements and
acceptance criteria. The concise goal summary does not replace or reduce them.
Read AGENTS.md, concise PROJECT_STATE.md, this document, and the latest relevant
service checkpoint to resume. Full DP history is not required for compliance work.
Shared platform rules remain authoritative for safety; new explicit user direction
governs scope. Development notes are not production memory or the operational sheet.

## Recovered original-goal acceptance audit — September 10, 2026

The original implementation objective is restored through the goal-management capability,
not replaced with the later status question or this recovery instruction. Its original scope
and all destination, continuity, shared-inference and hidden-launch amendments remain binding.
The verbatim original implementation objective and full checklist remain below.

| Original acceptance criterion | Retained evidence and final audit |
| --- | --- |
| 1. Official CLASS evidence retrieved/attributed | Verified: official_baseline and local_overflow pinned-retrieval acceptance records. |
| 2. Useful incremental source-backed DSA baseline | Verified: official_baseline/current_prompt each retain three official findings. |
| 3. One TEST substantive review generation | Verified: live_test_revision records one added generation and one TEST row. |
| 4. Unchanged/cosmetic checks do not duplicate/reopen | Verified: cosmetic/unchanged tests, live TEST zero calls/writes, fresh restart zero duplicates. |
| 5. Explicit uncertainty and consolidated questions | Verified: one service-scope question; profile-confirmation and question tests. Agency facts remain unknown. |
| 6. Citation/date/actor/exception/untrusted-content tests | Verified: corresponding tests in test_program_compliance.py pass. |
| 7. Dedicated sheet finding and readback | Verified: live sheet acceptance; later readback 41 unchanged, zero creates/updates/blocked. |
| 8. Human edits survive synchronization/revision | Verified: live_test_revision human_fields_preserved plus ownership/acknowledgment tests. |
| 9. Lost-response/restart/duplicate/restore | Verified: recovery tests and restart_backup (real restore, zero duplicate rows/writes/model calls). |
| 10. Local Ollama and complete-input behavior | Verified: current_prompt_complete, real overflow rejected without candidate, shared context tests. |
| 11. Compliance controls isolated; shared regressions | Verified: owned-lock/stop/import tests, affected DP/Training regressions, shared_queue_v1 real concurrent providers. |
| 12. Visible source failure distinct from no change | Verified: retained initial two retrieval failures, health rows and failed-fetch/empty-parse tests. |
| 13. Scheduling ready with decisions explicit | Verified after cadence correction: actual enabled hidden task exit 0; trigger-slot tests prevent skipped quarter-hours caused by completion latency. |

Continuity additions: dedicated resume contract/plan and one root routing entry are tested;
DP pending action and full prior history are preserved; runtime imports/state remain separate;
source/profile revision tests reopen affected decisions while retaining historical human fields;
compatible unchanged work reuses results; guarded shared writes preserve competing changes;
continuity and read-only tracker gates pass. Destination remains Program Compliance in
LT Automation Platform, with LT Project Tracking unchanged. Shared capacity is one actual
request, bounded DP priority and FIFO background order, independent of idle workers. Three
concurrent real provider processes verified that boundary; no production DP replay is claimed.

Audit correction: elapsed time from sync completion could skip the following quarter-hour
trigger. Runtime now compares UTC trigger slots, retaining sync_trigger separately from completion
and falling back to the old sync timestamp for existing state. It reads prior schedule state
under the service-owned lock. Three new synthetic tests prove completion-latency tolerance,
cross-boundary completion and persisted same-slot deduplication. Current Compliance suite:
43 passed. The previous 279-test acceptance remains retained; these add three new cases.
No prompts, inference behavior, source identities, sheet bindings or human decisions changed.

Remaining operational work: bounded incremental coverage/source-health gaps, human confirmation
of contracted/active services, and DP's separate unresolved correction. These were explicitly
allowed pilot limitations; no missing implementation acceptance criterion remains after the
cadence fix and delivery gates. Monitoring requires the user to remain logged in.

## Approved shared-inference amendment — September 10, 2026

This newer instruction supersedes the fixed/idle operating-window and worker-marker
admission conditions below. All other approved scope, memory and acceptance requirements remain.

> Run Compliance alongside DP and Training. Do not require them to be stopped or idle for a fixed window.
> Coordinate actual Ollama requests through a shared queue, initially allowing one inference at a time.
> Give DP priority without indefinitely starving Compliance. An idle DP worker must not block Compliance.
> Use daily source checks at 1 a.m. Central, broader discovery on Sunday, and Smartsheet synchronization
> every 15 minutes. These are trigger times, not exclusive operating windows.
> I authorize the minimal shared coordination changes needed. Preserve existing behavior, run affected
> DP/Training regressions, and verify concurrent service operation before activating recurring monitoring.
> If safe sharing remains unverified, leave activation disabled and report the specific blocker.

Implementation: the shared transport admits actual chat requests through a separate metadata-only
SQLite queue at LOCALAPPDATA/LTHHC/InferenceQueue. No prompts, findings, human decisions or DP recovery
records enter that queue. One active inference; DP has priority for at most three consecutive grants
while background work waits. Training and Compliance share FIFO background order. Request-scoped
ContextVars restore the original caller class, without mutating a shared provider object. Idle workers
are not scanned or treated as capacity reservations. Metadata preflight remains outside inference admission.

Completed/rejected requests release their reservation. Timeout, malformed/incomplete transport response,
or process death retains an uncertain/active reservation and blocks further inference; process age alone
never proves server completion. Waiting requests have a bounded 30-minute admission timeout. A queue
block requires confirming the server's outstanding inference has ended before explicit operator recovery;
there is no automatic deletion, stale-timeout eviction, model retry or Ollama restart. Direct non-platform
Ollama clients do not participate in this queue.

Activation: owned LTHHC-ProgramCompliance task enabled; daily 01:00 Central, Sunday discovery,
quarter-hour synchronization triggers. First task-launched tick passed and no boot/logon trigger was added.
A recovery backup was made before activation.

Sharing acceptance: 279 synthetic/mock tests passed (12 queue, 40 Compliance, 13 context contract,
214 affected DP/Training/continuity/tracker regressions). Three separate concurrent provider processes
using synthetic input completed real local Ollama requests with peak inference concurrency one,
DP first, and background arrival order preserved. Each used 39 input / 9 output tokens. No patient
input, production DP/Training run, learning/recovery record or human approval was operated on.
An initial live harness assertion incorrectly assumed background process launch order equaled queue
arrival order; serialization and output succeeded. The corrected arrival-order assertion passed on rerun.
Existing production worker count was zero, so no old loaded worker bypassed admission during verification.
These provider-boundary checks do not represent a production document replay or resolution of DP's
existing blocked correction generation.

## Approved implementation plan

Build one bounded, reusable multi-program service, initially configured only for
CLASS DSA requirements. Pipeline: approved registry -> HTTPS retrieval -> retained
raw and structured source versions -> section change/dependency detection -> local
Ollama structured analysis -> deterministic evidence/applicability validation ->
durable publication intents -> a separate Smartsheet human review queue.

Reuse only the smallest shared local Ollama wire contract and suitable validated
integration infrastructure. Keep compliance prompts, context, source configuration,
database, snapshots, identities, locks, worker, controls and sheet allowlists separate
from DP. Shared code changes require focused DP regressions; no DP service is started,
stopped, repaired or resumed. No custom website, vector database, policy inventory,
gap comparison, drafting, model retraining or autonomous code changes in this pilot.

Use a service-owned SQLite database and content-addressed source snapshots. Store
section/dependency versions, stable requirements, profile and analysis versions,
historical human decisions, review generations, outbound intents and readback results.
Reconcile uncertain creates before retrying; ambiguous/unavailable reconciliation
fails closed. Restart and backup restore preserve identities and human edits.

Program sources: CLASS manual and linked sections, appendices, forms/instructions,
glossary and revisions; official CLASS provider communications; relevant current
Texas rules and proposed/adopted notices; TMHP billing/documentation/EVV communications;
explicitly justified official cross-references. Verify URLs and publisher authority.
Automatic discovery stays within approved publisher/path and relevance boundaries.
Proposed rules remain proposals. Report unavailable/stale/parse-failed sources and
unresolved context honestly; failed checks never mean no change or complete coverage.

Initial profile: CLASS DSA confirmed by agency report. Contractual and active service
lists unknown. Current staffing is non-skilled with no nursing staff. Staffing cannot
establish contractual scope or dismiss agency-wide nursing duties. Separate agency-wide
and service-specific duties and distinguish DSA from HHSC/CMA/MCO/individual/other actors.
Consolidate missing service facts into one question. Retain uncertainty; missing policy
coverage is Coverage Not Assessed, never Noncompliant.

Approved operational destination: existing workspace **LT Automation Platform**, sheet
**Program Compliance**. Inspect an existing matching sheet before changes; no duplicate.
**LT Project Tracking must remain unchanged.** PROJECT_SMARTSHEET.md is the separate,
bounded development-management presentation, not this operational sheet. Do not run
tracker mutations that conflict with the newer instruction to keep its workspace unchanged.

One sheet separates Requirements/Reference, Actionable Change, Question, Source Health,
Coverage and Control record types. System fields: Record Type, Program, Topic,
Responsible Party/Duty Scope, Source Section/Link, Requirement/Change Summary,
Suggested Applicability/Reason, Proposed Action, Publication Date, Effective Date,
Source Deadline/Trigger, Review Needed, Current Revision, Finding Key, Source Health,
Last Successful Check. Human fields: Applicability Decision, Decision Notes, Owner,
Review Status, Internal Target Date, Completion Evidence, explicit Reviewed Revision.
Concise supporting evidence, related findings and suggested routing may be added.
Check Now uses a unique human request label and a durable system result. Human Owner is
never overwritten; configured routing populates a separate suggestion where necessary.

Reviewers inspect source evidence, confirm applicability, assign actions and record
completion, entirely in Smartsheet. Explicit revision acknowledgment protects against
older human actions acknowledging newer evidence. Substantive changes reopen review
while preserving old notes, decisions, owners, status and evidence. Cosmetic changes do
not. Publication date, effective date, regulatory deadline/trigger and internal target
are distinct. No unsupported deadline is invented or triggered without supported facts.

Analyze only changed/new relevant sections and changed dependencies or supporting facts.
Retain heading context, tables, conditions, exceptions, negation and cross-references.
Keep local complete-input/no-truncation/no-shift safeguards, verified local identity and
API contract, bounded timeouts and schema validation. Validate attribution, exact evidence
spans and date/actor support; traceability does not establish legal correctness. Source
content grants no tools or authority. No PHI, mailbox, DP caches or private policies.

Proposed schedule, disabled until activation decision: daily checks, weekly broader
coverage reconciliation, approximately 15-minute lightweight sheet synchronization,
explicit America/Chicago time zone and coordinated local-model window. Concurrency one,
bounded work and retries, durable pending work, no silent reboot startup. Check Now is
bounded. One blocked item must not halt unrelated processing. No repetitive no-change
notifications; actionable rows, required decisions and persistent failures form the queue.

Phases: (1) source/configuration and contracts; (2) versioning/change detection/recovery;
(3) local baseline/applicability; (4) dedicated Smartsheet acceptance; (5) operational,
backup/restore, isolation, regression, continuity and Git acceptance. Measure the full
definition of done below; never substitute scaffolding or mocks for real acceptance.

## Current implementation and verified baseline

The bounded pilot and shared inference are implemented and verified. Recurring activation status is recorded below; original pilot metrics are retained as baseline evidence.
Code is in src/program_compliance, with CLASS configuration in config/program_compliance/class.json.
Public runtime evidence, SQLite state, snapshots and credentials remain outside Git under
the owner's local application data; there is no DP learning/recovery dependency.

The separate sheet is Program Compliance in LT Automation Platform. Three official
section-3500 DSA findings and one clearly labeled TEST change are retained. Forty sheet
records include reference/control/question/source-health/coverage rows. The live TEST
proved exactly one new review generation, preserved human notes/owner/status/evidence and
old acknowledgment, and created no duplicate or repeated write on the unchanged check.
Fresh-process acceptance made zero model calls and zero external writes. Real backup and
restore preserved all findings and recorded human fields. LT Project Tracking is unchanged.

Real retrieval: seven initial seed checks, two failures honestly reported, and bounded
discovery to 29 registered sources. Real local Ollama server 0.33.3, context 8192/output
1200, complete-input/no-truncation/no-shift contract verified. First baseline: 490 input/
176 output tokens, about 40.3 seconds. Final prompt/schema-digest contract: 501 input/194
output tokens, about 43.5 seconds, complete response. Synthetic oversized input was rejected
with no candidate. Production pinned-public-IP HTTPS retrieval passed. Complete local
input/output and source traceability are not proof of legal correctness.

Five existing Ollama transport methods were mechanically extracted unchanged. Final
verification: 39 compliance + 4 service-continuity + 13 context boundary + 21 service-line
prompt/schema + 6 correction-context + 11 project-layer + 3 tracker tests = 97 passed,
synthetic deterministic/mock. Modified Python compiled. Native Windows PowerShell 5.1
Task Scheduler XML parsing passed with Enabled=false; no task was registered. The scheduler
definition has no boot or logon trigger and uses bounded ticks. No DP worker was operated.

Recovered implementation failures: create-column locking API contract, eventual workspace
readback, blank/null equivalence, Windows byte-lock re-entry and a test's default text
encoding. All were diagnosed with retained safe evidence; rejected/uncertain operations
were not blindly retried. Read-only tracker reconciliation: Writes 0, Not Found 0, Failed 0.
No external project-management synchronization is claimed under the newer keep-unchanged instruction.

## Source coverage and gaps

Verified official canonical manual:
https://fhb.hhs.texas.gov/handbooks/community-living-assistance-support-services-provider-manual
Legacy source returned 403 during planning; do not claim a verified redirect.
Section URLs use community-living-assistance-support-services-class-provider-manual.
Verified revision index includes notice 26-2, effective August 12, 2026, updating Appendix V.
The first real incremental baseline is limited to section 3500. Broader discovered pages
and rules/context dependencies remain pending. Exact contractual scope, active services,
licensing facts, private amendments and policies are not established by public retrieval.
Do not claim comprehensive regulatory coverage or agency compliance.

## Next Service Action

Continue approved incremental CLASS coverage and the existing source-health/gap queue. Recurring
monitoring is active; the first Task Scheduler cycle completed successfully on September 10, 2026
at 13:18 Central: exit 0, eight source checks, zero retrieval failures, two model calls, queue empty. Use shared request
admission at any time; there is no exclusive operating window. Contracted/active service lists remain
a consolidated human question in the operational sheet. Preserve DP's separate blocked correction
and pending work; enabling Compliance does not resume DP or consume Training approvals.
The task requires the operator to remain logged in; no boot/logon startup is enabled.

Full user scope and acceptance requirements below remain authoritative. Pilot completion
does not authorize other programs, policy drafting, regulatory actions or indefinite development.

## Shared platform continuity, separate service memory — full additional requirements

Program Compliance Monitor is a separate service within the existing platform.

1. Shared platform files

- AGENTS.md retains platform-wide safety and working rules.
- PROJECT_STATE.md contains concise, separately labeled current summaries for DP and Program Compliance Monitor.
- PROJECT_HISTORY.md retains append-only checkpoints clearly labeled by service.
- PROJECT_SMARTSHEET.md remains the bounded project-management presentation. It is not the operational compliance review sheet.

Preserve all DP facts, limitations, unfinished work, and pending actions.
Do not overwrite DP continuity to make compliance the only active service.

2. Service-specific development notes

Inspect repository conventions and create one concise, dedicated compliance state/plan
document in an appropriate location. Include approved scope and architecture; current
implementation and verified baseline; source coverage and known gaps; applicability
assumptions and unresolved agency facts; tests and acceptance status; exact pending service action.
Do not duplicate the entire platform state or historical journal. Read shared rules,
concise platform state, compliance-specific state and relevant checkpoint when resuming
compliance work—not all DP history.

Keep exactly one root CURRENT NEXT START. Make it a clear service-routing entry that
preserves each service's pending work rather than repeatedly replacing one service's
next step with the other's. Use a distinct heading such as Next Service Action in the
service-specific document. Adjust continuity validation/tests deliberately if required.

3. Coordinate shared-file changes

Before updating shared continuity, reread current contents and inspect the diff. Preserve
concurrent changes. Do not let separate development tasks overwrite shared files, stage
unrelated work, or commit each other's unreviewed changes. Coordinate or defer an overlapping update safely.

4. Separate production memory

Compliance runtime storage must be independent of DP state and learning. Retain approved
source registry and versioned snapshots; meaningful section changes and dependencies;
source-backed requirements; confirmed agency profile facts; applicability recommendations
and human decisions; requirement/review revisions; actions, ownership and completion evidence;
source health, pending analysis and durable Smartsheet write intents.

Bind decisions to supporting source/profile versions. Preserve historical decisions when
a substantive revision requires review. Do not treat an old decision as automatically
valid for changed requirements. Ollama receives only relevant evidence, agency facts and
applicable approved decisions. Do not reread all historical findings/comments for each
analysis. This is versioned operational knowledge, not model retraining or a copy of DP correction-learning.

5. Ownership and safety

Human Smartsheet decisions remain human-owned. Public source evidence, local runtime state,
development notes and project tracker remain distinct. Keep credentials and protected
runtime data out of Git and project summaries. Follow existing backup, recovery,
idempotency, tracker and Git safeguards.

Acceptance additions: prove compliance resumes from dedicated state without full DP
history; DP continuity and unfinished work remain intact; compliance runtime never reads
or mutates DP learning/recovery records; changed source/profile facts invalidate only
affected decisions; unchanged cycles reuse compatible results without repeated inference;
shared continuity updates preserve concurrent work; existing continuity/tracker tests pass.

Continue the existing goal with these additions. Do not create a second implementation
or restart planning. Preserve completed work and approved implementation plan.

## Full original planning requirements

The complete user-supplied planning request is preserved below.

Plan a new service for our existing LTHHC AI Automation Platform.

Service name:
Program Compliance Monitor

Repo:
C:\Projects\LTHHC-AI-Automation-Platform

BEFORE PLANNING
- Read AGENTS.md, PROJECT_STATE.md, and relevant PROJECT_HISTORY.md checkpoints.
- Inspect CURRENT NEXT START, branch, Git status, and local/remote sync.
- Preserve all committed and uncommitted work.
- Do not interfere with current Document Processor development or runtime.
- Do not reset, restore, clean, discard, or overwrite existing work.

BUSINESS PURPOSE
We participate in Texas service programs with requirements published through
official handbooks, regulations, provider notices, and other authoritative sources.

We need the platform to:
- Identify requirements that apply to our agency.
- Identify policies, procedures, training, documentation, reporting, and other
  actions those requirements call for.
- Monitor official sources for meaningful changes.
- Explain what changed, whether it applies to us, what action may be needed,
  and any supported effective date or deadline.
- Present findings and track human decisions in Smartsheet.

MULTI-PROGRAM ARCHITECTURE
Build Program Compliance Monitor as a reusable multi-program service.
CLASS is the first configured program, not a hard-coded architecture.

Additional programs should primarily require approved source configuration,
agency-role/service profiles, and applicability rules—not duplicated services.
Allow program-specific adapters only when source formats genuinely require them.

Future programs may include HCS, CFC, STAR KIDS, STAR+PLUS, and others.
Do not implement those programs during the initial CLASS pilot.

INITIAL AGENCY PROFILE
- We are a CLASS Direct Services Agency (DSA).
- We report that we can provide CLASS-authorized services, but the exact
  contractual and active service lists will be supplied later.
- Current staffing is non-skilled; we no longer have nursing staff.
- Do not infer complete contractual scope from current staffing.
- Do not automatically dismiss agency-wide obligations involving nursing.
- Service-specific applicability remains Needs Confirmation until supported.

END-USER WORKFLOW
- End users work only in a new, separate Smartsheet sheet.
- Reviewers should not need terminal commands, Codex, or technical knowledge.
- Findings should distinguish agency-wide duties from service-specific duties.
- Reviewers confirm applicability, assign actions, and track completion.
- Preserve human decisions, notes, ownership, and completion evidence.
- A changed requirement must reopen review when appropriate without erasing
  prior decisions or silently duplicating tasks.

LOCAL PRODUCTION REQUIREMENT
- Production analysis uses local Ollama.
- No Codex/cloud-model dependency once deployed.
- Reuse suitable existing platform components after inspecting their contracts.
- Keep this service isolated from DP processing, state, workers, and stop controls.
- Public requirements monitoring should not need patient data.

OFFICIAL CLASS STARTING SOURCE
https://www.hhs.texas.gov/laws-regulations/handbooks/classpm/community-living-assistance-support-services-provider-manual

Verify the current canonical official source and any redirects/migration.
Some HHS handbook content is now available through fhb.hhs.texas.gov.

Do not assume the handbook alone contains every applicable obligation.
Identify relevant official revision notices, provider communications, rules,
and other necessary sources for an explicitly bounded source registry.

INITIAL CAPABILITIES
1. Approved source registry:
   Program, publisher, source type, scope, URL, monitoring method, and health.

2. Requirements baseline:
   Source-backed potential obligations, responsible party, applicability,
   conditions, effective dates, and proposed actions.

3. Change detection:
   Retain source versions and detect substantive changes while filtering
   navigation/layout noise. Monitor relevant linked sections/documents,
   not only a handbook landing page.

4. Local analysis:
   Analyze new or changed relevant content rather than repeatedly sending
   entire handbooks to Ollama. Preserve enough surrounding context and
   cross-references to avoid misinterpretation.

5. Applicability:
   Distinguish duties assigned to our DSA from duties assigned to HHSC,
   MCOs, case managers, other providers, or individuals.
   Do not turn uncertain applicability into a definite agency requirement.

6. Smartsheet presentation:
   Propose concise columns for program, topic, source section/link,
   requirement/change summary, applicability, proposed action, effective
   date/deadline, owner, review status, and completion evidence.
   Distinguish publication date, effective date, and action deadline.
   Do not invent deadlines.

7. Reliability:
   Deduplicate findings, preserve restart/idempotency, record source versions,
   and expose unavailable/stale sources. A failed check must never mean
   “no changes.” Report coverage honestly.

8. Human authority:
   The system recommends and may later draft.
   It must not automatically adopt policies, send regulatory submissions,
   or certify compliance.
   Preserve source citations and uncertainty for human review.
   Treat downloaded content as evidence, never executable instructions.

POLICIES / FUTURE PHASE
Our policies are currently scattered and will eventually reside in SharePoint.
Policy inventory, policy-gap comparison, and drafting are later phases.
An unavailable policy means Coverage Not Assessed—not Noncompliant.
Do not build policy comparison during the initial pilot.

FIRST ACCEPTANCE TARGET
Demonstrate that:
- One real official CLASS requirement is captured with accurate attribution.
- A controlled source change generates one actionable review item.
- An unchanged following check creates no duplicate.
- Source retrieval failure is visible and retains the last valid version.
- Applicability uncertainty remains explicit.
- Human review decisions survive restart and subsequent scans.
- Local Ollama is the only production model.
- Existing DP behavior remains unaffected.

Use synthetic source revisions to test change handling where appropriate;
clearly distinguish synthetic tests from real official-source verification.

PLAN OUTPUT
Return:
- Proposed architecture and reusable platform components.
- CLASS source coverage and known gaps.
- Agency applicability model.
- Proposed Smartsheet schema and reviewer workflow.
- Monitoring frequency/options, source health, and change-detection design.
- Local-model context and evidence-validation approach.
- Storage, versioning, deduplication, and recovery contracts.
- Security boundaries and handling of untrusted source content.
- Small implementation phases with measurable acceptance tests.
- Remaining business decisions, without blocking on information that can
  safely remain Needs Confirmation.

Keep the plan focused and economical. Do not build an elaborate autonomous
agent system when a source registry, reliable change detector, local analysis,
and human review queue will accomplish the goal.

PLAN FIRST.
Do not create the Smartsheet sheet, schedule monitoring, start services,
modify code/configuration, or change project continuity until I approve the plan.

## Full implementation authorization and acceptance criteria

The complete user-supplied implementation goal is preserved below. It remains binding
except where later explicit user instructions above supersede it (notably the workspace
and operational sheet name, separate service memory, and keeping LT Project Tracking unchanged).

/goal Implement and verify the first operational pilot of Program Compliance Monitor for CLASS DSA requirements, using the existing reviewed plan plus the requirements below. Finish at a tested, documented, restart-safe pilot ready for scheduled activation. Do not expand into additional programs or run indefinitely.

AUTHORIZATION AND EXECUTION

I approve the reviewed architecture with these autonomy refinements.

Proceed with scoped implementation, tests, public official-source retrieval,
local Ollama acceptance, and creation/configuration of a new separate
Program Compliance Monitor Smartsheet sheet.

Use the intended existing Smartsheet workspace if it can be established
unambiguously. Otherwise ask once for the destination. Do not guess.

Do not ask for confirmation at every implementation phase or routine operation.
Continue through safe, authorized work. Ask only when genuinely required by
product permissions, missing access, a material business decision, or a
necessary expansion beyond this scope.

Do not bypass permissions, approve business decisions for us, purchase
services, weaken safeguards, or perform regulatory submissions.

Before recurring activation, verify acceptance and confirm any unresolved
operating-window or resource-sharing decision. A missing activation decision
must not block implementation and bounded acceptance.

PRESERVE EXISTING PLATFORM WORK

Repo:
C:\Projects\LTHHC-AI-Automation-Platform

Read AGENTS.md, PROJECT_STATE.md, and relevant recent PROJECT_HISTORY.md
checkpoints. Inspect branch/status/diff and local/remote synchronization.

Preserve all committed and uncommitted work. Do not reset, restore, clean,
discard, or overwrite unrelated changes.

Program Compliance Monitor is a SEPARATE platform service.
Do not resume, alter, start, stop, or repair Document Processor work as part
of this goal. Do not let the DP CURRENT NEXT START redirect this task.

Inspect existing components and reuse only genuinely shared infrastructure.
Keep separate:
- prompts and business context
- source registry and configuration
- database, snapshots, identities, locks, and recovery state
- Smartsheet destination and write allowlists
- deployment/scheduling and owned start/stop controls

It must operate while DP is stopped. Stopping either service must not stop
the other. Do not give two active tasks write ownership of the same files.
Shared-component changes require focused DP regressions and preservation
of current behavior.

SERVICE PURPOSE

Monitor official program requirements and help our agency answer:
- What requirements potentially apply to us?
- What changed?
- Why does it matter?
- What action is proposed?
- When does it take effect or become due?
- What source supports the finding?

Build a reusable multi-program architecture, initially configured for
CLASS only. Future programs should mainly require approved source/profile
configuration and applicability rules, not copied services.

CURRENT AGENCY PROFILE

- Program: CLASS.
- Agency role: Direct Services Agency (DSA), confirmed by our report.
- Exact contractual service scope: Needs Confirmation.
- Exact actively delivered services: Needs Confirmation.
- Current staffing: non-skilled; no nursing staff.
- Do not infer complete contractual scope from staffing.
- Do not automatically dismiss agency-wide nursing-related obligations.

Unknown facts must remain explicit. Do not block all work while waiting
for our service list.

END-USER INTERFACE

End users work entirely in the new Smartsheet.
They should not need terminal commands, Codex, or technical knowledge.

Keep the interface concise and actionable. Separate:
- requirements/reference information
- actionable changes
- consolidated questions requiring input
- source-health/coverage issues

One sheet with clearly identified record types/groups is acceptable.
Do not build a separate custom web application for this pilot.

MAXIMUM ROUTINE AUTONOMY

Automatically:
- check approved sources on schedule
- follow relevant links within approved publisher/path boundaries
- detect meaningful changes and remove cosmetic noise
- analyze new/changed relevant evidence
- reuse confirmed agency facts and approved applicability rules
- group related findings and deduplicate repeated alerts
- publish source-backed findings and proposed actions
- route using configured owner/department rules
- synchronize system-owned fields and verify readback
- perform bounded transient retries and resume pending work after restart

Do not require approval for each page, source check, or routine finding.

Ask for human input only for:
- missing agency facts that materially affect applicability
- conflicting or genuinely ambiguous interpretations
- policy adoption, spending, staffing actions, external submissions, or
  other consequential decisions
- access outside approved boundaries
- persistent technical failures requiring intervention

Consolidate repeated questions. If one unknown service list affects many
findings, ask for it once and link the affected findings.

One blocked item must not halt unrelated processing.
Do not repeatedly ask a question already answered unless relevant facts change.

Notify about actionable changes, necessary decisions, and persistent
monitoring failures. Do not send repetitive "nothing changed" messages.

OFFICIAL SOURCES AND COVERAGE

Starting source:
https://www.hhs.texas.gov/laws-regulations/handbooks/classpm/community-living-assistance-support-services-provider-manual

Verify the current official location; relevant HHS handbook content is
available through fhb.hhs.texas.gov. Do not assume an unverified redirect.

Use the reviewed bounded source families:
- CLASS manual sections, appendices, glossary, forms/instructions,
  and revision notices
- relevant official CLASS provider communications
- relevant current Texas rules and official proposed/adopted notices
- relevant official TMHP billing/documentation/EVV communications
- explicitly justified official cross-references

Verify actual URLs and source authority before use.
Do not treat proposed rules as effective requirements.
Do not treat publication, effective date, and action deadline as interchangeable.

Automatically discover relevant pages/documents within approved boundaries.
Out-of-scope publishers or unrelated programs remain coverage candidates,
not silently trusted sources.

Record coverage gaps honestly. Do not claim complete regulatory coverage,
certify compliance, or assume a handbook contains every contractual obligation.

BASELINE AND APPLICABILITY

Build the initial baseline incrementally.
Prioritize actionable DSA obligations; do not flood the reviewer with every
handbook sentence.

Identify:
- responsible actor
- requirement and conditions
- agency-wide versus service-specific scope
- supporting source/version/section
- proposed applicability and rationale
- proposed action
- supported date/deadline or event-based trigger

Distinguish our DSA duties from HHSC, MCO, CMA, individual, and other-provider
duties. Preserve context without assigning another party's duty to us.

System applicability recommendations and human decisions remain separate.
Reuse approved determinations when evidence/profile remains compatible.
Never convert unknown services into Not Applicable.

Unavailable policies mean Coverage Not Assessed, not Noncompliant or
automatically "create a new policy."

SMARTSHEET WORKFLOW AND OWNERSHIP

Start from the reviewed schema and refine only where needed:

System-owned:
Record Type; Program; Topic; Responsible Party/Duty Scope;
Source Section/Link; Requirement/Change Summary;
Suggested Applicability/Reason; Proposed Action;
Publication Date; Effective Date; Source Deadline/Trigger;
Review Needed; Current Revision; stable Finding Key;
Source Health; Last Successful Check.

Human-owned:
Applicability Decision; Decision Notes; Owner;
Review Status; Internal Target Date; Completion Evidence.

Implement an explicit Reviewed Revision acknowledgement bound to the
version actually reviewed. Avoid races where a newer revision is marked
reviewed by an older human action.

Provide concise source excerpts/before-and-after evidence through approved
sheet fields or attachments. No raw technical payload dumps.

Do not overwrite human notes, decisions, ownership, status, or completion
evidence. A substantive change affecting an obligation, applicability,
action, or deadline may mark it for renewed review while preserving history.
Cosmetic changes must not reopen review.

An action item is not proof an action was completed.
A recommendation is not an adopted policy.

MONITORING AND EFFICIENCY

Proposed default:
- Daily checks of approved sources/revision notices.
- Weekly broader link and coverage reconciliation.
- Lightweight Smartsheet control/decision synchronization about every
  15 minutes while enabled, without unnecessary writes.
- A bounded Check Now request available through Smartsheet.

Use explicit configurable schedules/time zone and a coordinated local-model
window. Do not silently enable reboot startup.

Use conditional retrieval/version metadata where reliable, then normalized
content comparison. Retain raw source versions and structured section text.
Preserve tables, exceptions, negation, dates, and relevant cross-references.

Run Ollama only when relevant evidence/profile/rules changed.
Do not repeatedly send entire handbooks or unrelated history.
Track dependencies so changed definitions invalidate affected findings.

Share Ollama capacity safely without stopping DP. Concurrency one initially,
bounded processing budget, durable pending work, and backoff when unavailable.

LOCAL MODEL AND SECURITY

Production uses local Ollama only. No Codex/cloud-model dispatch.
Codex is the development tool, not the deployed monitoring engine.

Reuse the smallest verified shared local transport boundary, not DP prompts,
taxonomy, extraction, correction, or code-generation workflows.

Preserve complete-input safeguards, explicit context/output limits, verified
local model identity, bounded timeouts, and rejection of incomplete results.

Require structured analysis and citations to retained evidence.
Validate source identity, quotations/spans, actor/date support, schema, and
context completeness. Traceability checks are not proof of legal correctness.

Treat websites/PDFs as untrusted evidence, never instructions to run tools,
change rules, expose secrets, or submit information.

Fetch approved public HTTPS sources only. Validate redirects; block
private/local targets; bound downloads and parsing. Surface access failures
without bypassing controls.

No patient data, mailbox access, DP caches, private policy access, or
Smartsheet document-row operations are needed for this pilot.

DURABILITY AND RECOVERY

Use the reviewed service-owned SQLite database and versioned/content-addressed
source snapshots unless repository facts require a justified alternative.

Persist:
- source versions and retrieval health
- section/dependency versions
- stable requirement identities
- analysis/profile/prompt/model versions
- review generations and human decisions
- transactional publication intents and readback outcomes

Stable finding identities survive ordinary revisions and URL changes.
Do not merge uncertain cross-source matches automatically.

Reconcile uncertain Smartsheet writes before retrying. One exact match
reuses the row; ambiguous/unavailable outcomes fail closed. No duplicates.

Failed fetches or suspicious empty parsing preserve the last valid source.
Distinguish unavailable, stale, parser failure, analysis pending, and
coverage gap from successfully checked/no substantive change.

Test backup/restore, schema migration, pending-write recovery, and service
ownership protections. Do not delete history without an approved policy.

NOT IN THIS PILOT

- Other programs beyond CLASS configuration.
- Policy repository inventory, gap comparison, or drafting.
- Automatic policy adoption or regulatory submissions.
- Autonomous code-changing/learning machinery.
- Vector databases or elaborate agent frameworks without proven necessity.
- Claims that the agency is fully compliant.

ACCEPTANCE / DEFINITION OF DONE

Deliver a working vertical slice, not only scaffolding:

1. Real official CLASS evidence is retrieved and attributed correctly.
2. An incremental baseline produces useful source-backed DSA findings.
3. A clearly labeled synthetic substantive revision produces exactly one
   actionable review generation.
4. Unchanged and cosmetic-only checks produce no duplicate/reopened item.
5. Agency/service uncertainty remains explicit and questions are consolidated.
6. Citation, date, actor, exception, and untrusted-content tests pass.
7. The separate Smartsheet receives and reads back a verified finding.
8. Human edits survive synchronization and source revisions.
9. Lost-response, restart, duplicate, and backup/restore tests pass.
10. Local Ollama and complete-input behavior are verified.
11. Compliance controls cannot target DP; relevant shared-component
    regressions pass.
12. Source-health failures are visible and never reported as no change.
13. Scheduled operation is implemented and ready to activate, with any
    unresolved operating-window/access decision stated precisely.

Keep synthetic examples unmistakably labeled TEST; never present a synthetic
revision as an official change. Use the dedicated new sheet only.

Stop the implementation goal when this verified pilot is complete and ready
for activation. Do not keep expanding scope to satisfy an indefinite goal.
If a real blocker prevents completion, save a safe checkpoint, complete
unblocked work, and report the exact smallest input needed.

VALIDATION, CONTINUITY, AND DELIVERY

Compile modified Python first. Run focused tests, then affected regressions.
Validate PowerShell 5.1 if touched.
Run git diff --check, protected-path/security review, and full reviewed diff.

Follow the existing continuity/tracker protocol, recording this service
separately without erasing or replacing the DP's unresolved work.
Require tracker Not Found: 0 and Failed: 0 before committing.

Stage only reviewed safe changes; commit/push and verify sync when all gates pass.
Do not commit unrelated partial work or report live acceptance based on mocks.

Report:
- implemented scope and architecture
- source coverage and gaps
- Smartsheet link and end-user workflow
- automatic behavior versus required human decisions
- real/synthetic/mock test results
- local-model verification
- recovery/idempotency evidence
- scheduling activation state
- tracker and Git state
- exact remaining input, if any

CONSERVE DEVELOPMENT USAGE

Use existing inspected evidence; do not restart planning from scratch.
Avoid repeated full-history reads, redundant inference, rapid unchanged
polling, and continuity-only commits for each status update.
Retain diagnostic results so failures can be understood without blind retries.
Do not spawn parallel agents unless explicitly requested.
Provide concise milestone updates and pursue this bounded outcome.

### Hidden background execution

The owned task invokes the repository virtual environment's pythonw.exe, which avoids a
console window. The Task Scheduler Hidden flag alone is not relied on to suppress windows.
The original console task's first run exited 0; when the reported blank repository terminal
was investigated, no matching terminal or Compliance process remained. The vanished window could
not be conclusively attributed. A console-free task run then exited 0 with zero repository
terminal windows observed. No terminal
or DP/Training process was stopped. Future manual background starts already use CREATE_NO_WINDOW.
Task exit status and durable Compliance records remain the operational diagnostics.
