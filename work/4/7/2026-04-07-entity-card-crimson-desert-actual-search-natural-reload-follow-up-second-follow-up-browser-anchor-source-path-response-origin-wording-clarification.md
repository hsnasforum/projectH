# entity-card crimson-desert actual-search natural-reload follow-up/second-follow-up browser-anchor source-path-response-origin wording clarification

날짜: 2026-04-07

## 변경 파일
- `e2e/tests/web-smoke.spec.mjs`

## 사용 skill
- 없음 (test-only wording clarification)

## 변경 이유
- actual-search follow-up/second-follow-up browser anchor titles가 generic `source path가 context box에 유지됩니다` / `response origin badge와 answer-mode badge가 drift하지 않습니다` 수준이어서, 이미 검사 중인 `namu.wiki`/`ko.wikipedia.org` source-path plurality와 `WEB`/`설명 카드`/`설명형 다중 출처 합의`/`백과 기반` response-origin contract가 title에서 드러나지 않았습니다.

## 핵심 변경
- follow-up source-path (4870): `(namu.wiki, ko.wikipedia.org)` 추가
- follow-up response-origin (4990): `WEB badge, 설명 카드, 설명형 다중 출처 합의, 백과 기반` 명시
- second-follow-up (5045): `(namu.wiki, ko.wikipedia.org)` + `WEB badge, 설명 카드, 설명형 다중 출처 합의, 백과 기반` 명시
- session ID 변경 없음, assertion logic 변경 없음, scenario count 75 유지

## 검증
- `npx playwright test -g "entity-card 붉은사막 actual-search 자연어 reload 후"`: 3 passed
- `git diff --check`: clean

## 남은 리스크
- 붉은사막 natural-reload family browser anchor wording clarification 전체 완료
