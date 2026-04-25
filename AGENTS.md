# AGENTS.md

## Purpose

This file is the mid-sized root memory for agents working in `projectH`.
Keep high-risk operating boundaries here, and put low-level or path-specific
detail in referenced docs that are read only when the current task touches that
area.

## Product Contract

`projectH` is a **local-first document assistant web MVP**, not a generic
chatbot starter.

Current shipped contract:
- local web shell on `127.0.0.1`
- local file summary, document search, and general chat
- session history stored locally
- approval-gated note saving and reissue flow
- evidence/source panels, web-investigation history, and source trust labels
- response origin and answer-mode badges for web investigation
- streaming progress, cancel, response feedback, and PDF text-layer reading
- OCR-not-supported guidance instead of silent OCR failure
- reviewed-memory slice through visible review queue, aggregate apply,
  active-effect path, explicit stop, reversal, and conflict visibility
- Playwright smoke coverage for core browser flows

Long-term north star:
- a teachable local personal agent that learns from correction, approval,
  rejection, and examples
- durable local preferences and working style
- later, tightly approved local tool or program operation

Do not present the north star as shipped behavior. Current work remains
document-first, local-first, approval-based, and replaceable across model,
runtime, and storage.

Frontier model releases such as GPT-5.5 are runtime capability context only.
They may justify larger coherent local bundles when tests and evidence support
the scope, but they do not change product scope, branding, API assumptions, or
approval/operator boundaries.

## Product Priorities

1. Local-first behavior
2. Approval-based safety
3. Practical document productivity
4. Teachability through correction, approval, and feedback traces
5. Auditable evidence and source handling
6. Commercial/IP-safe architecture
7. Replaceable model/runtime/storage seams

In scope:
- local file reading
- document summarization and search
- session persistence
- approval-gated note saving
- task/search logs
- evidence-backed web investigation as a secondary mode

Out of scope unless explicitly requested:
- wake-word voice assistant
- mobile app
- browser login automation
- autonomous destructive actions
- always-on background agents
- large-scale independent pretraining
- cloud-first architecture
- broad desktop/program operation outside approved flows

## Context Budget Policy

Root memory files (`AGENTS.md`, `CLAUDE.md`, `GEMINI.md`,
`PROJECT_CUSTOM_INSTRUCTIONS.md`) should be mid-sized routing and guardrail
pages. They should preserve the rules most likely to prevent unsafe stops,
scope drift, or repeated automation stalls, while keeping detailed runtime
mechanics out of the always-loaded context.

Default read set for a round:
- active owner root memory file only
- the active control/work/verify file for that round
- source files and tests directly touched by the task

Read detailed references only when relevant:
- product/spec drift: `docs/project-brief.md`, `docs/PRODUCT_SPEC.md`,
  `docs/ARCHITECTURE.md`, `docs/ACCEPTANCE_CRITERIA.md`,
  `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md`
- pipeline/runtime specifics: `.pipeline/README.md`,
  `.pipeline/harness/*.md`, `.claude/rules/pipeline-runtime.md`
- browser/E2E specifics: `.claude/rules/browser-e2e.md`
- doc-sync specifics: `.claude/rules/doc-sync.md`
- latest implementation truth: newest relevant `work/` and `verify/` notes
- long-term strategy only when requested: `plandoc/` and
  `docs/superpowers/**`

Do not put static guide files such as `work/README.md`, `verify/README.md`, or
`.pipeline/README.md` into every prompt by default. Pull them only when a task
actually needs that policy detail.

If a prompt already names exact source paths, docs, or tests, read those first
and avoid widening into historical planning folders. `docs/superpowers/**`,
`docs/recycle/**`, and `plandoc/**` are not current truth unless the user,
latest `/work`, latest `/verify`, or active control explicitly cites them.

## Repository Map

- `app/`: local web shell, web handlers, CLI entrypoints
- `core/`: orchestration, intent classification, approval logic,
  investigation pipeline
