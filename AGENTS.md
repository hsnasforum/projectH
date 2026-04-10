# AGENTS.md

## Mission

Build and maintain a **local-first AI assistant web MVP** for personal document work, with the first reviewed-memory slice shipped (review queue, aggregate apply trigger, emitted/apply/result/active-effect path, stop-apply, reversal, and conflict-visibility).

The product should help users:
- read local files
- summarize and search documents
- keep session history locally
- save notes only through explicit approval
- inspect evidence, sources, and audit logs

Long term, the project may evolve toward a proprietary model.
**Current phase is not model creation.** Current phase is defining the product loop, correction/approval memory, evidence policy, and evaluation structure that a future tuned or proprietary model would need.

## Long-Term North Star

Long term, `projectH` aims to become a **teachable local personal agent**:
- the user can teach it through correction, approval, rejection, and examples
- it retains durable preferences and working style locally
- it later expands from document work into constrained local tool or program operation
- risky actions remain explicit, auditable, and approval-gated

This north star is **not** the current shipped contract. The current shipped contract remains a document-first MVP.

## Current Product Slice

The repository currently implements a Python-based local web shell with:
- local web shell on `127.0.0.1`
- recent sessions and conversation timeline
- file summary / document search / general chat modes
- approval-based save flow
- reissue approval flow for changing save paths
- evidence/source panel with source-role trust labels
- structured search result preview panel
- summary source-type labels (`문서 요약` / `선택 결과 요약`)
- summary span / applied-range panel
- response origin badge (`MOCK`, `OLLAMA`, `WEB`, `SYSTEM`) with separate answer-mode badge for web investigation, source-role trust labels, and verification strength tags in origin detail
- applied-preferences badge (`선호 N건 반영`)
- streaming progress and cancel
- response feedback capture
- grounded-brief artifact trace anchor, original-response snapshot, corrected-outcome capture, corrected-save bridge, and artifact-linked reject/reissue reason traces
- PDF text-layer reading and OCR-not-supported guidance
- permission-gated web investigation (disabled/approval/enabled per session) with local JSON history, in-session reload, and history-card badges (answer-mode badges, color-coded verification-strength badges, color-coded source-role trust badges)
- entity-card / latest-update answer-mode distinction with separate verification labels and entity-card strong-badge downgrade
- claim-coverage panel with status tags, actionable hints, source role with trust level labels, color-coded fact-strength summary bar, and dedicated plain-language focus-slot reinvestigation explanation (reinforced / regressed / still single-source / still unresolved)
- review queue (`검토 후보`), aggregate apply trigger (`검토 메모 적용 후보`), and emitted/apply/result/active-effect path, stop-apply, reversal, and conflict-visibility
- Playwright smoke coverage for the core browser flows

Do not describe this repository as a generic starter unless the user explicitly asks for historical context.

## Product Priorities

Priority order:
1. Local-first behavior
2. Approval-based safety
3. Practical document productivity
4. Teachability through corrections, approvals, and feedback-ready structure
5. Auditable evidence and source handling
6. Commercial/IP-safe architecture
7. Replaceable model/runtime/storage seams

## Current Scope Boundaries

### In Scope
- local file reading
- document summarization
- document search
- session persistence
- approval-gated note saving
- task and search logs
- evidence-backed web investigation as a **secondary** mode

### Out of Scope For The Current Phase Unless Explicitly Requested
- wake-word voice assistant
- mobile app
- browser login automation
- autonomous destructive actions
- always-on background agents
- large-scale independent pretraining
- cloud-first architecture
- broad desktop or program operation outside tightly approved flows

### Long-Term Direction But Not Current Contract
- structured correction memory
- durable user preference memory
- approval-gated local tool or program operation
- reusable trajectories for later personalization or proprietary-model training

## Repository Map

- `app/`
  - local web shell and CLI entrypoints
  - web template and request handling
