STATUS: verified
CONTROL_SEQ: 128
BASED_ON_WORK: work/4/24/2026-04-24-adopted-correction-sync-button.md
VERIFIED_BY: Claude
NEXT_CONTROL: .pipeline/implement_handoff.md CONTROL_SEQ 129 (M29 Axis 3: available_to_sync_count backend + button visibility fix)

---

## M29 Axis 2 — Adopted Correction Sync Button UI

### Verdict

PASS. `client.ts` + `PreferencePanel.tsx` + Playwright smoke 변경이 `/work` 기술과 일치하고, 재검증 통과.

### Checks Rerun

- `git diff --check` → OK (출력 없음)
- `rg -n "sync-adopted-btn|postSyncAdoptedToPreferenceCandidates|sync-adopted-to-candidates" client.ts PreferencePanel.tsx web-smoke.spec.mjs` → 3파일 모두 매칭
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "활성 교정이 있으면 동기화 버튼이 보이고" --reporter=line` → `1 passed (6.0s)`

### Implementation Confirmed

- `app/frontend/src/api/client.ts:297–298`: `postSyncAdoptedToPreferenceCandidates()` — `POST /api/corrections/sync-adopted-to-candidates` 호출, `SyncAdoptedPreferenceCandidatesResponse` 반환 확인
- `PreferencePanel.tsx:112–125`: `handleSyncAdopted()` — `syncingAdopted` 상태 관리, API 호출, inline status 설정 (`N개 동기화됨` / `이미 동기화됨` / `동기화 실패`), `load()` 재호출 확인
- `PreferencePanel.tsx:130–131`: `canSyncAdoptedCorrections = adoptedCorrectionsCount > 0` 가드 조건 확인
- `PreferencePanel.tsx:192–201`: `data-testid="sync-adopted-btn"` 버튼 — `canSyncAdoptedCorrections`일 때만 렌더, `disabled={syncingAdopted || loading}` 확인
- `PreferencePanel.tsx:203–207`: `data-testid="sync-adopted-status"` 인라인 피드백 확인
- `e2e/tests/web-smoke.spec.mjs:11946`: `POST /api/corrections/sync-adopted-to-candidates` mock, `sync-adopted-btn` 버튼 노출+클릭, audit reload 검증 확인

### What Was Checked

- `git diff --check`, rg 패턴 매칭, Playwright 1-scenario 재실행
- `PreferencePanel.tsx:112–207` 코드 직접 확인 (handler, guard, button, feedback)

### What Was Not Checked

- `make e2e-test` (전체 143 시나리오) 미실행: 새 시나리오는 additive이며 기존 selector/helper 미변경. 좁은 isolated rerun으로 충분. browser contract 확장 없음.
- 전체 `python3 -m unittest discover` 미실행: Axis 2는 frontend-only 변경 (TypeScript/TSX + e2e). backend 파일 미변경.

### Residual Risk

- `adopted_corrections_count` 기반 버튼 표시: 이미 모두 동기화된 경우에도 버튼이 보임 — `/work` 명시적 Axis 3 deferred. `available_to_sync_count` 추가 후 수정 예정.
- Vite build artifact `app/static/dist/assets/index.js` 커밋 포함 필요 (현재 untracked 상태): commit bundle 시 포함 대상.
