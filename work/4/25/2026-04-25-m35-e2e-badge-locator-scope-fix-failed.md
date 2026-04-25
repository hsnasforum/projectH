# 2026-04-25 M35 E2E badge locator scope fix 실패 기록

## 변경 파일
- `e2e/tests/web-smoke.spec.mjs`
- `work/4/25/2026-04-25-m35-e2e-badge-locator-scope-fix-failed.md`

## 사용 skill
- `e2e-smoke-triage`: 이전 Playwright 실패 시나리오의 selector 범위를 좁히고 isolated smoke만 재실행했습니다.
- `work-log-closeout`: handoff 범위 변경, 실제 검증 결과, 남은 리스크를 `/work` closeout으로 기록했습니다.

## 변경 이유
- `CONTROL_SEQ: 180` handoff에 따라 badge-popover-pause 시나리오가 이전 테스트 세션의 badge를 클릭하지 않도록 badge, popover, pause 버튼 로케이터를 `main` 범위로 제한해야 했습니다.

## 핵심 변경
- `"reviewed-memory loop: badge 클릭 시 popover가 열리고 선호를 일시중지할 수 있습니다"` 시나리오의 badge 로케이터를 `page.locator("main").getByTestId("applied-preferences-badge").first()`로 변경했습니다.
- 같은 시나리오의 popover 로케이터를 `page.locator("main").getByTestId("applied-preferences-popover")`로 변경했습니다.
- pause 버튼 클릭도 `page.locator("main").getByTestId("preference-pause-btn").first()`로 제한했습니다.
- setup, 채팅 전송, preference status 확인 로직은 변경하지 않았습니다.
- `MessageBubble.tsx`, `app/static/dist/`, backend 파일은 이번 handoff에서 수정하지 않았습니다.

## 검증
- `node --check e2e/tests/web-smoke.spec.mjs`
  - 통과, 출력 없음.
- `cd /home/xpdlqj/code/projectH/e2e && npx playwright test tests/web-smoke.spec.mjs -g "badge 클릭" --reporter=line`
  - 실패.
  - 실패 시나리오: `reviewed-memory loop: badge 클릭 시 popover가 열리고 선호를 일시중지할 수 있습니다`
  - 실패 위치: `e2e/tests/web-smoke.spec.mjs:12175`
  - 실패 내용: `locator('main').getByTestId('applied-preferences-popover').getByText(preferenceStatement)` 요소를 찾지 못해 `toBeVisible()` 실패.
  - artifact: `e2e/test-results/web-smoke-reviewed-memory--4968a-pover가-열리고-선호를-일시중지할-수-있습니다/trace.zip`

## 미실행 검증
- 전체 Playwright smoke 및 `make e2e-test`는 실행하지 않았습니다. handoff가 isolated `"badge 클릭"` 실패 시 실패 메시지를 기록하고 STOP하라고 지정했기 때문입니다.

## 남은 리스크
- `main` 범위 제한 후에도 popover 안에서 현재 테스트의 `preferenceStatement` 텍스트를 찾지 못했습니다.
- 실패 원인 추가 조사는 수행하지 않았습니다. handoff의 실패 시 STOP 지시에 따라 추가 수정, 다음 slice 선택, advisory/operator slot 작성 없이 중단합니다.
- 작업 전부터 남아 있던 `MessageBubble.tsx`, `app/static/dist/assets/index.css`, `app/static/dist/assets/index.js` 변경은 이전 `CONTROL_SEQ: 179` 결과이며 이번 handoff에서는 건드리지 않았습니다.
