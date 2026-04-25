# 2026-04-25 M36 preference pause persistence E2E

## 변경 파일
- `e2e/tests/web-smoke.spec.mjs`
- `work/4/25/2026-04-25-m36-preference-pause-persistence-e2e.md`

## 사용 skill
- `e2e-smoke-triage`: 기존 badge-popover-pause smoke 시나리오에 reload 후 count 유지 assertion을 추가하고 isolated rerun으로 확인했습니다.
- `work-log-closeout`: 변경 파일, 실행한 검증, 남은 리스크를 `/work` closeout으로 기록했습니다.

## 변경 이유
- `CONTROL_SEQ: 195` handoff에 따라 preference pause가 페이지 새로고침 이후에도 유지되어 다음 mock chat 응답의 applied preference count가 `N-1`로 남는지 확인해야 했습니다.

## 핵심 변경
- 기존 `"reviewed-memory loop: badge 클릭 시 popover가 열리고 선호를 일시중지할 수 있습니다"` 시나리오만 확장했습니다.
- Axis 1에서 계산한 `badgeCountBefore`를 재사용했습니다.
- `badgeCountBefore >= 2`일 때 `page.reload({ waitUntil: "domcontentloaded" })` 후 세 번째 메시지를 전송합니다.
- reload 후 새 응답에서도 `선호 ${badgeCountBefore - 1}건 반영` badge가 보이는지 확인합니다.
- `MessageBubble.tsx`, backend 파일, resume/reject 체크, 새 시나리오는 수정하지 않았습니다.

## 검증
- `node --check e2e/tests/web-smoke.spec.mjs`
  - 통과, 출력 없음.
- `cd /home/xpdlqj/code/projectH/e2e && npx playwright test tests/web-smoke.spec.mjs -g "badge 클릭" --reporter=line`
  - 통과.
  - `1 passed (11.3s)`

## 남은 리스크
- 전체 Playwright smoke 및 `make e2e-test`는 실행하지 않았습니다. handoff가 isolated `"badge 클릭"` 시나리오만 지정했고, 전체 suite 재실행을 금지했기 때문입니다.
- `badgeCountBefore < 2` edge case는 handoff 지시대로 reload persistence assertion을 건너뜁니다.
- 작업 전부터 있던 `verify/4/25/2026-04-25-m36-preference-pause-functional-e2e.md` 변경은 이번 implement handoff 범위 밖이라 건드리지 않았습니다.
- commit, push, branch/PR 생성, 다음 slice 선택은 수행하지 않았습니다.
