# Claude Project Memory

## Purpose

This is Claude's mid-sized root memory. Keep startup context smaller than the
full policy docs, but preserve the operating boundaries that prevent unsafe
operator stops, duplicate handoffs, and stalled automation.

## Current Contract

- `projectH` is a local-first document assistant web MVP.
- Shipped focus: local web shell, document summary/search/chat,
  approval-based save/reissue, evidence-backed web investigation, and the
  reviewed-memory loop through visible review queue, activation, and explicit
  stop.
- Long-term north star: a teachable local personal agent under explicit
  approval. Do not describe it as shipped behavior.
- Frontier model releases such as GPT-5.5 are capability context only; they do
  not change document-first scope, replaceable runtime posture, or
  approval/operator boundaries.

## Role Binding

Claude follows `.pipeline/config/agent_profile.json`, not historical
vendor-named filenames. In the current A profile Claude is usually the
verify/handoff owner, but always trust the active binding.

Canonical role controls:
- implement input: `.pipeline/implement_handoff.md`
- advisory request: `.pipeline/advisory_request.md`
- advisory response: `.pipeline/advisory_advice.md`
- operator stop: `.pipeline/operator_request.md`

Historical aliases are read-only compatibility inputs only:
`.pipeline/claude_handoff.md`, `.pipeline/gemini_request.md`,
`.pipeline/gemini_advice.md`.

Newest valid control wins by `CONTROL_SEQ` first, `mtime` only as fallback.
If `.pipeline` conflicts with persistent notes, trust the latest relevant
`work/` and `verify/` records.

`.pipeline/harness/*.md` are role protocols, not control slots.
`.pipeline/session_arbitration_draft.md` is a watcher draft only. Treat
`.pipeline/codex_feedback.md` and `.pipeline/gpt_prompt.md` as optional scratch,
not current execution truth.

## If Bound To Verify / Handoff

- Read newest relevant `work/` note, then same-day `verify/` if present.
- Rerun the narrowest honest verification.
- Leave or update `/verify` before writing the next control.
- Write one exact `.pipeline/implement_handoff.md` when a slice is clear.
- Write `.pipeline/advisory_request.md` for next-slice ambiguity, overlapping
  candidates, or low-confidence tie-breaks.
- Write `.pipeline/operator_request.md` only for real operator-only decisions,
  approval/truth-sync blockers, immediate safety stops, or unresolved
  post-advisory ambiguity.
- Do not close a verification round with pane-only reasoning.
- If an operator stop is just labeled choices that current docs/latest
  `/work`/`/verify` can narrow, open advisory-first arbitration instead of
  waiting for the user.
- If watcher sends operator retriage, write exactly one newer control slot.
  Returning idle with no control can trigger `operator_retriage_no_next_control`.
- For active implement-owner side questions such as context exhaustion,
  rollover, or continue-vs-switch, relay a short answer back to the lane and
  keep the round-start implement handoff stable until the session boundary.
- Approved publish follow-up belongs here, not in implement. Handle or
  coordinate `commit_push_bundle_authorization + internal_only` and
  `pr_creation_gate + gate_24h + release_gate` only after scoping the dirty
  tree and leaving the action auditable.
- Keep `pr_merge_gate`, destructive publication, auth/credential,
  approval-record, and truth-sync blockers as operator boundaries.

## If Bound To Implement

- Execute only the active `STATUS: implement` slice.
- Do not self-select the next slice.
- Stop after bounded edits plus canonical `/work` closeout.
- Do not commit, push, publish branches/PRs, or merge from the implement lane.
- If the handoff is blocked, stale, already implemented, or contradicted by
  latest `/work` + `/verify`, emit pane-local `STATUS: implement_blocked` with
  structured fields and stop.
- The blocked sentinel should include `BLOCK_REASON`, `BLOCK_REASON_CODE`,
  `REQUEST: verify_triage`, `ESCALATION_CLASS: verify_triage`, `HANDOFF`,
  `HANDOFF_SHA`, and `BLOCK_ID` when available.

## Automation Bias

- Do not call the user for ordinary next-step, ambiguity, stall, rollover, or
  recovery choices.
- Route ordinary ambiguity through verify/handoff and advisory first.
- Keep real-risk actions as explicit operator boundaries: destructive writes,
  credentials/auth, approval-record repair, truth-sync blockers, publication,
  and merge execution.
- Commit/push/PR creation belongs only to verified large-bundle publish
  follow-up and never to ordinary small/local implementation slices.

Turbo-lite wrapper order:
- `onboard-lite` for unfamiliar repo/subsystem orientation
- implementation
- `finalize-lite` for implementation-side verification/doc-sync/`/work`
  readiness
- `round-handoff` when verification truth must be rerun and recorded
- `next-slice-triage` only after `/work` and `/verify` truth is current

Do not use a wrapper to absorb another wrapper's responsibility.

## Engineering Rules

- Prefer the smallest coherent reviewable change.
- Reuse existing helpers, queries, scripts, prompts, and local patterns.
- Do not hardcode branch names, commit SHAs, `CONTROL_SEQ`, pane ids, Korean UI
  labels, exact operator prose, or one-off control bodies.
- Do not duplicate watcher/supervisor/launcher/controller truth logic; move
  shared truth to the owning helper and keep clients thin.
- Keep behavior local-first, read-heavy, and approval-based.
- If docs and implementation disagree, make docs match implementation or mark
  `TODO` / `OPEN QUESTION`.
- For repeated runtime incidents, improve the owning boundary, shared helper,
  replay test, or runtime surface instead of adding another higher-layer
  exception branch.
- Do not widen from document-first MVP into generic web chatbot or autonomous
  local tool operation.

## Verification

- Run the narrowest relevant check first and report skipped checks honestly.
- For browser selector/fixture drift, start with the isolated Playwright
  scenario.
- Use broad browser/E2E only when the browser contract changed, shared browser
  helpers changed, release/ready is being claimed, or isolated rerun suggests
  wider drift.

Common commands:
- `python3 -m py_compile <files>`
- `python3 -m unittest -v <tests>`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "<scenario>" --reporter=line`
- `make e2e-test`
- `git diff --check -- <paths>`

## Read On Demand

- Pipeline/runtime details: `.pipeline/README.md`,
  `.claude/rules/pipeline-runtime.md`, `.pipeline/harness/*.md`
- Browser/E2E details: `.claude/rules/browser-e2e.md`
- Doc-sync details: `.claude/rules/doc-sync.md`
- Product truth: `docs/project-brief.md`, `docs/PRODUCT_SPEC.md`,
  `docs/ARCHITECTURE.md`, `docs/ACCEPTANCE_CRITERIA.md`,
  `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md`
- Latest truth: newest relevant `work/` and `verify/` notes

Do not read `docs/superpowers/**`, `docs/recycle/**`, or `plandoc/**` unless
the task, active control, latest notes, or user explicitly makes them current
evidence.
For large planning docs such as `docs/TASK_BACKLOG.md`, `docs/MILESTONES.md`,
or `docs/NEXT_STEPS.md`, use targeted `rg` / section reads instead of full-file
`cat`; if evidence remains insufficient, name the missing exact evidence.

When docs must sync, use implementation truth. UI changes usually affect
`README.md`, `docs/PRODUCT_SPEC.md`, and `docs/ACCEPTANCE_CRITERIA.md`;
approval/session/schema changes usually affect `docs/ARCHITECTURE.md`; skill
or agent changes must keep Codex/Claude mirrors aligned.

## Response Pattern

Respond to the user in Korean honorifics. For meaningful work, summarize goal,
files affected, change made, remaining risk/open question, and verification.
