# Claude Project Memory

## Current Identity

This repository is a **local-first document assistant web MVP**, not a generic chatbot starter.

Long term, it is a stepping stone toward a **teachable local personal agent** that can absorb user corrections and later expand into constrained program operation under approval.

Current implemented focus:
- local web shell on `127.0.0.1`
- recent sessions and timeline
- file summary / document search / general chat
- approval-based save and reissue approval
- evidence/source panel with source-role trust labels
- structured search result preview panel
- summary source-type labels (`문서 요약` / `선택 결과 요약`)
- summary span / applied-range panel
- response origin badges
- applied-preferences badge (`선호 N건 반영`)
- streaming progress and cancel
- PDF text-layer support with OCR-not-supported guidance
- permission-gated web investigation with local JSON history
- claim coverage / verification state and history reload
- Playwright smoke coverage for the browser MVP

## Product Priorities

1. local-first behavior
2. approval-based safety
3. practical document productivity
4. teachability through correction/approval-ready structure
5. evidence/source transparency
6. commercial/IP-safe architecture
7. replaceable model/runtime seams

## Default Constraints

- Prefer read operations over write operations.
- Keep writes explicit and approval-gated.
- Treat external network access as risky and permission-gated.
- Do not widen scope from document assistant into broad web answer bot without explicit product direction.
- If docs and implementation disagree, align docs to implementation or mark `TODO` / `OPEN QUESTION`.
- If agent or skill files change, keep `.codex/config.toml`, mirrored agent files, and mirrored skill files synchronized.
- Always separate current shipped behavior from long-term teachable-agent roadmap.
- Do not describe preference learning, model adaptation, or program control as implemented unless the code actually supports it.
- Prefer reusing or extending existing shared helpers, queries, scripts, and prompts over duplicating code paths.
- Do not over-fragment work into many micro-slices; prefer one coherent reviewable unit when the same files and verification path naturally belong together.

## Operator Surfaces

- `.codex/config.toml`: Codex defaults, enabled repo skills, agent registry
- `.codex/agents/`: Codex helper-agent definitions
- `.claude/agents/`: mirrored helper-agent definitions
- `.agents/skills/`, `.claude/skills/`: mirrored repo-specific skills
- `work/`: tracked closeout notes for Codex rounds and operator handoff
- `verify/`: tracked verification rerun notes and truth-reconciliation handoff results
- `report/`: occasional whole-project or milestone-level audit memos
  - `report/gemini/` = Gemini advisory logs
- `.pipeline/`: rolling automation handoff slots
  - `claude_handoff.md` = Claude-only execution slot
  - `gemini_request.md` = Codex -> Gemini arbitration slot
  - `gemini_advice.md` = Gemini -> Codex advisory slot
  - `operator_request.md` = operator-only stop slot
  - `codex_feedback.md` = optional scratch or legacy compatibility text, not an execution slot
  - `gpt_prompt.md` = optional or legacy scratch slot
- `plandoc/`: staged roadmap and strategy notes above the current shipped contract

Current high-value helper roles:
- `planner`
- `reviewer`
- `spec-editor`
- `qa-e2e-reviewer`
- `approval-auditor`
- `investigation-reviewer`
- `documenter`
- `trace-implementer`

Current closeout skill:
- `work-log-closeout`

Current handoff skill:
- `round-handoff`

## Documentation Sync Reminder

If you change:
- web UI behavior
- approval payload or flow
- session/search record schema
- smoke/E2E scenarios
- agent or skill configuration / prompts
- long-term roadmap or current-phase framing

then update the matching product docs in the same task:
- `README.md`
- `docs/PRODUCT_SPEC.md`
- `docs/ARCHITECTURE.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`

And if helper-agent or repo-skill files changed, also sync:
- `AGENTS.md`
- `CLAUDE.md`
- `GEMINI.md`
- `PROJECT_CUSTOM_INSTRUCTIONS.md`
- `.codex/config.toml`
- matching files under `.codex/agents/`, `.claude/agents/`, `.agents/skills/`, `.claude/skills/`
- `work/README.md` and `verify/README.md` if closeout, handoff, or verification-note policy changed
- relevant files under `plandoc/` if roadmap or staged strategy changed

## Work And Verify Note Reminder

- Meaningful work should leave a closeout note at `work/<month>/<day>/YYYY-MM-DD-<slug>.md`.
- Meaningful verification-backed handoff or rerun-check work should leave a verification note at `verify/<month>/<day>/YYYY-MM-DD-<slug>.md`.
- Gemini advisory or mediation work should leave a note at `report/gemini/YYYY-MM-DD-<slug>.md`.
- Persistent notes in `work/`, `verify/`, and `report/` default to Korean unless the user explicitly asks otherwise.
- Execution slots in `.pipeline/` default to concise English-led instructions.
- File paths, test names, selectors, and literal code ids should stay in their original form inside either Korean notes or English execution slots.
- `.pipeline/claude_handoff.md` is the current execution slot for Claude and may be overwritten between rounds; it does not replace `/work` or `/verify`.
- `.pipeline/gemini_request.md` and `.pipeline/gemini_advice.md` are current arbitration slots; they do not replace `/work` or `/verify`.
- `.pipeline/operator_request.md` is the current stop slot for operator-only decisions and may be overwritten; it does not replace `/work` or `/verify`.
- `.pipeline/session_arbitration_draft.md` is an optional watcher-generated draft slot for Codex review only; it appears only when an active Claude session shows an escalation pattern after Codex/Gemini have gone idle and Claude is either idle or stably sitting on the escalation text for a short settle window, and it is cleared again when Claude resumes work or canonical Gemini/operator control opens. It does not replace `/work` or `/verify`.
- `.pipeline/codex_feedback.md` may remain as optional scratch or legacy compatibility text, but it is no longer part of the execution path.
- `.pipeline/gpt_prompt.md` may remain as an optional or legacy scratch slot, but it is no longer part of the canonical single-Codex flow.
- Gemini advisory writes should prefer file edit/write tools rather than shell heredoc or shell redirection so the arbitration lane can stay in its constrained write mode.
- Gemini arbitration prompts should prefer explicit `@path` file mentions and exact advisory output paths so Gemini can resolve its inputs and outputs without guessing.
- Before a new round, read today's newest note first; if none exists, use the newest note from the previous day.
- Before a new verification-backed handoff round, read the newest `work/` note first and then the newest same-day `verify/` note if one exists.
- Keep the closeout honest: changed files, used skills, commands actually run, residual risks.
- When proposing the next round, avoid artificially tiny follow-ups if one bounded slice can close the same meaningful progress.

