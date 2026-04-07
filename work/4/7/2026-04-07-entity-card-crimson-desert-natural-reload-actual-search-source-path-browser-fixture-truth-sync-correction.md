# entity-card crimson-desert natural-reload actual-search source-path browser fixture truth-sync correction

날짜: 2026-04-07

## 변경 파일
- `e2e/tests/web-smoke.spec.mjs`

## 사용 skill
- 없음 (test-only fixture correction)

## 변경 이유
- crimson natural-reload follow-up source-path browser anchor의 fixture body가 `설명형 단일 출처` (single-source wording)를 유지하고 있어, actual-search multi-source agreement truth (`설명형 다중 출처 합의`)와 불일치했습니다.
- paired service anchors와 initial natural-reload exact-field browser anchor는 이미 `설명형 다중 출처 합의`를 사용합니다.

## 핵심 변경
- fixture comment: `single source` → `multi-source agreement`
- seeded `verification_label`: `설명형 단일 출처` → `설명형 다중 출처 합의` (record body + history metadata 둘 다)
- assertion logic 변경 없음, scenario count 75 유지

## 검증
- `npx playwright test -g "entity-card 붉은사막 actual-search 자연어 reload 후 follow-up에서 source path가 context box에 유지됩니다"`: 1 passed
- `git diff --check`: clean

## 남은 리스크
- response-origin/second-follow-up browser anchors의 fixture에도 동일 `설명형 단일 출처` → `설명형 다중 출처 합의` 정렬이 필요할 수 있음 (이번 범위 밖)
