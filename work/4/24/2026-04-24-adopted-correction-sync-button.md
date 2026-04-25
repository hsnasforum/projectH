# 2026-04-24 adopted correction sync button

## 변경 파일
- `app/frontend/src/api/client.ts`
- `app/frontend/src/components/PreferencePanel.tsx`
- `app/static/dist/assets/index.js`
- `e2e/tests/web-smoke.spec.mjs`
- `work/4/24/2026-04-24-adopted-correction-sync-button.md`

## 사용 skill
- `security-gate`: UI 버튼이 local preference candidate 생성 POST를 호출하므로 local-first, 활성화/승인 경계, 로깅 경계를 확인했습니다.
- `e2e-smoke-triage`: browser-visible selector와 flow가 추가되어 isolated Playwright 시나리오만 추가/실행했습니다.
- `finalize-lite`: handoff 범위, 실제 검증, 문서 동기화 필요 여부를 마무리 점검했습니다.
- `work-log-closeout`: 이번 라운드 변경 파일과 실행 검증만 한국어 `/work` 기록으로 남겼습니다.

## 변경 이유
- M29 Axis 1에서 backend `POST /api/corrections/sync-adopted-to-candidates`가 추가되었지만, `PreferencePanel`에서는 `adopted_corrections_count`를 텍스트로만 보여주고 사용자가 sync를 실행할 수 없었습니다.
- M29 Axis 2 handoff는 `adopted_corrections_count > 0`일 때 버튼을 노출하고 클릭 결과를 인라인으로 보여주는 UI 연결을 요구했습니다.

## 핵심 변경
- `postSyncAdoptedToPreferenceCandidates()` API client 함수를 추가해 `POST /api/corrections/sync-adopted-to-candidates`를 호출하도록 했습니다.
- `PreferencePanel` audit row에 `data-testid="sync-adopted-btn"` 버튼을 추가했고, `adopted_corrections_count > 0`일 때만 노출되도록 했습니다.
- 버튼 클릭 중에는 disabled 상태가 되며, 응답에 따라 `1개 동기화됨` 또는 `이미 동기화됨` 인라인 상태를 표시합니다.
- sync 성공 후 기존 `load()`를 재호출해 preference list와 audit을 함께 다시 불러오도록 했습니다.
- `e2e/tests/web-smoke.spec.mjs`에 API mock 기반 focused scenario를 추가해 버튼 노출, POST 호출, audit reload, inline feedback을 확인했습니다.
- `/app-preview`가 tracked React build 산출물을 서빙하므로 `npx vite build`로 `app/static/dist/assets/index.js`를 갱신했습니다.

## 검증
- `cd app/frontend && npx vite build`
  - 통과: 48 modules transformed, `app/static/dist/assets/index.js` 갱신
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "활성 교정이 있으면 동기화 버튼이 보이고" --reporter=line`
  - 통과: 1 passed
- `rg -n "sync-adopted-btn|sync-adopted-status|후보 동기화|동기화됨|sync-adopted-to-candidates" app/static/dist/assets/index.js`
  - 통과: build 산출물에 sync endpoint, 버튼 test id, 상태 문구가 반영된 것을 확인했습니다.
- `git diff --check`
  - 통과: 출력 없음

## 남은 리스크
- 이번 구현은 backend, storage, pipeline control slot을 수정하지 않았습니다.
- `adopted_corrections_count`는 "동기화 가능 수"가 아니라 ACTIVE correction 수라서, 이미 모두 동기화된 경우에도 버튼은 보이고 클릭 후 `이미 동기화됨`을 표시합니다. `available_to_sync_count` 추가는 handoff가 Axis 3 범위로 명시해 이번 라운드에서는 하지 않았습니다.
- Preference candidate 생성만 연결했으며, preference 활성화나 승인 저장 흐름은 변경하지 않았습니다.
- 작업 시작 전부터 dirty였던 `app/handlers/preferences.py`, `app/web.py`, `docs/MILESTONES.md`, `tests/test_preference_handler.py`, 기존 `report/`, `verify/`, `/work` untracked 파일들은 이번 Axis 2 범위 밖이라 변경하지 않았습니다.
- commit, push, branch/PR publish, next-slice 선택, `.pipeline/advisory_request.md`, `.pipeline/operator_request.md` 작성은 수행하지 않았습니다.
