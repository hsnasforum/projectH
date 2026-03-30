# AGENTS.md

## Mission

Build and maintain a **local-first AI assistant web MVP** for personal document work.

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
- evidence and source panel
- summary span / applied-range panel
- response origin badge (`MOCK`, `OLLAMA`, `WEB`, `SYSTEM`)
- streaming progress and cancel
- PDF text-layer reading and OCR-not-supported guidance
- permission-gated web investigation with local JSON history
- claim coverage / verification state and in-session history reload
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
  - tracked Codex round closeout notes and operator handoff context
- `verify/`
  - tracked verification rerun notes and truth-reconciliation handoff results
- `.pipeline/`
  - rolling automation handoff slots for the single-Codex tmux flow
  - `codex_feedback.md` is the primary next-Claude handoff slot written after verification
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
  - Codex = verification plus handoff lane
  - watcher = file-watch and delivery helper lane
- Codex responsibilities:
  - read the newest `/work` note first
  - read the newest same-day `/verify` note if one exists
  - rerun the requested verification honestly
  - leave or update the persistent `/verify` note
  - write the next Claude-facing handoff to `.pipeline/codex_feedback.md`
- `.pipeline/codex_feedback.md` is the primary rolling latest-slot file for automation.
- `.pipeline/gpt_prompt.md` may remain as an optional or legacy scratch slot, but it is no longer required for the canonical flow.
- Persistent truth still lives in `/work` and `/verify`; if `.pipeline` disagrees with them, trust the latest `/work` and `/verify`.

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
- `.pipeline/codex_feedback.md` may mirror the latest handoff for automation, but it never replaces the persistent `/work` and `/verify` notes.
- `.pipeline/gpt_prompt.md` may remain as an optional or legacy scratch slot, but it is not required in the canonical single-Codex flow.
- In the single-Codex flow:
  - Claude finishes implementation and leaves `/work`
  - Codex reruns verification and leaves `/verify`
  - Codex then writes `.pipeline/codex_feedback.md` for the next Claude round
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
- `PROJECT_CUSTOM_INSTRUCTIONS.md`
- relevant files under `plandoc/`
- `docs/MILESTONES.md` or `docs/TASK_BACKLOG.md` if near-term execution priorities moved

### If skills or subagents change
Update:
- `AGENTS.md`
- `CLAUDE.md`
- `PROJECT_CUSTOM_INSTRUCTIONS.md`
- `.codex/config.toml` if Codex defaults, skill enablement, or agent registry changed
- `work/README.md` and `verify/README.md` if `/work` or `/verify` logging rules changed
- matching files in `.agents/skills/`, `.claude/skills/`, `.codex/agents/`, `.claude/agents/`

### If Codex / Claude operator config changes
Examples:
- `.codex/config.toml`
- `.codex/agents/*.toml`
- `.claude/agents/*.md`
- repo skill additions, removals, or role changes

Update:
- `AGENTS.md`
- `CLAUDE.md`
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
