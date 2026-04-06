# entity-card dual-probe browser natural-reload exact-field smoke tightening

날짜: 2026-04-07

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs` — entity-card dual-probe browser natural-reload exact-field scenario 1건 추가 (scenario 42)
- `README.md` — scenario 42 추가
- `docs/ACCEPTANCE_CRITERIA.md` — dual-probe natural-reload exact-field criteria 추가
- `docs/MILESTONES.md` — dual-probe natural-reload exact-field smoke milestone 항목 추가
- `docs/TASK_BACKLOG.md` — backlog item 48 추가
- `docs/NEXT_STEPS.md` — scenario count 41→42 갱신, dual-probe natural-reload exact-field 설명 삽입

## 사용 skill

- 없음

## 변경 이유

- scenario 41에서 dual-probe natural-reload source-path continuity를 잠갔지만, response-origin exact field (WEB badge, 설명 카드, 설명형 단일 출처, 백과 기반)는 미검증
- service test `tests/test_web_app.py:8805-8898`이 dual-probe natural-reload exact-field를 이미 잠그고 있으므로 browser contract만 추가

## 핵심 변경

- pre-seeded record: 붉은사막 entity_card with dual-probe URLs
- Step 1: click reload로 서버 세션에 record 등록
- Step 2: `sendRequest({user_text: "방금 검색한 결과 다시 보여줘"})` 자연어 reload
- Assert: `#response-origin-badge` = "WEB" + `.web`, `#response-answer-mode-badge` = "설명 카드", `#response-origin-detail`에 "설명형 단일 출처", "백과 기반" 포함

## 검증

- `git diff --check` — 통과
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "entity-card dual-probe 자연어 reload에서 response origin badge와 answer-mode badge가 유지됩니다" --reporter=line` — 1 passed (7.1s)
- `make e2e-test` — 생략 (shared browser helper 미변경)

## 남은 리스크

- full suite 미실행으로 broader regression 가능성 잔존하나, isolated rerun에서 drift 신호 없음