- `core/`
  - orchestration, intent classification, approval logic, investigation pipeline
- `tools/`
  - explicit auditable tools such as file read, file search, web search, note writing
- `storage/`
  - local session JSON, web search history JSON, task log JSONL
- `model_adapter/`
  - provider-swappable runtime adapters
- `docs/`
  - product, spec, architecture, acceptance, milestones, backlog
- `plandoc/`
  - strategic and staged roadmap documents that sit above the current shipped contract
- `work/`
  - tracked Korean closeout notes and operator handoff context
- `verify/`
  - tracked Korean verification rerun notes and truth-reconciliation handoff results
- `report/`
  - occasional Korean whole-project trajectory audits or milestone-level review memos
  - `report/gemini/` stores Gemini advisory or mediation logs
- `.pipeline/`
  - rolling automation handoff slots for the single-Codex tmux flow
  - `claude_handoff.md` is the Claude-only execution slot in the current stage-3 flow
  - `gemini_request.md` is the Codex -> Gemini arbitration request slot in the current stage-3 flow
  - `gemini_advice.md` is the Gemini -> Codex advisory slot in the current stage-3 flow
  - `operator_request.md` is the operator-only stop slot in the current stage-3 flow
  - `codex_feedback.md` is optional scratch or legacy compatibility text and is no longer part of the execution path
  - `gpt_prompt.md` is an optional or legacy scratch slot and is no longer part of the canonical flow
- `.agents/skills/`, `.claude/skills/`
  - reusable repo-specific skills
- `.codex/config.toml`
  - Codex local defaults, enabled skills, and subagent registry
- `.codex/agents/`, `.claude/agents/`
  - planning/review/spec/QA helper agents

Current source-of-truth docs live in the root `docs/` directory.
`docs/recycle/` contains retained drafts and historical notes unless a file is explicitly promoted into the root docs set.

## Agent / Skill Surfaces

- `.codex/config.toml`
  - enables repo-specific skills for Codex
  - registers repo helper agents that should map to repeated workflows or risks
  - `.codex/agents/`
  - Codex subagent definitions
  - current useful roles include:
    - `planner`
    - `reviewer`
    - `spec-editor`
    - `qa-e2e-reviewer`
    - `approval-auditor`
    - `investigation-reviewer`
    - `documenter`
    - `trace-implementer`
- `.claude/agents/`
  - mirrored prompts for the same helper-agent roles
- `.agents/skills/`, `.claude/skills/`
  - mirrored repo-specific skills
  - current useful skills include:
    - `approval-flow-audit`
    - `doc-sync`
    - `e2e-smoke-triage`
    - `investigation-quality-audit`
    - `mvp-scope`
    - `release-check`
    - `round-handoff`
    - `security-gate`
    - `work-log-closeout`

## Single Codex Pipeline Convention

- When tmux or a comparable split-lane setup is used, the canonical lanes are:
  - Claude = implementation lane
  - Codex = round verification plus handoff lane
  - watcher = file-watch and delivery helper lane
- Codex responsibilities:
  - read the newest `/work` note first
  - read the newest same-day `/verify` note if one exists
  - rerun the requested verification honestly
  - leave or update the persistent `/verify` note
  - write the next Claude-facing execution handoff to `.pipeline/claude_handoff.md` when one exact slice is fixed
  - write `.pipeline/gemini_request.md` when Codex needs a third-party tie-break before operator escalation
  - if an active Claude session asks a live side question such as context exhaustion, session rollover, or continue-vs-switch, use `.pipeline/gemini_request.md` only as Codex↔Gemini coordination and relay the answer back to Claude as a short lane reply instead of rewriting `.pipeline/claude_handoff.md` mid-session
  - write `.pipeline/operator_request.md` when automation must stop for a real operator decision