- `tools/`: explicit auditable tools such as file read/search and note write
- `storage/`: local session, web-history, and task-log JSON/JSONL
- `model_adapter/`: provider-swappable runtime adapters
- `controller/`: local pipeline/controller monitor UI and server
- `docs/`: current product/spec/architecture/acceptance/milestone docs
- `plandoc/`: strategy above the current shipped contract
- `work/`: Korean implementation closeout notes
- `verify/`: Korean verification and truth-reconciliation notes
- `report/`: broader audits and `report/gemini/` advisory logs
- `.pipeline/`: rolling automation control slots and harnesses
- `.agents/skills/`, `.claude/skills/`: mirrored repo skills
- `.codex/agents/`, `.claude/agents/`: mirrored helper agents
- `.codex/config.toml`: Codex defaults, enabled skills, subagent registry

## Automation Contract

Automation target:
- do not call the user for ordinary next-step, ambiguity, stall, rollover, or
  recovery choices
- route ordinary ambiguity through implement / verify-handoff / advisory owner
  discussion using `/work`, `/verify`, current docs, and runtime evidence
- make repeated failures produce recursive improvement: incident family,
  focused replay, owner boundary, shared helper, or runtime surface
- treat recursive learning as repo-local operational memory, not model-weight
  learning or autonomous risky action

Real-risk actions still require explicit, auditable boundaries:
- destructive writes
- credential/auth work
- approval-record repair
- truth-sync blockers
- external publication, branch/PR publication, merge execution

Operator stops must be structured and actionable. A pending
`.pipeline/operator_request.md` should include `STATUS: needs_operator`,
`CONTROL_SEQ`, `REASON_CODE`, `OPERATOR_POLICY`, `DECISION_CLASS`,
`DECISION_REQUIRED`, `BASED_ON_WORK`, and `BASED_ON_VERIFY`. It should explain
why automation is stopping now, which evidence it used, and what one decision
would let automation resume.

If a stop is only a labeled choice set that agents can narrow from current
docs, milestones, latest `/work`, and latest `/verify`, route advisory-first
instead of calling the operator. Keep actual safety, destructive, auth,
credential, approval-record, truth-sync, publication, and merge boundaries as
operator stops.

## Pipeline Roles

Role ownership comes from active `role_bindings`, not vendor-named legacy files.

Canonical control slots:
- `.pipeline/implement_handoff.md`: implement owner input
- `.pipeline/advisory_request.md`: verify/handoff -> advisory request
- `.pipeline/advisory_advice.md`: advisory -> verify/handoff recommendation
- `.pipeline/operator_request.md`: operator-only stop slot

Historical aliases are read-only compatibility inputs:
- `.pipeline/claude_handoff.md`
- `.pipeline/gemini_request.md`
- `.pipeline/gemini_advice.md`

If canonical and alias files exist for the same logical slot, resolve by higher
`CONTROL_SEQ`; canonical wins ties. Newest valid control uses `CONTROL_SEQ`
first and `mtime` only as fallback.

`.pipeline/harness/*.md` files are role protocols, not control slots.
`.pipeline/session_arbitration_draft.md` is draft-only and never a stop/go
signal. `.pipeline/codex_feedback.md` and `.pipeline/gpt_prompt.md` are
optional/legacy scratch.

Control statuses:
- `.pipeline/implement_handoff.md` uses `STATUS: implement`
- `.pipeline/advisory_request.md` uses `STATUS: request_open`
- `.pipeline/advisory_advice.md` uses `STATUS: advice_ready`
- `.pipeline/operator_request.md` uses `STATUS: needs_operator`
- `.pipeline/session_arbitration_draft.md` uses `STATUS: draft_only`

Verify/handoff owner:
- read newest relevant `/work`, then same-day `/verify` if present
- rerun the narrowest honest verification
- leave or update `/verify` before writing the next control
- write one exact `.pipeline/implement_handoff.md` when a slice is clear
- write `.pipeline/advisory_request.md` only for next-slice ambiguity,
  overlapping candidates, or low-confidence tie-breaks
- write `.pipeline/operator_request.md` only for real operator-only decisions,
  approval/truth-sync blockers, immediate safety stops, or unresolved
  post-advisory ambiguity
- if an implement-owner session asks a live side question such as context
  exhaustion, session rollover, or continue-vs-switch, use advisory only for
  coordination and relay the answer back as a short lane reply; do not rewrite
  `.pipeline/implement_handoff.md` mid-session
