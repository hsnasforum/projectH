# entity-card dual-probe browser natural-reload source-path continuity smoke tightening

날짜: 2026-04-07

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs` — entity-card dual-probe browser natural-reload source-path continuity scenario 1건 추가 (scenario 41)
- `README.md` — scenario 41 추가
- `docs/ACCEPTANCE_CRITERIA.md` — dual-probe natural-reload source-path continuity criteria 추가
- `docs/MILESTONES.md` — dual-probe natural-reload source-path continuity smoke milestone 항목 추가
- `docs/TASK_BACKLOG.md` — backlog item 47 추가
- `docs/NEXT_STEPS.md` — scenario count 40→41 갱신, dual-probe natural-reload source-path continuity 설명 삽입

## 사용 skill

- 없음

## 변경 이유

- scenario 40에서 generic entity-card natural-reload exact-field를 잠갔지만, dual-probe source-path continuity는 click-based reload만 잠겨 있고(scenario 23) natural-reload path는 미검증
- service test `tests/test_web_app.py:8657-8744`이 actual entity-search dual-probe natural-reload source-path를 이미 잠그고 있으므로 browser contract만 추가

## 핵심 변경

- pre-seeded record: 붉은사막 entity_card with dual-probe URLs (`pearlabyss.com/ko-KR/Board/Detail?_boardNo=200`, `pearlabyss.com/ko-KR/Board/Detail?_boardNo=300`)
- Step 1: click reload로 서버 세션에 record 등록
- Step 2: `sendRequest({user_text: "방금 검색한 결과 다시 보여줘"})` 자연어 reload
- Assert: `#context-box`에 두 dual-probe URL 모두 포함

## 검증

- `git diff --check` — 통과
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "entity-card dual-probe 자연어 reload에서 source path가 context box에 유지됩니다" --reporter=line` — 1 passed (6.8s)
- `make e2e-test` — 생략 (shared browser helper 미변경)

## 남은 리스크

- full suite 미실행으로 broader regression 가능성 잔존하나, isolated rerun에서 drift 신호 없음