- `.pipeline/claude_handoff.md` is the current Claude-only execution slot.
- `.pipeline/claude_handoff.md` should declare `STATUS: implement` and should include `CONTROL_SEQ`.
- When `STATUS: implement` is active, Claude may only implement that exact slice or emit a pane-local `STATUS: implement_blocked` sentinel with `BLOCK_REASON`, `REQUEST: codex_triage`, `HANDOFF`, `HANDOFF_SHA`, and `BLOCK_ID`.
- Claude implement rounds stop after the bounded file edits plus the canonical `/work` closeout. Claude must not commit, push, publish a branch, or open a PR from the implement lane.
- watcher should auto-route that `implement_blocked` sentinel to Codex triage instead of opening an operator stop directly.
- `.pipeline/gemini_request.md` is the current Codex -> Gemini arbitration slot.
- `.pipeline/gemini_request.md` should declare `STATUS: request_open` and should include `CONTROL_SEQ` while pending.
- `.pipeline/gemini_advice.md` is the current Gemini -> Codex advisory slot.
- `.pipeline/gemini_advice.md` should declare `STATUS: advice_ready` and should include `CONTROL_SEQ` while pending.
- `.pipeline/session_arbitration_draft.md` is an optional watcher-generated non-canonical draft slot.
- `.pipeline/session_arbitration_draft.md` should declare `STATUS: draft_only` only, and must not be treated as a stop/go execution signal.
- `.pipeline/operator_request.md` is the current operator-only stop slot.
- `.pipeline/operator_request.md` should declare `STATUS: needs_operator`, should include `CONTROL_SEQ`, and should record:
  - why automation is stopping now
  - which latest `/work` and `/verify` pair the stop is based on
  - what the operator must decide before automation can resume
- Gemini is advisory only:
  - it may write `report/gemini/...md`
  - it may write `.pipeline/gemini_advice.md`
  - it must not directly write `.pipeline/claude_handoff.md` or `.pipeline/operator_request.md`
  - it should prefer file edit/write tools for advisory output instead of shell heredoc or shell redirection
  - watcher prompts for Gemini should prefer explicit `@path` file mentions and exact advisory output paths over loose path prose
  - pane-only answers do not close the advisory round; the round is complete only after both `report/gemini/...md` and `.pipeline/gemini_advice.md` are written
  - if the advice is answering an active Claude session's side question, Codex should relay that answer as a short lane reply and keep `.pipeline/claude_handoff.md` unchanged until the session boundary or next round handoff
- `.pipeline/codex_feedback.md` may still exist as optional scratch, but Claude should not rely on it as a direct execution slot.
- In automation, the newest valid control file wins by `CONTROL_SEQ` first and `mtime` only as a fallback, and stale control files are excluded from dispatch:
  - `.pipeline/claude_handoff.md` → Claude 실행
  - `.pipeline/gemini_request.md` → Gemini 실행
  - `.pipeline/gemini_advice.md` → Codex follow-up
  - `.pipeline/operator_request.md` → 자동 진행 중단, operator 대기
- `.pipeline/session_arbitration_draft.md` is not a control file. watcher may write it as a draft only after an active Claude session shows the escalation pattern and the lanes are settled enough for arbitration: Codex/Gemini panes must be idle, and Claude must be either idle or stably showing the escalation text for a short settle window. watcher should clear that draft again when Claude activity resumes or canonical Gemini/operator control opens, and should suppress immediate same-fingerprint rewrites for a short cooldown. Codex must explicitly decide whether to ignore it, answer Claude directly, or promote it into `.pipeline/gemini_request.md`.
- `.pipeline/gpt_prompt.md` may remain as an optional or legacy scratch slot, but it is no longer required for the canonical flow.
- Persistent records in `/work`, `/verify`, and `report/` should default to Korean unless the user explicitly asks otherwise.
- Execution-facing rolling slots in `.pipeline/` should default to concise English-led instructions so Claude, Codex, and Gemini can execute exact slices without translation drift.
- File paths, test names, selectors, field names, and literal code identifiers should stay in their original form even inside Korean records or English execution slots.
- Persistent truth still lives in `/work` and `/verify`; if `.pipeline` disagrees with them, trust the latest `/work` and `/verify`.
- watcher guarantees file-detection and pane-delivery only. If Claude or Codex is busy, interrupted, or not actually ready to receive input, that is a lane/session-state issue rather than a `.pipeline` contract issue.
- `.pipeline/claude_handoff.md` is the round-start execution contract, not a live side-channel. Mid-session Gemini arbitration answers should normally return to Claude as a short lane reply so later troubleshooting can still compare the finished work against the unchanged handoff that started the round.

