# 2026-04-25 M35 applied preference details edit

## 변경 파일
- `app/frontend/src/components/MessageBubble.tsx`
- `e2e/tests/web-smoke.spec.mjs`
- `app/static/dist/assets/index.css`
- `app/static/dist/assets/index.js`
- `work/4/25/2026-04-25-m35-applied-preference-details-edit.md`

## 사용 skill
- `security-gate`: 기존 `fetchPreferences`, `pausePreference`, `updatePreferenceDescription` API를 호출하는 write-capable preference UI 변경이라서 local-first/저장 경계를 확인했습니다.
- `e2e-smoke-triage`: badge popover browser flow가 바뀌어 기존 `"badge 클릭"` smoke 시나리오를 확장하고 isolated rerun으로 확인했습니다.
- `work-log-closeout`: 변경 파일, 실제 검증 결과, 남은 리스크를 `/work` closeout으로 기록했습니다.

## 변경 이유
- `CONTROL_SEQ: 185` handoff에 따라 applied-preferences popover가 전체 preference record를 가져와 snippet을 보여주고, description inline edit 진입점을 제공해야 했습니다.

## 핵심 변경
- `MessageBubble.tsx`에서 `PreferenceRecord`와 `updatePreferenceDescription`을 사용하도록 import를 확장했습니다.
- popover open 시 `/api/preferences` 목록을 가져와 `delta_fingerprint`로 applied preference와 full preference record를 매칭합니다.
- popover 항목에 description inline edit 상태, 입력 필드, 저장/취소 버튼을 추가했습니다.
- `original_snippet`, `corrected_snippet`이 있는 preference는 popover 안에 각각 `pref-original-snippet`, `pref-corrected-snippet`으로 표시합니다.
- 기존 pause 동작은 유지했고, description 저장은 기존 `updatePreferenceDescription(preference_id, description)` API를 사용합니다.
- 기존 `"badge 클릭"` smoke 시나리오에 `pref-description-edit` 버튼 visible 확인을 추가했습니다.
- frontend build로 `app/static/dist/assets/index.css`, `app/static/dist/assets/index.js`를 갱신했습니다.

## 검증
- `node --check e2e/tests/web-smoke.spec.mjs`
  - 통과, 출력 없음.
- `cd app/frontend && npx vite build 2>&1 | tail -3`
  - 통과.
  - `../static/dist/assets/index.css   31.40 kB │ gzip:  6.37 kB`
  - `../static/dist/assets/index.js   303.63 kB │ gzip: 91.52 kB`
  - `✓ built in 4.94s`
- `cd /home/xpdlqj/code/projectH/e2e && npx playwright test tests/web-smoke.spec.mjs -g "badge 클릭" --reporter=line`
  - 통과.
  - `1 passed (8.6s)`

## 남은 리스크
- 전체 Playwright smoke 및 `make e2e-test`는 실행하지 않았습니다. handoff가 isolated `"badge 클릭"` 시나리오만 지정했고, 전체 suite 재실행을 금지했기 때문입니다.
- smoke는 edit 버튼의 존재만 확인합니다. 실제 description 저장 round-trip은 UI 구현에 연결돼 있지만, 이번 handoff 범위에서는 별도 E2E 저장 assertion을 추가하지 않았습니다.
- backend, storage, approval flow는 수정하지 않았습니다. write 동작은 기존 local preference update API 경계 안에 머뭅니다.
