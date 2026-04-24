STATUS: verified
CONTROL_SEQ: 103
BASED_ON_WORK: work/4/24/2026-04-24-m25-axis1-preference-audit.md
HANDOFF_SHA: 0a49752
VERIFIED_BY: Claude
SUPERSEDES: verify/4/24/2026-04-24-m24-axis1-list-incomplete-corrections.md CONTROL_SEQ 102
NEXT_CONTROL: .pipeline/operator_request.md CONTROL_SEQ 103
PUSH_RESULT: feat/watcher-turn-state 5868390..0a49752 pushed to origin (2026-04-24)

---

## M25 Axis 1 Claim: GET /api/preferences/audit + PreferencePanel Summary

**Work**: `work/4/24/2026-04-24-m25-axis1-preference-audit.md`
**Commit**: 0a49752

### Summary

`get_preference_audit()` added to `app/handlers/preferences.py` — aggregates `list_all()` into `{total, by_status, conflict_pair_count}` using the existing `_jaccard_word_similarity` threshold. `GET /api/preferences/audit` wired in `app/web.py`. `PreferenceAudit` TypeScript interface + `fetchPreferenceAudit()` added to `client.ts`. `PreferencePanel.tsx` shows compact 1-line audit summary (`활성 N · 후보 M · 충돌 K쌍`). Vite dist rebuilt. 1 new unit test. `docs/MILESTONES.md` M25 Axes 1-2 + closed marker.

### Checks Run

- `python3 -m py_compile app/handlers/preferences.py app/web.py` → **OK**
- `python3 -m unittest tests.test_preference_handler -v` → **6 tests OK** (5 existing + 1 new `test_get_preference_audit_returns_counts`)
- `cd app/frontend && npx tsc --noEmit` → **OK (exit 0)**
- `cd app/frontend && npx vite build` → **OK** (index.js 299 kB, index.css 31 kB)
- `git diff --check` (all changed files) → **OK**
- `make e2e-test` (full suite, M25 Axis 2 release gate) → **143 passed (10.7m)** ← PASS

### Checks Not Run

- PreferencePanel audit summary manual visual inspection — no Playwright assertion for the new line (per handoff boundary); TypeScript pass + no test regressions confirm contract.

### Verdict

**PASS.** **Milestone 25 closed** (Axes 1–2): preference lifecycle audit endpoint, compact summary UI, and release gate complete.

---

## Current Shipped Truth

| Item | SHA |
|---|---|
| M22 Axes 1–3 | ed77ff2, acacb28, (143 passed) |
| M23 Axis 1 JSON guard | 3a16884 |
| M24 Axis 1 list_incomplete_corrections | 0e9f46e |
| **M25 Axes 1–2 preference audit + release gate** | **0a49752** |
| **Milestone 25** | **Closed** |
| PR #32 (M20 Axis 2–M22) | OPEN — operator merge pending |
| Release gate | M25 Axis 2: 143 passed (10.7m, 2026-04-24) |

## Risks / Open Questions

1. **PR #32 merge**: M22/M23/M24/M25 commits are on `feat/watcher-turn-state`; PR #32 description still covers M20-M22 only — operator decision pending.
2. **Advisory timeouts**: Gemini unavailable for extended periods; council convergence used for M23/M24/M25. Next direction still requires advisory or operator input.
3. **Global candidate test isolation**: still open (Option A, deferred).
