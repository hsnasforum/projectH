# 2026-04-25 M36 preference pause functional E2E

## 변경 파일
- `e2e/tests/web-smoke.spec.mjs`
- `work/4/25/2026-04-25-m36-preference-pause-functional-e2e.md`

## 사용 skill
- `e2e-smoke-triage`: 기존 badge-popover-pause smoke 시나리오에 pause 후 기능 효과 assertion을 추가하고 isolated rerun으로 확인했습니다.
- `work-log-closeout`: 변경 파일, 실행한 검증, 남은 리스크를 `/work` closeout으로 기록했습니다.

## 변경 이유
- `CONTROL_SEQ: 192` handoff에 따라 preference pause가 API 상태 변경에서 끝나지 않고 다음 mock chat 응답의 applied preference count를 줄이는지 확인해야 했습니다.

## 핵심 변경
- 기존 `"reviewed-memory loop: badge 클릭 시 popover가 열리고 선호를 일시중지할 수 있습니다"` 시나리오만 확장했습니다.
- pause 전 badge 텍스트에서 `선호 N건` count를 파싱합니다.
- pause 상태 확인 후 두 번째 메시지를 전송합니다.
- pause 전 count가 1 이하이면 응답 도착만 fallback으로 확인하고, count가 2 이상이면 새 응답 badge가 `N-1건`으로 줄었는지 확인합니다.
- `MessageBubble.tsx`, backend 파일, 새 시나리오는 수정하지 않았습니다.

## 검증
- `node --check e2e/tests/web-smoke.spec.mjs`
  - 통과, 출력 없음.
- `cd /home/xpdlqj/code/projectH/e2e && npx playwright test tests/web-smoke.spec.mjs -g "badge 클릭" --reporter=line`
  - 통과.
  - `1 passed (7.3s)`

## 남은 리스크
- 전체 Playwright smoke 및 `make e2e-test`는 실행하지 않았습니다. handoff가 isolated `"badge 클릭"` 시나리오만 지정했고, 전체 suite 재실행을 금지했기 때문입니다.
- `badgeCountBefore <= 1` 분기는 handoff 제공 fallback을 그대로 사용해 응답 도착 확인 중심입니다. 현재 isolated 실행에서는 전체 시나리오가 통과했습니다.
- commit, push, branch/PR 생성, 다음 slice 선택은 수행하지 않았습니다.
