STATUS: verified
CONTROL_SEQ: 129
BASED_ON_WORK: work/4/24/2026-04-24-available-sync-count-button-visibility.md
VERIFIED_BY: Claude
NEXT_CONTROL: .pipeline/implement_handoff.md CONTROL_SEQ 130 (M29 release gate — make e2e-test + MILESTONES.md closure)

---

## M29 Axis 3 — available_to_sync_count + Button Visibility Fix

### Verdict

PASS. `app/handlers/preferences.py` + `client.ts` + `PreferencePanel.tsx` + `test_preference_handler.py` + `e2e` 변경이 `/work` 기술과 일치하고, 재검증 통과.

### Checks Rerun

- `python3 -m unittest tests.test_preference_handler` → `Ran 13 tests in 0.001s`, OK (신규 2개 포함)
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "동기화" --reporter=line` → `1 passed (5.9s)`
- `rg -n "available_to_sync_count"` 5파일 → backend, frontend type, PreferencePanel, 테스트 4개, e2e mock 모두 매칭 확인
- `git diff --check` → OK (출력 없음)

### Implementation Confirmed

- `app/handlers/preferences.py:161,179,185,191`: `get_preference_audit()` — `available_to_sync_count` 계산 (ACTIVE correction 중 fingerprint 미존재 수) + 반환 확인
- `app/frontend/src/api/client.ts:282`: `available_to_sync_count?: number` 타입 필드 추가 확인
- `app/frontend/src/components/PreferencePanel.tsx:131–132`: `availableToSyncCount = audit?.available_to_sync_count ?? 0` + `canSyncAdoptedCorrections = availableToSyncCount > 0` 조건 교체 확인
- `tests/test_preference_handler.py:235,244,261,285`: 4개 assertion으로 count 0(이미 동기화), count 1(미동기화) 케이스 검증 확인
- `e2e/tests/web-smoke.spec.mjs:11942`: `available_to_sync_count: syncRequests === 0 ? 1 : 0` — sync 후 버튼 숨김 동작 mock 반영 확인

### Discrepancy: handoff method name vs actual

handoff는 `preference_audit_payload()`를 언급했으나 실제 audit owner는 `get_preference_audit()` (line 161). `/work` 노트에 명시됨. 기능 구현에 영향 없음.

### What Was Checked

- `python3 -m unittest tests.test_preference_handler` (13개 전체), Playwright 1-scenario 재실행
- `rg available_to_sync_count` 5파일 패턴 매칭, `git diff --check`

### What Was Not Checked

- `make e2e-test` 미실행: SCOPE_HINT "narrowest checks for claimed changes". Axes 2-3 UI 변경에 대한 전체 143-scenario 브라우저 회귀는 M29 release gate 라운드(seq 130)에서 실행 예정.
- 전체 `python3 -m unittest discover` 미실행: Axis 3 변경 파일은 `preferences.py` (backend audit) + TypeScript/e2e. `test_preference_handler` 13개로 backend change coverage 충분.

### M29 Axes 1–3 Summary

| Axis | 내용 | 검증 |
|---|---|---|
| Axis 1 (seq 127) | backend bridge: `sync_adopted_corrections_to_candidates()` + POST endpoint | 11 tests PASS |
| Axis 2 (seq 128) | UI 버튼: `data-testid="sync-adopted-btn"` + inline feedback | 1 Playwright PASS |
| Axis 3 (seq 129) | `available_to_sync_count` + 정확한 버튼 표시 조건 | 13 tests + 1 Playwright PASS |

### Residual Risk

- 전체 e2e 회귀 미검증: M29 Axes 2–3에서 browser-visible PreferencePanel contract 변경됨. `make e2e-test` release gate가 M29 closure 전 필요.
- Vite build artifact `app/static/dist/assets/index.js` commit bundle 시 포함 대상.
