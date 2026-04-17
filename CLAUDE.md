# Claude Project Memory

## Current Contract

- This repository is a local-first document assistant web MVP, not a generic chatbot starter.
- Current shipped focus: local web shell, document summary/search/chat, approval-based save, evidence-backed web investigation, and the reviewed-memory loop through activation plus explicit stop.
- Long-term north star: a teachable local personal agent under explicit approval. Do not present that future stage as shipped behavior.

## Product Priorities

1. local-first behavior
2. approval-based safety
3. practical document productivity
4. teachability through correction / approval traces
5. evidence and source transparency
6. replaceable model / runtime / storage seams

## Claude Lane Contract

- Claude is the implementation lane, not the slice-selection lane.
- Read the newest relevant `work/` note first. If the handoff points to a same-day `verify/` note, read that too.
- Implement only the exact slice in `.pipeline/claude_handoff.md` when it says `STATUS: implement`.
- Do not self-select the next slice.
- Do not write `.pipeline/gemini_request.md` or `.pipeline/operator_request.md`.
- If the handoff is blocked, stale, already implemented, or otherwise not actionable, emit pane-local `STATUS: implement_blocked` with `BLOCK_REASON`, `BLOCK_REASON_CODE`, `REQUEST: codex_triage`, `ESCALATION_CLASS: codex_triage`, `HANDOFF`, `HANDOFF_SHA`, and `BLOCK_ID`, then stop.
- Stop after bounded edits plus the canonical `/work` closeout. Do not commit, push, publish a branch, or open a PR from the implement lane.

## Handoff Interpretation

- Newest valid control wins by `CONTROL_SEQ` first and `mtime` only as a fallback.
- `.pipeline/gemini_request.md`, `.pipeline/gemini_advice.md`, and `.pipeline/operator_request.md` are not Claude execution input.
- Older stale control files are not execution input once a newer valid control file exists.
- If `.pipeline` disagrees with persistent notes, trust the latest `/work` and `/verify`.
- If the latest `/work` and `/verify` already closed the same handoff SHA or exact slice, treat that handoff as blocked / already implemented instead of redoing it.
- Mid-session lane replies are guidance for the current session, not a rewritten round-start handoff.

## Default Engineering Rules

- Prefer the smallest coherent reviewable change that closes real progress.
- Reuse existing helpers, queries, scripts, prompts, and local patterns before adding near-copy code paths.
- Keep writes explicit and approval-aware.
- Do not widen scope from the current document-first MVP into generic web chatbot or autonomous tool-operation behavior.
- If docs and implementation disagree, make docs match implementation or mark the gap as `TODO` / `OPEN QUESTION`.

## Verification Rules

- Run the narrowest relevant check first.
- If a check was not run, say so explicitly.
- Start with isolated Playwright reruns for selector drift, fixture drift, or single-scenario smoke changes. Use the broad browser suite only when the browser-visible contract widened, shared helpers changed, or a ready / release claim is being made.

Common commands:
- `python3 -m py_compile <files>`
- `python3 -m unittest -v <tests>`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "<scenario>" --reporter=line`
- `make e2e-test`
- `git diff --check -- <paths>`

## Scoped Rules

- Detailed pipeline/runtime rules live in `.claude/rules/pipeline-runtime.md`.
- Detailed browser/E2E rules live in `.claude/rules/browser-e2e.md`.
- Detailed doc-sync and operator-config sync rules live in `.claude/rules/doc-sync.md`.
- Keep this top-level `CLAUDE.md` concise; move file-family detail into path-scoped rules instead of growing startup memory.

## Response Pattern

- Respond to the user in Korean honorifics.
- For meaningful work, summarize:
  1. goal
  2. files affected
  3. change made
  4. risk / open question
  5. verification
