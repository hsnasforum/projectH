# 검토 후보 source-message review-outcome visibility

## 변경 파일

- `app/static/app.js`
- `e2e/tests/web-smoke.spec.mjs`
- `README.md`
- `docs/PRODUCT_SPEC.md`
- `docs/ACCEPTANCE_CRITERIA.md`

## 사용 skill

- 없음

## 변경 이유

docs-only review-queue action-vocabulary family가 이전 3회 라운드로 닫혔으며, 이 라운드는 다음으로 가장 작은 same-family user-visible gap으로 이동합니다: 검토 결과 기록 후 queue item이 사라지면 사용자가 해당 source message의 review outcome을 persistent하게 볼 수 없었습니다.

## 핵심 변경

1. **`app/static/app.js`**: `formatReviewOutcomeLabel(reviewAction)` 함수 추가 (`accept → 검토 수락됨`, `reject → 검토 거절됨`, `defer → 검토 보류됨`). transcript `renderTranscript` metaLines와 `renderResponseSummary` quick meta parts 양쪽에 `candidate_review_record.review_action` 기반 label 표시.
2. **`e2e/tests/web-smoke.spec.mjs`**: candidate confirmation path 시나리오에 review accept 후 transcript-meta "검토 수락됨" 존재 검증 추가. later correction 후 transcript-meta "검토 수락됨" 소멸(stale-clear) 검증 추가.
3. **docs**: `README.md`, `docs/PRODUCT_SPEC.md`, `docs/ACCEPTANCE_CRITERIA.md`에 persistent review-outcome visibility 서술 추가.

## 검증

- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "candidate confirmation path는 save support와 분리되어 기록되고 later correction으로 current state에서 사라집니다" --reporter=line` → 1 passed
- `git diff --check` → clean
- Python 테스트 재실행 없음 — JS-only 변경이며 serializer/handler 무변경

## 남은 리스크

- quick meta는 latest assistant message만 보여주므로, 검토된 source message가 latest가 아닌 경우(예: 이후 save confirmation이 latest인 경우) quick meta에는 review outcome이 나타나지 않습니다. transcript meta에서는 항상 해당 source message 카드에 표시됩니다.
- `reject`/`defer` 결과에 대한 aggregate 제외 논리는 아직 미구현입니다.
