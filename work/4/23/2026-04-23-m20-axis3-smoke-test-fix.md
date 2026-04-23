# 2026-04-23 M20 Axis 3 smoke test fix

## 변경 파일
- `e2e/tests/web-smoke.spec.mjs`
- `work/4/23/2026-04-23-m20-axis3-smoke-test-fix.md`

## 사용 skill
- `e2e-smoke-triage`: global candidate가 review queue에 섞여 session-local smoke assertion을 오염시키는 실패 경로를 좁게 분리했습니다.
- `finalize-lite`: handoff acceptance check와 전체 `make e2e-test` 결과만 통과로 기록했습니다.
- `work-log-closeout`: 실제 변경 파일, 실행 검증, 남은 리스크를 `/work` 형식으로 기록했습니다.

## 변경 이유
- implement handoff seq 84 기준 M20 Axis 3 full smoke gate에서 실패한 6개 E2E smoke를 복구하기 위해서입니다.
- M18 Axis 3 이후 `_build_review_queue_items()`가 global candidates를 포함하면서, 테스트 간 같은 `(fixture, correctedText)` fingerprint 또는 의도적 aggregate recurrence가 뒤쪽 review queue assertion을 오염시켰습니다.

## 핵심 변경
- `corrected-long-history` 테스트의 `correctedTextA/B`를 `corrected-save`와 다른 값으로 바꿔 cross-session fingerprint collision을 피했습니다.
- 해당 corrected text는 다른 테스트와 중복되면 global candidate를 만들 수 있다는 주석을 추가했습니다.
- `sessionLocalReviewQueueItems()`, `expectSessionLocalReviewQueueCount()`, `sessionLocalReviewQueueItem()` helper를 추가해 session-local review queue contract를 global candidate와 분리했습니다.
- candidate confirmation, reject/defer, edit, aggregate lifecycle smoke에서 session-local item만 검증하거나 조작하도록 변경했습니다.
- review queue panel/edit smoke의 accept 후 empty assertion은 `is_global !== true` 항목만 0인지 확인하도록 변경했습니다.
- backend/frontend 제품 코드는 변경하지 않았고, aggregate test의 의도적 recurring corrected text도 변경하지 않았습니다.

## 검증
- `git diff --check -- e2e/tests/web-smoke.spec.mjs`
  - 통과: 출력 없음
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "candidate confirmation path" --reporter=line`
  - 1차 실행 실패: `review-queue-box`가 global candidate 때문에 visible
  - session-local queue helper 보정 후 재실행 통과: `1 passed (14.1s)`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "review-queue reject/defer" --reporter=line`
  - 통과: `1 passed (14.2s)`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "편집은 review_action" --reporter=line`
  - 통과: `1 passed (7.8s)`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "same-session recurrence aggregate는 emitted" --reporter=line`
  - 통과: `1 passed (15.7s)`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "review queue panel opens on badge click" --reporter=line`
  - 통과: `1 passed (6.1s)`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "review queue edit statement sends edited text" --reporter=line`
  - 통과: `1 passed (6.2s)`
- `make e2e-test`
  - 통과: `142 passed (6.8m)`
- `git diff --check`
  - 통과: 출력 없음

## 남은 리스크
- 앞으로 새 smoke가 같은 `(fixture, correctedText)` 조합을 여러 session에서 재사용하면 global candidate 오염이 다시 생길 수 있습니다. 이번 round는 convention comment와 session-local helper로 현재 실패군을 줄였습니다.
- global candidate UI 자체의 별도 격리/cleanup 정책은 이번 handoff 범위가 아니어서 추가하지 않았습니다.
- 기존 미추적 파일 `report/gemini/2026-04-23-m20-closure-consolidation.md`는 이번 implement round에서 건드리지 않았습니다.