## Codex Review Scope

- In the canonical flow, Codex is not the default whole-project auditor for every round.
- Codex should first verify whether the latest Claude `/work` note is truthful:
  - the claimed code changes are actually present
  - the claimed docs changes match implementation
  - the claimed checks were actually rerun when required
  - the round did not widen scope away from current MVP priorities
- Treat `/verify` as the review report for the latest Claude round plus a narrow direction guard, not as a mandatory full-repository diagnosis.
- After that review, Codex should either:
  - choose one exact next slice and write `STATUS: implement` to `.pipeline/claude_handoff.md`, or
  - write `.pipeline/gemini_request.md` when a third-party tie-break is needed, or
  - explicitly stop automation with `.pipeline/operator_request.md`
- In the canonical flow, Codex should not close a verification round with pane-only reasoning or a control-slot rewrite alone. Codex must leave or update `/verify` before writing the next control slot.
- When the latest `/work` and `/verify` already closed one family truthfully, prefer automatic next-slice selection over `needs_operator` if one smaller same-family follow-up remains.
- Default automatic tie-break order is:
  - same-family current-risk reduction
  - same-family user-visible improvement
  - new quality axis
  - internal cleanup
- However, if the same day already contains 3 or more same-family docs-only truth-sync rounds in a row, Codex must not auto-select yet another narrower docs-only micro-slice from that family. At that point Codex should either:
  - choose one slightly larger but still bounded docs-only bundle that closes the remaining same-family drift in one round, or
  - open `.pipeline/gemini_request.md` or `.pipeline/operator_request.md` instead of extending the docs-only micro-loop
- If Codex stops with `.pipeline/operator_request.md`, the stop request should still explain the reason and the missing operator decision instead of leaving the rolling slot empty.
- Do not push slice selection back onto Claude with wording such as "continue only if you can find a good slice."
- Use a broader whole-project audit only when explicitly requested or when a milestone, release, or trajectory check is needed.
- When a broader audit is needed, record it under `report/` so it does not overwrite the meaning of `/verify`.

## Slice Selection Guardrails

- The next slice must improve at least one of the following:
  - user-visible value in the current document-first MVP
  - a concrete current-risk reduction
  - a currently shipped contract that is actually broken or misleading
- Do not choose the next slice only because a route, helper, contract family, or handler-level regression is still incomplete.
- Do not let uncovered verification gaps alone drive roadmap priority unless they block a currently shipped user flow.
- Prefer slices that the user can see, feel, or directly benefit from over internal completeness work.
- Do not choose a micro-slice when one slightly larger bounded slice can close the same user-visible or current-risk unit within the same verification family.
- If the latest round already closed one family truthfully, prefer the next smallest same-family current-risk reduction before opening a different quality axis.
- But if same-day history already shows 3 or more consecutive same-family docs-only truth-sync rounds, stop shrinking that family into smaller docs-only slices. Close the remaining docs-only drift as one bounded bundle or escalate instead.
- When multiple plausible slices remain, choose in this order unless a newer `/verify` gives a stronger reason otherwise:
  - current-risk reduction
  - same-family user-visible improvement
  - new quality axis
  - internal cleanup
