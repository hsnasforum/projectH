# 2026-04-25 M35 applied preference badge popover 실패 기록

## 변경 파일
- `app/frontend/src/components/MessageBubble.tsx`
- `e2e/tests/web-smoke.spec.mjs`
- `app/static/dist/assets/index.css`
- `app/static/dist/assets/index.js`
- `work/4/25/2026-04-25-m35-applied-preference-badge-popover-failed.md`

## 사용 skill
- `security-gate`: 적용된 선호를 UI에서 일시중지하는 저장 상태 변경 경로라서 승인/저장 경계를 확인했습니다.
- `e2e-smoke-triage`: Playwright smoke 시나리오를 추가하고 실패 시 handoff 지시에 따라 자체 수정 없이 실패 기록으로 중단했습니다.
- `work-log-closeout`: 구현 변경, 실제 검증 결과, 남은 리스크를 `/work` closeout으로 기록했습니다.

## 변경 이유
- `CONTROL_SEQ: 179` handoff에 따라 assistant 메시지의 `applied-preferences-badge`를 클릭 가능한 button으로 바꾸고, popover에서 적용된 선호를 일시중지할 수 있는 UI 경로를 추가해야 했습니다.

## 핵심 변경
- `MessageBubble.tsx`에서 `applied-preferences-badge`를 기존 tooltip span에서 interactive button으로 변경했습니다.
- badge 옆 popover를 추가해 적용된 선호 설명 목록과 `preference-pause-btn` 버튼을 렌더링합니다.
- 외부 클릭 시 popover가 닫히도록 `useEffect`와 wrapper ref를 추가했습니다.
- popover pause 동작은 현재 메시지에 내려오는 `fingerprint`로 `/api/preferences` 목록에서 실제 `preference_id`를 찾아 기존 `pausePreference(preferenceId)` API를 호출합니다. 매칭 실패 시에는 fingerprint를 fallback으로 사용합니다.
- `e2e/tests/web-smoke.spec.mjs`에 `"reviewed-memory loop: badge 클릭 시 popover가 열리고 선호를 일시중지할 수 있습니다"` 시나리오를 추가했습니다.
- `npx vite build`로 정적 번들 `index.js`, `index.css`를 갱신했습니다.

## 검증
- `python3 -m py_compile app/frontend/src/components/MessageBubble.tsx 2>/dev/null || node --check e2e/tests/web-smoke.spec.mjs`
  - 통과, 출력 없음.
- `cd app/frontend && npx vite build 2>&1 | tail -3`
  - 통과.
  - `../static/dist/assets/index.css   30.95 kB │ gzip:  6.30 kB`
  - `../static/dist/assets/index.js   301.63 kB │ gzip: 91.03 kB`
  - `✓ built in 1.51s`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "badge 클릭" --reporter=line`
  - 실패.
  - 실패 시나리오: `reviewed-memory loop: badge 클릭 시 popover가 열리고 선호를 일시중지할 수 있습니다`
  - 실패 위치: `e2e/tests/web-smoke.spec.mjs:12175`
  - 실패 내용: `getByTestId('applied-preferences-popover').getByText(preferenceStatement)` 요소를 찾지 못해 `toBeVisible()` 실패.
  - artifact: `e2e/test-results/web-smoke-reviewed-memory--4968a-pover가-열리고-선호를-일시중지할-수-있습니다/trace.zip`

## 미실행 검증
- 전체 Playwright smoke 및 `make e2e-test`는 실행하지 않았습니다. handoff가 새 E2E 실패 시 실패 시나리오를 기록하고 STOP하라고 지정했기 때문입니다.

## 남은 리스크
- popover 자체는 visible까지 도달했지만, 기대한 `preferenceStatement` 텍스트가 popover 안에서 확인되지 않아 pause 버튼 클릭과 최종 `status === "paused"` 검증까지 도달하지 못했습니다.
- 실패 원인은 추가 조사하지 않았습니다. handoff의 실패 시 STOP 지시에 따라 자체 수정 또는 다음 slice 선택 없이 중단합니다.
