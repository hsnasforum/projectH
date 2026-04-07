# entity-card crimson-desert natural-reload exact-field browser-anchor noisy-exclusion provenance wording clarification

날짜: 2026-04-07

## 변경 파일
- `e2e/tests/web-smoke.spec.mjs`

## 사용 skill
- 없음 (test-only wording clarification)

## 변경 이유
- entity-card 붉은사막 natural-reload initial exact-field browser anchor title이 generic `response origin badge와 answer-mode badge가 유지됩니다` 수준이어서, 이미 검사 중인 `출시일`/`2025`/`blog.example.com` negative-assertion, `설명형 다중 출처 합의`, `백과 기반`, `namu.wiki`/`ko.wikipedia.org`/`blog.example.com` provenance contract가 title에서 드러나지 않았습니다.

## 핵심 변경
- test title에 `noisy single-source claim(출시일/2025/blog.example.com) 미노출, 설명형 다중 출처 합의, 백과 기반 유지, namu.wiki/ko.wikipedia.org/blog.example.com provenance 유지됩니다` 추가
- session ID에 `-prov` suffix 추가
- assertion logic 변경 없음, scenario count 75 유지

## 검증
- `npx playwright test -g "entity-card 붉은사막 검색 결과 자연어 reload"`: 1 passed
- `git diff --check`: clean

## 남은 리스크
- source-path-only anchor (`e2e/tests/web-smoke.spec.mjs:4314`)의 wording clarification은 이번 범위 밖