- Use `STATUS: needs_operator` only when:
  - two or more candidates remain genuinely tied after the order above, or
  - approval-record or truth-sync work must happen before any new implementation slice can start.

## Reviewed-Memory Planning Boundary

- Reviewed-memory remains in scope, but planning should proceed from the user-visible loop outward, not from internal contract completeness inward.
- For current planning and handoff purposes, the default reviewed-memory anchor is:
  - the reviewed-memory path becomes visible to the user
  - the effect can become active
  - the effect can be explicitly stopped
- Later reviewed-memory layers that may already exist in code or historical notes, such as deeper reversal, conflict-visibility, or route-by-route handler completeness, must not automatically become the next default slice.
- If a later reviewed-memory layer is chosen again, the handoff must explain why it improves current MVP value more than summary quality, search quality, approval UX, evidence UX, or current user-visible reviewed-memory clarity.

## Verification Scope Rules

- Verification should be risk-based, not maximal by default.
- Run the narrowest relevant check first.
- For Playwright-only smoke tightening, selector-only drift fixes, or single-scenario fixture updates, rerun the isolated affected browser scenario first instead of jumping straight to the full browser suite.
- Use full browser or end-to-end verification only when:
  - a browser-visible contract changed
  - a release or ready decision is being made
  - a current browser flow is suspected broken
  - the change touched shared browser helpers or multiple browser scenarios
  - an isolated browser rerun suggests broader browser-family drift
- Do not treat every focused service or handler regression as a reason to rerun the full browser suite.
- Do not let uncovered route-level regressions automatically become the next product slice unless they protect a currently shipped user-facing contract.

## Working Rules

1. Inspect the current implementation before changing docs or behavior.
2. Prefer the smallest defensible change.
3. Keep default behavior read-heavy and approval-based.
4. Do not silently widen scope from “document assistant” into “general-purpose web chatbot.”
5. If implementation and docs disagree, **make docs match implementation**, or mark the gap as `TODO` / `OPEN QUESTION`.
6. Separate facts, assumptions, and recommendations when useful.
7. Respond to the user in Korean honorifics.
8. If you add or rename an agent, mirror it across `.codex/agents/` and `.claude/agents/`, and register it in `.codex/config.toml`.
9. If you add or rename a repo skill, mirror it across `.agents/skills/` and `.claude/skills/`, and enable it in `.codex/config.toml` if Codex should use it by default.
10. New agents or skills must solve a repeated repo workflow or repeated risk area. Do not add generic prompts with no clear project-specific role.
11. Keep operator instructions short, implementation-truthful, and tied to current MVP scope.
12. When discussing strategy, always separate:
   - current shipped contract
   - next phase design target
   - long-term north star
13. Use `trace-implementer` for small additive grounded-brief trace or memory-foundation implementation slices that must keep current UI stable while moving code, tests, and docs together.
14. Use `round-handoff` when a Codex round is complete and you need to re-check the latest `/work` note, rerun honest verification, leave or update a `/verify` note, and draft the next operator prompt without overstating progress.
15. In the single-Codex tmux flow, keep Codex responsible for rerun verification and next-Claude feedback together; do not reintroduce a second canonical Codex lane unless the docs are updated again.
16. In automation handoff, Claude should implement only `.pipeline/claude_handoff.md` when it says `STATUS: implement`. If that slice is blocked, Claude should emit the `STATUS: implement_blocked` sentinel instead of asking the operator to choose. Gemini와 operator stop files must not be routed to Claude.
17. Prefer extending existing shared helpers, queries, scripts, and prompts over adding near-copy code paths. If temporary duplication is unavoidable, say why and leave a clear cleanup path.
18. Do not split one coherent task into many ultra-small slices just to keep rounds tiny. Prefer the smallest coherent reviewable slice that closes meaningful progress when the files and verification path naturally belong together.

## Personalization / Learning Rules

