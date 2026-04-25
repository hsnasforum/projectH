# 2026-04-24 available sync count button visibility

## 변경 파일
- `app/handlers/preferences.py`
- `tests/test_preference_handler.py`
- `app/frontend/src/api/client.ts`
- `app/frontend/src/components/PreferencePanel.tsx`
- `e2e/tests/web-smoke.spec.mjs`
- `app/static/dist/assets/index.js`
- `work/4/24/2026-04-24-available-sync-count-button-visibility.md`

## 사용 skill
- `security-gate`: sync 버튼 노출 조건이 local preference candidate 생성 POST의 진입점을 제어하므로, write-capable 동작이 기존 local/audit 경계 안에 머무는지 확인했습니다.
- `e2e-smoke-triage`: browser-visible 버튼 조건과 mock audit contract가 바뀌어 focused Playwright rerun 범위를 확인했습니다.
- `finalize-lite`: handoff 범위, 실행 검증, 문서 동기화 필요 여부를 마무리 점검했습니다.
- `work-log-closeout`: 실제 변경 파일과 실행 검증만 한국어 `/work` 기록으로 남겼습니다.

## 변경 이유
- M29 Axis 2에서는 `adopted_corrections_count > 0`이면 sync 버튼이 항상 보였고, 이미 모두 preference candidate로 동기화된 상태에서도 사용자가 버튼을 눌러 `이미 동기화됨`만 보게 되는 혼란이 남았습니다.
- M29 Axis 3 handoff는 audit payload에 실제 동기화 가능한 ACTIVE correction 수인 `available_to_sync_count`를 추가하고, UI 버튼 표시 조건을 이 값으로 바꾸도록 요구했습니다.

## 핵심 변경
- 기존 audit owner인 `get_preference_audit()`에서 ACTIVE correction 목록을 읽고, 각 `delta_fingerprint`가 preference store에 이미 존재하는지 `_preference_exists_for_fingerprint()`로 확인해 `available_to_sync_count`를 반환하도록 했습니다.
- 기존 `adopted_corrections_count`는 유지해 전체 ACTIVE correction 수 audit 정보는 보존했습니다.
- `sync_adopted_corrections_to_candidates()` 로직은 handoff boundary대로 수정하지 않았습니다.
- `PreferenceAudit` 타입에 `available_to_sync_count?: number`를 추가하고, `PreferencePanel` 버튼 노출 조건을 `available_to_sync_count > 0`으로 교체했습니다.
- 기존 sync smoke mock에 `available_to_sync_count`를 반영했고, sync 후 audit reload에서 값이 0이 되면 `data-testid="sync-adopted-btn"` 버튼이 숨겨지는 것을 확인하도록 했습니다.
- `/app-preview`가 tracked React build 산출물을 서빙하므로 `npx vite build`로 `app/static/dist/assets/index.js`를 갱신했습니다.

## 검증
- `python3 -m unittest tests.test_preference_handler`
  - 통과: 13개 테스트 OK
- `cd app/frontend && npx vite build`
  - 통과: 48 modules transformed, `app/static/dist/assets/index.js` 갱신
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "동기화" --reporter=line`
  - 통과: 1 passed
- `rg -n "available_to_sync_count|sync-adopted-btn|sync-adopted-to-candidates" app/handlers/preferences.py app/frontend/src/api/client.ts app/frontend/src/components/PreferencePanel.tsx tests/test_preference_handler.py e2e/tests/web-smoke.spec.mjs app/static/dist/assets/index.js`
  - 통과: backend audit, frontend type/condition, e2e mock, build 산출물 반영을 확인했습니다.
- `git diff --check`
  - 통과: 출력 없음

## 남은 리스크
- handoff는 `preference_audit_payload()`를 언급했지만 현재 repo의 실제 audit payload owner는 `get_preference_audit()`라서 그 메서드에 구현했습니다.
- 이번 변경은 버튼 표시 조건과 audit count 보강만 다루며, backend route, storage schema, sync write 로직은 변경하지 않았습니다.
- 작업 시작 전부터 dirty였던 `app/web.py`, `docs/MILESTONES.md`, 기존 `report/`, `verify/`, `/work` untracked 파일들은 이번 Axis 3 범위 밖이라 변경하지 않았습니다.
- commit, push, branch/PR publish, next-slice 선택, `.pipeline/advisory_request.md`, `.pipeline/operator_request.md` 작성은 수행하지 않았습니다.
