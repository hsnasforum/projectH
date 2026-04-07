# entity-card crimson-desert natural-reload follow-up/second-follow-up noisy-exclusion browser-anchor continuity wording clarification

날짜: 2026-04-07

## 변경 파일
- `e2e/tests/web-smoke.spec.mjs`

## 사용 skill
- 없음 (test-only wording clarification)

## 변경 이유
- crimson-specific noisy-exclusion follow-up/second-follow-up browser anchor titles가 `blog.example.com provenance와 continuity가 유지됩니다` 수준이어서, 이미 검사 중인 `설명형 다중 출처 합의`, `백과 기반`, `namu.wiki`/`ko.wikipedia.org` continuity가 title에서 드러나지 않았습니다.

## 핵심 변경
- 2개 test title의 continuity 부분을 `설명형 다중 출처 합의, 백과 기반, namu.wiki/ko.wikipedia.org/blog.example.com provenance continuity가 유지됩니다`로 확장
- session ID 변경 없음, assertion logic 변경 없음, scenario count 75 유지

## 검증
- `npx playwright test -g "noisy single-source claim"`: 2 passed
- `git diff --check`: clean

## 남은 리스크
- 붉은사막 natural-reload family 전체 browser anchor wording clarification 완료 (exact-field, source-path, actual-search follow-up/second-follow-up, noisy-exclusion follow-up/second-follow-up)
