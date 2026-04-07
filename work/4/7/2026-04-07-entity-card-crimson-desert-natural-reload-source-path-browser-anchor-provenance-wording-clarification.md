# entity-card crimson-desert natural-reload source-path browser-anchor provenance wording clarification

날짜: 2026-04-07

## 변경 파일
- `e2e/tests/web-smoke.spec.mjs`

## 사용 skill
- 없음 (test-only wording clarification)

## 변경 이유
- entity-card 붉은사막 natural-reload source-path-only browser anchor title이 generic `source path가 context box에 유지됩니다` 수준이어서, 이미 검사 중인 `namu.wiki`, `ko.wikipedia.org`, `blog.example.com` provenance plurality가 title에서 드러나지 않았습니다.
- docs는 이 provenance plurality를 직접 명시합니다.

## 핵심 변경
- test title에 `(namu.wiki, ko.wikipedia.org, blog.example.com provenance)` 추가
- session ID에 `-prov` suffix 추가
- assertion logic 변경 없음, scenario count 75 유지

## 검증
- `npx playwright test -g "entity-card 붉은사막 자연어 reload에서 source path"`: 1 passed
- `git diff --check`: clean

## 남은 리스크
- 붉은사막 natural-reload family browser anchor wording clarification 전체 완료 (exact-field, source-path, actual-search follow-up/second-follow-up, noisy-exclusion follow-up/second-follow-up)
