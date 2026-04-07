# entity-card crimson-desert natural-reload actual-search second-follow-up browser-anchor naming clarification

날짜: 2026-04-07

## 변경 파일
- `e2e/tests/web-smoke.spec.mjs`

## 사용 skill
- 없음 (test-only naming clarification)

## 변경 이유
- second-follow-up browser anchor title이 response-origin 중심 naming만 노출하고 있었으나, test body는 이미 `namu.wiki`, `ko.wikipedia.org` context box source-path continuity까지 검증합니다.
- root docs와 service anchor는 source-path + response-origin continuity를 함께 명시합니다.

## 핵심 변경
- test title: `response origin badge와 answer-mode badge가 drift하지 않습니다` → `source path가 context box에 유지되고 response origin badge와 answer-mode badge가 drift하지 않습니다`
- session ID: `entity-actual-search-natural-reload-second-followup-origin` → `entity-actual-search-natural-reload-second-followup-sp-origin`
- assertion logic 변경 없음, scenario count 75 유지

## 검증
- `npx playwright test -g "entity-card 붉은사막 actual-search 자연어 reload 후 두 번째 follow-up"`: 1 passed
- `git diff --check`: clean

## 남은 리스크
- second-follow-up fixture body의 `설명형 다중 출처 합의` 정렬 여부 확인 필요 (이번 범위 밖)
