# 검토 후보 review-outcome quick-meta browser parity

## 변경 파일

- `app/static/app.js`
- `e2e/tests/web-smoke.spec.mjs`

## 사용 skill

- 없음

## 변경 이유

docs-only 잔여 truth-sync가 이전 라운드로 닫혔으며, 이 라운드는 이미 shipped된 review-outcome quick-meta 경로의 browser parity를 좁힙니다. 기존 `renderResponseSummary`는 latest assistant message만 보고 review-outcome label을 추가했으나, 검토된 source message가 latest가 아닌 경우(예: save confirmation이 latest인 경우) quick-meta에 review outcome이 나타나지 않았습니다.

## 핵심 변경

1. **`app/static/app.js`**: `renderSession` 내 `renderResponseSummary()` 호출 후, `correctionTargetMessage`에 `candidate_review_record`가 있고 `latestAssistantMessage`에는 없는 경우 quick-meta에 review-outcome label을 추가하는 보조 로직 삽입. `correctionTargetMessage`가 latest와 같은 경우 기존 `renderResponseSummary` 내부 경로로 처리되므로 중복 없음.
2. **`e2e/tests/web-smoke.spec.mjs`**: candidate confirmation path 시나리오에 review accept 후 `#response-quick-meta-text`에 "검토 수락됨" 존재 검증 추가. Later correction 후 quick-meta에서 "검토 수락됨" 소멸(stale-clear) 검증 추가.

## 검증

- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "candidate confirmation path는 save support와 분리되어 기록되고 later correction으로 current state에서 사라집니다" --reporter=line` → 1 passed
- `git diff --check` → clean

## 남은 리스크

- `reject`/`defer` browser coverage는 이 라운드 범위 밖입니다. 현재 `formatReviewOutcomeLabel`은 세 action 모두 처리하므로 코드 경로는 준비되어 있습니다.
