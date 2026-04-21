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

## Claude Runtime Role Contract

- Claude follows the active role binding from `.pipeline/config/agent_profile.json`, not the historical slot filename.
- `.pipeline/claude_handoff.md` remains the implement control slot name even when Claude is not the implement owner.
- In the currently applied A profile, `implement=Codex`, `verify=Claude`, and `advisory=Gemini`, so Claude is the verification + handoff owner.
- If Claude is bound to `verify`:
  - read the newest relevant `work/` note first, then the same-day `verify/` note if one exists
  - rerun the narrowest honest verification
  - leave or update the persistent `/verify`
  - write the next `.pipeline/claude_handoff.md`, `.pipeline/gemini_request.md`, or `.pipeline/operator_request.md` as needed
- If Claude is bound to `implement`:
  - implement only the exact slice in `.pipeline/claude_handoff.md` when it says `STATUS: implement`
  - do not self-select the next slice
  - do not write `.pipeline/gemini_request.md` or `.pipeline/operator_request.md`
  - if the handoff is blocked, stale, already implemented, or otherwise not actionable, emit pane-local `STATUS: implement_blocked` with `BLOCK_REASON`, `BLOCK_REASON_CODE`, `REQUEST: codex_triage`, `ESCALATION_CLASS: codex_triage`, `HANDOFF`, `HANDOFF_SHA`, and `BLOCK_ID`, then stop
  - stop after bounded edits plus the canonical `/work` closeout. Do not commit, push, publish a branch, or open a PR from the implement lane
- If Claude is not the active owner for a role, do not treat that role's control slot as executable input.

## Handoff Interpretation

- Newest valid control wins by `CONTROL_SEQ` first and `mtime` only as a fallback.
- Which rolling slot is Claude execution input depends on the active role binding:
  - implement owner -> `.pipeline/claude_handoff.md`
  - verify/handoff owner -> latest `/work` + `/verify` pair, plus `.pipeline/gemini_advice.md` follow-up when opened
  - advisory owner -> `.pipeline/gemini_request.md`
- Older stale control files are not execution input once a newer valid control file exists.
- If `.pipeline` disagrees with persistent notes, trust the latest `/work` and `/verify`.
- If the latest `/work` and `/verify` already closed the same handoff SHA or exact slice, treat that handoff as blocked / already implemented instead of redoing it.
- When opening `.pipeline/gemini_request.md` for advisory arbitration, keep the ask anchored to the named shipped docs/code paths first; do not send Gemini into `docs/superpowers/**`, `plandoc/**`, or other historical planning docs unless the current `/work` or `/verify` explicitly cites them as the evidence source.
- If an operator stop is just a labeled choice set, such as lettered, numbered, inline parenthesized, or Korean `n안` options, that can be narrowed from current docs, milestones, and the latest `/work` + `/verify`, route it through advisory-first arbitration instead of waiting on the operator. Keep real safety, destructive, auth/credential, approval-record, and truth-sync blockers in the decision header as operator stops.
- If watcher sends an operator-retriage follow-up, close it by writing exactly one newer control slot. Returning to an idle prompt without a new control lets watcher escalate the same gated request to `.pipeline/gemini_request.md` with `operator_retriage_no_next_control`.
- Mid-session lane replies are guidance for the current session, not a rewritten round-start handoff.

## Default Engineering Rules

- Prefer the smallest coherent reviewable change that closes real progress.
- Reuse existing helpers, queries, scripts, prompts, and local patterns before adding near-copy code paths.
- Keep writes explicit and approval-aware.
- Do not widen scope from the current document-first MVP into generic web chatbot or autonomous tool-operation behavior.
- If docs and implementation disagree, make docs match implementation or mark the gap as `TODO` / `OPEN QUESTION`.

## Recursive Improvement

- 런타임/런처/워처 문제를 고칠 때 재귀개선은 "같은 종류의 다음 수정 범위를 더 작게 만드는 것"을 뜻합니다.
- 같은 incident family가 다시 나왔으면 조건문을 하나 더 얹기보다, 그 incident의 owner인 boundary/helper/module을 먼저 고칩니다.
- 새 incident family면 먼저 named incident, focused replay test, truthful runtime surface를 추가하고 그 다음 구현을 좁힙니다.
- `pipeline-launcher.py`나 controller/browser 쪽에 추가 추론을 얹어 runtime drift를 가리려 하지 않습니다. thin client는 계속 runtime truth를 읽는 쪽에 둡니다.
- long soak 재실행은 기본 증명이 아닙니다. runtime contract 자체를 크게 바꾼 경우가 아니면 launcher live stability gate + incident replay를 우선합니다.
- 수정이 끝났을 때 "다음 같은 버그가 나와도 어디를 고쳐야 하는지 더 분명해졌는가"를 기준으로 결과를 점검합니다.

## Verification Rules

- Run the narrowest relevant check first.
- If a check was not run, say so explicitly.
- Start with isolated Playwright reruns for selector drift, fixture drift, or single-scenario smoke changes. Use the broad browser suite only when the browser-visible contract widened, shared helpers changed, or a ready / release claim is being made.
- `finalize-lite` is the implementation-side wrap-up skill for this repo. Use it to combine release-check truth, doc-sync review, and `/work` closeout readiness without adding commit/push/PR, `/verify`, or next-slice selection.
- `onboard-lite` is the fast-orientation skill for unfamiliar repos or subsystems. Use it to gather real run/test entrypoints, required docs, and ownership boundaries before planning or implementation, not as a broad audit.
- `next-slice-triage` is the verification-side slice-selection wrapper. Use it only after `/work` and `/verify` truth is already current, to narrow one exact next slice or choose `gemini_request` versus `needs_operator` without rerunning verification.
- Preferred order is: `onboard-lite` for orientation when needed -> implementation -> `finalize-lite` -> `round-handoff` when verification truth needs rerun -> `next-slice-triage` only after truth is current.

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
