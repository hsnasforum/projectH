# 2026-04-26 M37 preference count-agnostic E2E

## 변경 파일
- `e2e/tests/web-smoke.spec.mjs`
- `work/4/26/2026-04-26-m37-preference-count-agnostic-e2e.md`

## 사용 skill
- `e2e-smoke-triage`: 실패했던 Playwright smoke 147/148의 count 및 cap 조건을 isolated scenario부터 확인했습니다.
- `finalize-lite`: 실행한 검증, doc-sync 필요 여부, 남은 리스크를 구현 closeout 전에 정리했습니다.
- `work-log-closeout`: 실제 변경 파일과 검증 결과를 `/work` closeout으로 기록했습니다.

## 변경 이유
- `CONTROL_SEQ: 213` handoff에 따라 scenario 147의 hardcoded `선호 1건 반영` 단언을 누적 active preference 수에 독립적인 단언으로 바꿔야 했습니다.
- scenario 148은 누적 active Playwright preference가 cap(10)을 채우면 새 test preference pause가 visible count에 반영되지 않아 실패하므로, test 시작 전 기존 Playwright active preference를 pause해야 했습니다.

## 핵심 변경
- scenario 147의 mock response 단언을 `[모의 응답, 선호` prefix와 `/선호 \d+건 반영/` badge text 패턴으로 교체했습니다.
- scenario 148에서 candidate preference 확인 직후, `pw-` description 또는 `source_corrections[].session_id`가 `pw-`로 시작하는 기존 active preference만 pause하는 cleanup을 추가했습니다.
- cleanup은 현재 테스트가 만든 `preference.preference_id`를 제외해서 test target은 유지합니다.
- `app/`, `storage/`, frontend 컴포넌트, scenario 149는 수정하지 않았습니다.

## 검증
- `git diff --check -- e2e/tests/web-smoke.spec.mjs`
  - 통과, 출력 없음.
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "sync 후 활성화" --reporter=line`
  - 통과.
  - `1 passed (17.7s)`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "badge 클릭 시 popover" --reporter=line`
  - 통과.
  - `1 passed (30.0s)`
- `make e2e-test`
  - 통과.
  - `149 passed (13.5m)`

## 남은 리스크
- full E2E 중 PDF fixture에서 기존 `incorrect startxref pointer(3)` 경고가 출력됐지만 관련 PDF scenarios는 통과했습니다.
- 작업 전부터 있던 `verify/4/25/2026-04-25-m36-preference-pause-functional-e2e.md` 변경, `verify/4/25/2026-04-25-m37-preference-resume-reject-e2e.md` 미추적 파일, `report/gemini/**` 미추적 파일, `work/4/25/**` 미추적 파일들은 이번 handoff 범위 밖이라 건드리지 않았습니다.
- commit, push, branch/PR 생성, 다음 slice 선택은 수행하지 않았습니다.
