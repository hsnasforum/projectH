# Claude Project Memory

## Current Identity

This repository is a **local-first document assistant web MVP**, not a generic chatbot starter.

Long term, it is a stepping stone toward a **teachable local personal agent** that can absorb user corrections and later expand into constrained program operation under approval.

Current implemented focus:
- local web shell on `127.0.0.1`
- recent sessions and timeline
- file summary / document search / general chat
- approval-based save and reissue approval
- evidence/source panel and summary-range panel
- response origin badges
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

## Operator Surfaces

- `.codex/config.toml`: Codex defaults, enabled repo skills, agent registry
- `.codex/agents/`: Codex helper-agent definitions
- `.claude/agents/`: mirrored helper-agent definitions
- `.agents/skills/`, `.claude/skills/`: mirrored repo-specific skills
- `work/`: tracked closeout notes for Codex rounds and operator handoff
- `verify/`: tracked verification rerun notes and truth-reconciliation handoff results
- `report/`: occasional whole-project or milestone-level audit memos
- `.pipeline/`: rolling automation handoff slots; `codex_feedback.md` is the primary Codex -> Claude next-round prompt, and `gpt_prompt.md` is now optional or legacy
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
- `PROJECT_CUSTOM_INSTRUCTIONS.md`
- `.codex/config.toml`
- matching files under `.codex/agents/`, `.claude/agents/`, `.agents/skills/`, `.claude/skills/`
- `work/README.md` and `verify/README.md` if closeout, handoff, or verification-note policy changed
- relevant files under `plandoc/` if roadmap or staged strategy changed

## Work And Verify Note Reminder

- Meaningful work should leave a closeout note at `work/<month>/<day>/YYYY-MM-DD-<slug>.md`.
- Meaningful verification-backed handoff or rerun-check work should leave a verification note at `verify/<month>/<day>/YYYY-MM-DD-<slug>.md`.
- `.pipeline/codex_feedback.md` is the primary rolling latest-slot handoff file for automation and may be overwritten; it does not replace `/work` or `/verify`.
- `.pipeline/codex_feedback.md` should explicitly say either `STATUS: implement` or `STATUS: needs_operator`.
- `.pipeline/gpt_prompt.md` may remain as an optional or legacy scratch slot, but it is no longer part of the canonical single-Codex flow.
- Before a new round, read today's newest note first; if none exists, use the newest note from the previous day.
- Before a new verification-backed handoff round, read the newest `work/` note first and then the newest same-day `verify/` note if one exists.
- Keep the closeout honest: changed files, used skills, commands actually run, residual risks.

## Single Codex Reminder

- Codex = round verification and handoff lane: reads latest `/work` and `/verify`, reruns the checks needed to review that round, updates `/verify`, then writes `.pipeline/codex_feedback.md`.
- `STATUS: implement` means the next slice is already fixed and should be implemented as written.
- `STATUS: needs_operator` means the next slice is intentionally not fixed yet; do not start a new implementation round from that handoff.
- In automation, the status line is the control signal. A prose change without a status change should not be treated as a stop/go override.
- `gpt_prompt.md` is optional or legacy and should not be treated as required for the canonical flow.
- If `.pipeline` contents disagree with persistent notes, trust `/work` and `/verify`.
- Whole-project audits are exceptional and belong in `report/`; they should not silently redefine the meaning of `/verify`.

## Current Handoff Interpretation Rules

- Read `.pipeline/codex_feedback.md` as the latest operator handoff, but keep current MVP priorities above internal completeness.
- Do not self-select a new slice from `.pipeline/codex_feedback.md`.
- If the file says `STATUS: implement`, implement that one slice only.
- If the file says `STATUS: needs_operator`, wait for a new handoff instead of creating a new `/work` round.
- If watcher delivered the handoff but your lane is busy, interrupted, or mid-response, that is a session-state issue rather than a handoff-policy change.
- Do not widen a reviewed-memory slice only because more internal layers or route-level regressions remain.
- If the handoff appears to pull the work toward route-by-route completeness rather than user-visible value, prefer the smallest user-visible or current-risk-reducing interpretation that still fits the written instruction.
- Browser or end-to-end checks are not default for every round; use them when the current change actually touches browser-visible behavior or when the handoff explicitly requires a ready or release decision.
- For current planning purposes, treat the reviewed-memory user-visible loop through effect activation plus explicit stop as the default anchor; later reversal or conflict-visibility layers may exist, but they are not the automatic next slice.

## Response Pattern

For meaningful work, summarize:
1. goal
2. files affected
3. change made
4. risk / open question
5. verification