- if watcher routes an operator-retriage follow-up, close it by writing exactly
  one newer control slot; returning idle with no control lets watcher escalate
  to advisory with `operator_retriage_no_next_control`
- handle approved large-bundle publish follow-up in the verify/handoff lane,
  not by handing commit/push/PR creation to implement

Implement owner:
- execute only the exact active `STATUS: implement` slice
- do not self-select the next slice
- stop after bounded edits plus canonical `/work` closeout
- do not commit, push, publish branches/PRs, or merge from the implement lane
- if blocked/stale/already implemented, emit pane-local
  `STATUS: implement_blocked` with structured fields and stop

Advisory owner:
- compare bounded candidates and recommend one exact next slice, axis switch,
  or one real operator decision
- write `report/gemini/...md` and `.pipeline/advisory_advice.md`
- do not write implement handoffs, operator stops, `/work`, or `/verify`

Publish boundaries:
- ordinary small/local slices stop at `/work` and dirty local state
- commit/push/PR creation is only for explicitly approved, verified large
  bundles such as release, soak, PR stabilization, or direct publish work
- `commit_push_bundle_authorization + internal_only` and
  `pr_creation_gate + gate_24h + release_gate` are verify/handoff follow-ups
  when already approved; they should not re-ask the operator by default
- `pr_merge_gate`, destructive publication changes, auth/credential repair,
  approval-record/truth-sync blockers, and external publication boundaries stay
  operator-approved boundaries

## Slice Selection

Choose the next slice only if it improves one of:
- user-visible value in the current document-first MVP
- a concrete current-risk reduction
- a shipped contract that is broken or misleading

Default tie-break:
1. same-family current-risk reduction
2. same-family user-visible improvement
3. new quality axis
4. internal cleanup

Avoid route/helper completeness work unless it protects a currently shipped
user-facing contract. Avoid docs-only micro-loops; after three same-family
docs-only truth-sync rounds in one day, close the remaining drift as one bounded
bundle or escalate.

Reviewed-memory remains in scope, but the planning anchor is user-visible
reviewed-memory, active effect, and explicit stop. Deeper reversal,
conflict-visibility, or route completeness is not the automatic next slice.

## Recursive Improvement

For runtime, launcher, watcher, supervisor, and controller work:
- classify whether the issue is an existing incident family or a new one
- for existing families, strengthen the owning module/helper/contract/replay
  instead of adding parallel heuristics
- for new families, add a named incident, focused replay, and truthful runtime
  surface before broad soak or UI polish
- keep thin clients thin; do not hide runtime drift by adding extra truth
  inference to launcher/controller/browser consumers
- prefer focused incident replay and live stability gates over long soak unless
  the runtime contract materially changed

Good recursive improvement reduces future diff surface, duplication, or owner
ambiguity.

## Engineering Rules

- Inspect implementation before changing docs or behavior.
- Prefer the smallest coherent reviewable change.
- Reuse existing helpers, queries, scripts, prompts, and local patterns.
- Do not hardcode branch names, commit SHAs, `CONTROL_SEQ`, pane ids, Korean UI
  text, exact operator prose, or one-off control bodies in runtime logic.
- Do not duplicate watcher/supervisor/launcher/controller truth logic; move
  shared truth to an owning helper.
- Extract parsing, labeling, control writing, lane-surface, or event-contract
  responsibilities when one file/function starts collecting unrelated logic.
- Keep default behavior read-heavy and approval-based.
- Do not widen the product into a general-purpose web chatbot.
- If docs and implementation disagree, make docs match implementation or mark
  the gap `TODO` / `OPEN QUESTION`.
- Respond to the user in Korean honorifics.

## Verification Rules

- Verification is risk-based, not maximal by default.
- Run the narrowest relevant check first.
- For small Python/helper/service changes, run targeted compile and unit tests.
- For selector-only, fixture-only, or single browser scenario changes, run the
  isolated Playwright scenario first.
- Use broad browser/E2E only when browser-visible contracts changed, shared
  browser helpers changed, release/ready is being claimed, a current browser
  flow is suspected broken, or isolated rerun suggests broader drift.
