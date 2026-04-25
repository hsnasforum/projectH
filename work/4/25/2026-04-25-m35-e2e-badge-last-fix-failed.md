# 2026-04-25 M35 E2E badge last locator fix 실패 기록

## 변경 파일
- `e2e/tests/web-smoke.spec.mjs`
- `work/4/25/2026-04-25-m35-e2e-badge-last-fix-failed.md`

## 사용 skill
- `e2e-smoke-triage`: 실패한 Playwright smoke 시나리오의 badge/popover/pause selector만 좁게 수정하고 isolated 시나리오를 재실행했습니다.
- `work-log-closeout`: 실제 변경 범위, 실행한 검증, error-context 관찰 내용을 `/work` closeout으로 기록했습니다.

## 변경 이유
- `CONTROL_SEQ: 181` handoff에 따라 badge-popover-pause 시나리오에서 `.first()`가 이전 메시지 badge를 선택하는 문제를 피하려고, 가장 최근 메시지 쪽 로케이터를 선택하도록 `.last()`로 교체해야 했습니다.

## 핵심 변경
- `"reviewed-memory loop: badge 클릭 시 popover가 열리고 선호를 일시중지할 수 있습니다"` 시나리오의 badge 로케이터를 `.first()`에서 `.last()`로 변경했습니다.
- 같은 시나리오의 popover 로케이터를 `page.locator("main").getByTestId("applied-preferences-popover").last()`로 변경했습니다.
- pause 버튼 클릭도 `.first()`에서 `.last()`로 변경했습니다.
- setup, 채팅 전송, `preferenceStatement` assertion, 최종 preference status 확인 로직은 변경하지 않았습니다.
- `MessageBubble.tsx`, `app/static/dist/`, backend 파일은 이번 handoff에서 수정하지 않았습니다.

## 검증
- `node --check e2e/tests/web-smoke.spec.mjs`
  - 통과, 출력 없음.
- `cd /home/xpdlqj/code/projectH/e2e && npx playwright test tests/web-smoke.spec.mjs -g "badge 클릭" --reporter=line`
  - 실패.
  - 실패 시나리오: `reviewed-memory loop: badge 클릭 시 popover가 열리고 선호를 일시중지할 수 있습니다`
  - 실패 위치: `e2e/tests/web-smoke.spec.mjs:12175`
  - 실패 내용: `locator('main').getByTestId('applied-preferences-popover').last().getByText(preferenceStatement)` 요소를 찾지 못해 `toBeVisible()` 실패.
  - artifact: `e2e/test-results/web-smoke-reviewed-memory--4968a-pover가-열리고-선호를-일시중지할-수-있습니다/trace.zip`
  - error-context: `e2e/test-results/web-smoke-reviewed-memory--4968a-pover가-열리고-선호를-일시중지할-수-있습니다/error-context.md`

## error-context 관찰
- 사이드 패널에는 현재 테스트 preference인 `reviewed-memory badge pause accepted preference pw-reviewed-memory-badge-pause-moeajzrr-xrf79`가 후보 상태로 표시됐습니다.
- `main`에는 `[모의 응답, 선호 6건 반영]` 메시지의 badge가 expanded 상태였고, popover에는 이전 badge-pause preference들과 reviewed-memory loop preference들이 표시됐습니다.
- 같은 snapshot에 더 아래쪽 `[모의 응답, 선호 7건 반영]` 메시지와 `선호 7건 반영` badge가 존재했지만 expanded 상태는 아니었습니다.
- 따라서 `.last()` 교체 후에도 현재 assertion이 기대한 `preferenceStatement`는 열린 popover 안에서 확인되지 않았습니다.

## 미실행 검증
- 전체 Playwright smoke 및 `make e2e-test`는 실행하지 않았습니다. handoff가 isolated `"badge 클릭"` 실패 시 error-context 포함 실패 상세를 기록하고 STOP하라고 지정했기 때문입니다.

## 남은 리스크
- `.last()` 변경만으로는 시나리오가 통과하지 않았습니다.
- 실패 원인 추가 조사는 수행하지 않았습니다. handoff의 실패 시 STOP 지시에 따라 추가 수정, 다음 slice 선택, advisory/operator slot 작성 없이 중단합니다.
- 작업 전부터 남아 있던 `MessageBubble.tsx`, `app/static/dist/assets/index.css`, `app/static/dist/assets/index.js` 변경은 이전 `CONTROL_SEQ: 179` 결과이며 이번 handoff에서는 건드리지 않았습니다.
