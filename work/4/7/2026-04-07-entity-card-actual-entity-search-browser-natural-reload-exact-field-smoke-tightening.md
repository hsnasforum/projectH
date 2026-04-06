# entity-card actual-entity-search browser natural-reload exact-field smoke tightening

날짜: 2026-04-07

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs` — entity-card 붉은사막 검색 결과 browser natural-reload exact-field scenario 1건 추가 (scenario 40)
- `README.md` — scenario 40 추가
- `docs/ACCEPTANCE_CRITERIA.md` — actual entity-search natural-reload criteria 추가
- `docs/MILESTONES.md` — actual entity-search natural-reload smoke milestone 항목 추가
- `docs/TASK_BACKLOG.md` — backlog item 46 추가
- `docs/NEXT_STEPS.md` — scenario count 39→40 갱신, actual entity-search natural-reload 설명 삽입

## 사용 skill

- 없음

## 변경 이유

- zero-strong-slot entity-card의 natural-reload는 scenario 38/39에서 잠갔지만, generic entity-card (strong slot 있는 붉은사막 fixture)의 natural-reload browser exact-field는 미검증
- service test `tests/test_web_app.py:8746-8803`이 actual entity-search natural-reload exact-field를 이미 잠그고 있으므로 browser contract만 추가

## 핵심 변경

- pre-seeded record: 붉은사막 entity_card with strong claim coverage (`교차 확인 1건`)
- Step 1: click reload로 서버 세션에 record 등록
- Step 2: `sendRequest({user_text: "방금 검색한 결과 다시 보여줘"})` 자연어 reload
- Assert: `#response-origin-badge` = "WEB" + `.web`, `#response-answer-mode-badge` = "설명 카드", `#response-origin-detail`에 "설명형 단일 출처", "백과 기반" 포함

## 검증

- `git diff --check` — 통과
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "entity-card 붉은사막 검색 결과 자연어 reload에서 response origin badge와 answer-mode badge가 유지됩니다" --reporter=line` — 1 passed (6.7s)
- `make e2e-test` — 생략 (shared browser helper 미변경)

## 남은 리스크

- full suite 미실행으로 broader regression 가능성 잔존하나, isolated rerun에서 drift 신호 없음
- browser mock 환경에서는 실제 web search tool call이 불가능하므로, pre-seeded record + click register + natural reload text 패턴을 사용 — service test가 actual search path를 별도로 커버