- If a check was not run, say so explicitly.

Common checks:
- `python3 -m py_compile <files>`
- `python3 -m unittest -v <tests>`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "<scenario>" --reporter=line`
- `make e2e-test`
- `git diff --check -- <paths>`

## Skill / Agent Sync

Current useful helper-agent roles:
- `planner`: scoped product/implementation planning
- `reviewer`: correctness, scope, approval safety, and verification review
- `spec-editor`: product/spec/architecture/acceptance doc alignment
- `qa-e2e-reviewer`: browser-facing flow and Playwright contract review
- `approval-auditor`: approval payload/save/reissue/pending invariant review
- `investigation-reviewer`: web investigation quality/source review
- `documenter`: closeout and operator handoff summaries
- `trace-implementer`: small grounded-brief trace or memory-foundation slices

Useful repo skills include:
- `onboard-lite`: narrow orientation for unfamiliar subsystem
- `finalize-lite`: implementation-side release-check/doc-sync/`/work` readiness
- `round-handoff`: rerun verification truth and prepare next handoff
- `next-slice-triage`: exact next-slice/advisory/operator decision after truth
  is current
- `trace-implementer`: small grounded-brief trace or memory-foundation slices
- `approval-flow-audit`, `investigation-quality-audit`, `e2e-smoke-triage`,
  `security-gate`, `release-check`, `work-log-closeout`, `doc-sync`

Wrapper order:
- use `onboard-lite` first when entering an unfamiliar repo or subsystem
- use `finalize-lite` after a meaningful implementation round
- use `round-handoff` when verification truth must be rerun/reconciled
- use `next-slice-triage` only after `/work` and `/verify` truth is current

Do not collapse these wrappers into one broad audit. Each should stop at its
own boundary.

When behavior changes, sync the relevant product docs. UI changes usually touch
`README.md`, `docs/PRODUCT_SPEC.md`, and `docs/ACCEPTANCE_CRITERIA.md`;
architecture/schema changes usually touch `docs/ARCHITECTURE.md`; staged
roadmap changes should also check `plandoc/`.

Specific doc-sync triggers:
- approval payload or save/reissue flow changes should also check approval
  architecture and acceptance docs
- session schema, stored search record, or task-log shape changes should check
  architecture and migration notes
- test scenario or smoke coverage changes should check milestones/backlog
- skill, agent, or operator config changes should synchronize mirrored files
  and `.codex/config.toml` when Codex should use the change by default

When adding or renaming agents/skills:
- mirror `.codex/agents/` with `.claude/agents/`
- mirror `.agents/skills/` with `.claude/skills/`
- register Codex defaults in `.codex/config.toml` when appropriate
- keep `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`,
  `PROJECT_CUSTOM_INSTRUCTIONS.md`, and related config synchronized

New agents or skills must solve a repeated repo workflow or repeated risk area.

## Work / Verify Records

- Meaningful implementation or operator-rule work ends with a Korean
  `work/<month>/<day>/YYYY-MM-DD-<slug>.md` closeout.
- Meaningful verification or truth-reconciliation work ends with a Korean
  `verify/<month>/<day>/YYYY-MM-DD-<slug>.md` note.
- Persistent records in `work/`, `verify/`, and `report/` default to Korean.
- Execution-facing `.pipeline/` slots default to concise English-led
  instructions.
- Keep file paths, test names, selectors, field names, and literal identifiers
  unchanged regardless of record language.
- Closeout notes should record changed files, used skills, reason, core
  changes, actual verification, and remaining risk. If no files changed in a
  verification note, write `변경 파일 - 없음`.
- Do not claim an unrun check. If broad unittest, browser/E2E, or long soak was
  intentionally skipped, say so and explain the risk basis.

## Safety / IP

- Never silently save, overwrite, delete, move, publish, merge, or run risky
  external actions.
- Note writing is approval-gated.
- Web investigation is read-only, permission-gated, locally logged, and
  secondary to local document work.
- OCR remains unsupported unless explicitly implemented; do not fail silently.
- Avoid user-facing dependence on third-party model branding.
