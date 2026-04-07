# entity-card crimson-desert natural-reload actual-search browser-anchor naming clarification

날짜: 2026-04-07

## 변경 파일
- `e2e/tests/web-smoke.spec.mjs`

## 사용 skill
- 없음 (test-only naming clarification)

## 변경 이유
- crimson natural-reload follow-up/second-follow-up actual-search browser test titles가 generic `entity-card 붉은사막 자연어 reload 후 ...` wording이어서, service anchors (`test_handle_chat_actual_entity_search_...`)와 docs의 `actual-search` qualifier와 불일치했습니다.
- response-origin test의 session IDs도 `actual-search` spelling이 빠져 있었습니다.

## 핵심 변경
- 3개 test title에 `actual-search` qualifier 추가:
  - `e2e/tests/web-smoke.spec.mjs:4870` (follow-up source-path)
  - `e2e/tests/web-smoke.spec.mjs:4990` (follow-up response-origin)
  - `e2e/tests/web-smoke.spec.mjs:5045` (second-follow-up response-origin)
- 2개 session ID에 `actual-search` 추가:
  - `entity-actual-natural-reload-followup-origin` → `entity-actual-search-natural-reload-followup-origin`
  - `entity-actual-natural-reload-second-followup-origin` → `entity-actual-search-natural-reload-second-followup-origin`
- assertion logic, docs, scenario count 75 변경 없음

## 검증
- `npx playwright test -g "entity-card 붉은사막 actual-search 자연어 reload 후"`: 3 passed
- `git diff --check`: clean

## 남은 리스크
- 없음 (naming-only clarification, crimson natural-reload actual-search family 전체 정렬 완료)