## Single Codex Reminder

- Codex = round verification and handoff lane: reads latest `/work` and `/verify`, reruns the checks needed to review that round, updates `/verify`, then writes `.pipeline/claude_handoff.md`, `.pipeline/gemini_request.md`, or `.pipeline/operator_request.md`.
- `.pipeline/claude_handoff.md` with `STATUS: implement` means the next slice is already fixed and should be implemented as written.
- `.pipeline/gemini_request.md` and `.pipeline/gemini_advice.md` are not Claude input slots.
- `.pipeline/operator_request.md` with `STATUS: needs_operator` means the next slice is intentionally not fixed yet; do not start a new implementation round from that stop request.
- A `needs_operator` stop request should never be interpreted as "choose your own next slice." It is a stopped state with an explained reason, not an invitation to improvise.
- If Codex relays a short side answer during an active session because Gemini arbitrated a context-exhaustion, session-rollover, or continue-vs-switch question, treat that reply as lane guidance for the current session only. Do not reinterpret it as a new `.pipeline/claude_handoff.md`.
- Codex may auto-fix the next slice without operator intervention when the latest `/work` and `/verify` already closed one family and one smaller same-family current-risk reduction clearly remains.
- If Codex instead bundles several remaining docs-only truth-sync lines from one family into one bounded handoff after repeated same-day docs-only rounds, treat that bundled handoff as intentional. Do not re-split it into smaller docs-only micro-slices yourself.
- In automation, the newest control file is the signal. A prose change without a status change should not be treated as a stop/go override.
- `gpt_prompt.md` is optional or legacy and should not be treated as required for the canonical flow.
- If `.pipeline` contents disagree with persistent notes, trust `/work` and `/verify`.
- Whole-project audits are exceptional and belong in `report/`; they should not silently redefine the meaning of `/verify`.

## Current Handoff Interpretation Rules

- Read `.pipeline/claude_handoff.md` as the latest execution handoff, but keep current MVP priorities above internal completeness.
- Expect `.pipeline/claude_handoff.md` to be written in concise English-led execution language; do not rewrite that handoff into Korean before implementing it.
- Do not self-select a new slice from `.pipeline/claude_handoff.md`.
- If `.pipeline/claude_handoff.md` says `STATUS: implement`, implement that one slice only.
- If `.pipeline/gemini_request.md` or `.pipeline/gemini_advice.md` is the newest pending control file, wait instead of creating a new `/work` round.
- If `.pipeline/operator_request.md` is the newest pending control file, wait instead of creating a new `/work` round.
- `.pipeline/operator_request.md` is not a Claude input slot. Do not answer it on behalf of the operator.
- `.pipeline/codex_feedback.md` is not a Claude input slot. Prefer `.pipeline/claude_handoff.md` only for actual implementation input.
- `.pipeline/session_arbitration_draft.md` is not a Claude input slot. If Codex references it, wait for a short lane reply or a new round-start handoff instead of reading the draft as execution input.
- While a session is already active, assume `.pipeline/claude_handoff.md` remains the round-start contract unless Codex explicitly ends the round and delivers a new handoff. Mid-session side answers should be followed as short lane guidance, not as a rewritten handoff.
- If watcher delivered the handoff but your lane is busy, interrupted, or mid-response, that is a session-state issue rather than a handoff-policy change.
- Do not widen a reviewed-memory slice only because more internal layers or route-level regressions remain.
- If the handoff appears to pull the work toward route-by-route completeness rather than user-visible value, prefer the smallest user-visible or current-risk-reducing interpretation that still fits the written instruction.
- If Codex selected the slice through the same-family current-risk-first tie-break, treat that as the intended plan and do not reopen a broader comparison yourself.
- Browser or end-to-end checks are not default for every round; use them when the current change actually touches browser-visible behavior or when the handoff explicitly requires a ready or release decision.
- Playwright-only smoke tightening, selector drift, or single-scenario fixture updates should normally start with an isolated browser rerun. Do not treat every narrow browser tweak as an automatic `make e2e-test` round unless the handoff clearly widened the browser-visible contract, touched shared browser helpers, or is making a ready / release claim.
- For current planning purposes, treat the reviewed-memory user-visible loop through effect activation plus explicit stop as the default anchor; later reversal or conflict-visibility layers may exist, but they are not the automatic next slice.

## Response Pattern

For meaningful work, summarize:
1. goal
2. files affected
3. change made
4. risk / open question
5. verification