- Treat user corrections, approvals, rejections, and examples as future personalization or training assets, but do not present them as model learning unless that learning path is actually implemented.
- Distinguish transient session context, durable preference memory, and future training artifacts.
- Prefer structures that preserve later teachability:
  - accepted output
  - corrected output
  - approval / rejection reason
  - preference signal
  - evidence and source trace
- Future program or tool operation must remain observable, approval-gated, and reversible.
- Do not claim autonomous desktop or program control as current behavior unless it is explicitly implemented and tested.

## Work And Verify Log Protocol

- Meaningful implementation or operator-flow work should leave a closeout note under `work/<month>/<day>/YYYY-MM-DD-<slug>.md`.
- Meaningful verification-backed handoff or independent rerun-check work should leave a verification note under `verify/<month>/<day>/YYYY-MM-DD-<slug>.md`.
- Occasional whole-project, milestone, or trajectory audits should leave a report under `report/YYYY-MM-DD-<slug>.md`.
- Persistent notes under `work/`, `verify/`, and `report/` should default to Korean.
- Rolling execution slots under `.pipeline/` should default to English-led execution prompts.
- `.pipeline/claude_handoff.md`, `.pipeline/gemini_request.md`, `.pipeline/gemini_advice.md`, `.pipeline/operator_request.md`, and optional scratch files like `.pipeline/codex_feedback.md` never replace the persistent `/work` and `/verify` notes.
- `.pipeline/gpt_prompt.md` may remain as an optional or legacy scratch slot, but it is not required in the canonical single-Codex flow.
- In the current stage-3 single-Codex flow:
  - Claude finishes implementation and leaves `/work`
  - Codex reruns verification and leaves `/verify`
  - Codex then writes `.pipeline/claude_handoff.md` for the next Claude round when one exact slice is fixed
  - if Codex cannot narrow one exact slice yet, Codex writes `.pipeline/gemini_request.md`
  - Gemini writes `.pipeline/gemini_advice.md` plus `report/gemini/...md`
  - Codex then writes the final `.pipeline/claude_handoff.md` or `.pipeline/operator_request.md`
  - if automation must stop, Codex writes `.pipeline/operator_request.md`
- `/verify` should stay tied to the latest Claude round. Do not turn every verification note into a whole-project audit.
- Before starting a new meaningful round, check the newest note in today's `work/<month>/<day>/` folder. If there is no note for today, read the newest note from the previous day.
- Before starting a verification-backed handoff round, read the newest `work/<month>/<day>/` note first and then the newest note in today's `verify/<month>/<day>/` folder if one exists.
- New `work/` closeout notes and new `verify/` verification notes should use these sections in order unless the user explicitly asks for another format:
  - `## 변경 파일`
  - `## 사용 skill`
  - `## 변경 이유`
  - `## 핵심 변경`
  - `## 검증`
  - `## 남은 리스크`
- `## 사용 skill` is always required. If no skill was used, write `- 없음`.
- If a verification-only note changed no files, write `- 없음` under `## 변경 파일` instead of inventing a write.
- Never claim a test, command, or verification result that was not actually run.
- If operator rules, helper-agent roles, Codex config, or `/work` / `/verify` policy change, update `work/README.md` and `verify/README.md` in the same task.

## Safety Rules

Treat these as risky:
- file overwrite
- file delete
- file move/rename
- shell execution
- external network access
- background automation
- writes outside the approved working directory

Rules:
- Never add silent destructive behavior.
- Never default to overwrite.
- Approval-gated writes must remain explicit and auditable.
- Web search remains read-only, permission-gated, and logged.
- OCR remains unsupported unless explicitly added as new scope.

## Architecture Rules

Preserve clear separation between:
- UI layer
- orchestration layer
- tools/actions layer
- storage/history layer
- model/runtime adapter layer

Do not hard-wire the product to one runtime vendor or one model family.

Also preserve separation between:
- current document-first product loop
- preference or correction memory
- future training or personalization artifacts
- future action or program-operation layer

