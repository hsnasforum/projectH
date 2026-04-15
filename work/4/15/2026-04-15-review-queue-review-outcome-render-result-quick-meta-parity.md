# 검토 후보 review-outcome render-result quick-meta parity

## 변경 파일

- `app/static/app.js`

## 사용 skill

- 없음

## 변경 이유

이전 quick-meta parity 라운드가 `renderSession()` 경로의 correction-target review-outcome supplement를 구현했으나, `renderResult()`는 `renderSession()` 호출 후 `renderResponseSummary(data.response, ...)` 로 quick-meta를 덮어써서 새로운 streamed response가 오면 review-outcome label이 사라지는 gap이 있었습니다. 이 라운드는 공유 헬퍼 추출로 두 render 경로의 parity를 닫습니다.

## 핵심 변경

1. **`supplementQuickMetaReviewOutcome(responseMessage, correctionTargetMessage)`**: inline 조건을 공유 헬퍼로 추출. `correctionTargetMessage`에 `candidate_review_record`가 있고 `responseMessage`에는 없는 경우 quick-meta에 review-outcome label 추가.
2. **`renderSession()`**: 기존 inline 코드를 `supplementQuickMetaReviewOutcome()` 호출로 교체.
3. **`renderResult()`**: `renderResponseSummary()` 뒤에 같은 `supplementQuickMetaReviewOutcome()` 호출 추가.

## 검증

- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "candidate confirmation path는 save support와 분리되어 기록되고 later correction으로 current state에서 사라집니다" --reporter=line` → 1 passed
- `git diff --check` → clean

## 남은 리스크

- e2e 시나리오에서 review accept 후 새 streamed response를 트리거하는 별도 assertion은 추가하지 않았습니다. 현재 시나리오는 mutation rerender 경로만 커버하며, renderResult 경로는 코드 레벨 parity로 보장합니다.
