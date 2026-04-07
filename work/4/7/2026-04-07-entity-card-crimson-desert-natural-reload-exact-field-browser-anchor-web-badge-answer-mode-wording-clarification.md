# entity-card crimson-desert natural-reload exact-field browser-anchor web-badge-answer-mode wording clarification

날짜: 2026-04-07

## 변경 파일
- `e2e/tests/web-smoke.spec.mjs`

## 사용 skill
- 없음 (test-only wording clarification)

## 변경 이유
- initial natural-reload exact-field browser anchor title이 noisy-exclusion, `설명형 다중 출처 합의`, `백과 기반`, provenance는 적고 있었으나, test body에서 이미 검사 중인 `WEB` badge와 `설명 카드` answer-mode가 title에서 드러나지 않았습니다.

## 핵심 변경
- test title에 `WEB badge, 설명 카드,` 추가 (기존 noisy-exclusion + provenance wording 유지)
- session ID 변경 없음, assertion logic 변경 없음, scenario count 75 유지

## 검증
- `npx playwright test -g "entity-card 붉은사막 검색 결과 자연어 reload"`: 1 passed
- `git diff --check`: clean

## 남은 리스크
- 붉은사막 natural-reload family 전체 browser anchor wording clarification 완료