## Commercial / IP Rules

Always distinguish:
1. code license
2. model/runtime license
3. asset/data license
4. trademark/branding

Rules:
- avoid branding the product around third-party model names
- treat external search results and scraped page text as source material, not proprietary product IP
- keep user corrections, accepted outputs, preference rules, and approval traces distinct from third-party source material
- keep product identity centered on workflow, safety, and local-first UX

## Document Sync Rules

When behavior changes, update the matching docs in the same task.

### If UI behavior changes
Examples:
- panels, badges, timeline, session list, progress box, cancel button
- browser file/folder pickers
- response cards or approval cards

Update:
- `README.md`
- `docs/PRODUCT_SPEC.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/MILESTONES.md` or `docs/TASK_BACKLOG.md` if milestone state changed

### If approval payload or approval flow changes
Examples:
- `approval` object shape
- `approved_approval_id`, `reissue_approval_id`, rejection behavior
- overwrite handling

Update:
- `docs/PRODUCT_SPEC.md`
- `docs/ARCHITECTURE.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- related tests in `tests/test_smoke.py` and `tests/test_web_app.py`

### If session schema or stored search record shape changes
Examples:
- `schema_version`
- `pending_approvals`
- `permissions`
- `active_context`
- `summary_chunks`
- `claim_coverage`
- `web_search_history`

Update:
- `docs/PRODUCT_SPEC.md`
- `docs/ARCHITECTURE.md`
- `docs/TASK_BACKLOG.md` if migration/follow-up work is created
- storage tests

### If test scenarios or smoke coverage changes
Examples:
- Playwright smoke count
- service-test contract
- streaming/approval/evidence coverage

Update:
- `README.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`

### If product direction or staged roadmap changes
Examples:
- current phase vs long-term north star wording
- teachability / personalization framing
- future program-operation stage boundaries
- strategic roadmap phases

Update:
- `AGENTS.md`
- `CLAUDE.md`
- `GEMINI.md`
- `PROJECT_CUSTOM_INSTRUCTIONS.md`
- relevant files under `plandoc/`
- `docs/MILESTONES.md` or `docs/TASK_BACKLOG.md` if near-term execution priorities moved

### If skills or subagents change
Update:
- `AGENTS.md`
- `CLAUDE.md`
- `GEMINI.md`
- `PROJECT_CUSTOM_INSTRUCTIONS.md`
- `.codex/config.toml` if Codex defaults, skill enablement, or agent registry changed
- `work/README.md` and `verify/README.md` if `/work` or `/verify` logging rules changed
- matching files in `.agents/skills/`, `.claude/skills/`, `.codex/agents/`, `.claude/agents/`

### If Codex / Claude / Gemini operator config changes
Examples:
- `.codex/config.toml`
- `.codex/agents/*.toml`
- `.claude/agents/*.md`
- repo skill additions, removals, or role changes

Update:
- `AGENTS.md`
- `CLAUDE.md`
- `GEMINI.md`
- `PROJECT_CUSTOM_INSTRUCTIONS.md`
- `work/README.md` and `verify/README.md` if operator logging, handoff policy, or verification-note policy changed
- the mirrored config / agent / skill files that represent the same role

## Verification Rules

Run the narrowest relevant check first.

Common checks:
- narrow syntax check:
  - `python3 -m py_compile <files>`
- repo unit/service regression:
  - `python3 -m unittest -v`
- focused smoke slices:
  - `python3 -m unittest -v tests.test_smoke tests.test_web_app`
- isolated browser scenario rerun:
  - `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "<scenario>" --reporter=line`
- browser smoke:
  - `make e2e-test`

If behavior changed but tests were not run, say so explicitly.

## Response Checklist For Implementation Work

Always summarize:
1. goal understood
2. files affected
3. change made
4. risk or tradeoff
5. verification run / not run
