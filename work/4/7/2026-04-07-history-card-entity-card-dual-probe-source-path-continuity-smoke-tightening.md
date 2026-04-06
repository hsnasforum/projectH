# history-card entity-card dual-probe source-path continuity smoke tightening

날짜: 2026-04-07

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs` — entity-card reload dual-probe source-path continuity scenario 1건 추가 (scenario 23)
- `README.md` — scenario 23 추가
- `docs/ACCEPTANCE_CRITERIA.md` — dual-probe source-path continuity criteria 추가
- `docs/MILESTONES.md` — dual-probe source-path continuity smoke milestone 항목 추가
- `docs/TASK_BACKLOG.md` — backlog item 29 추가
- `docs/NEXT_STEPS.md` — scenario count 22→23 갱신, dual-probe source-path continuity 설명 삽입

## 사용 skill

- 없음

## 변경 이유

- service regression `tests/test_web_app.py:8508-8655`에서 entity-card dual-probe reload 후 `active_context.source_paths`에 두 probe URL이 보존되는지 이미 잠겨 있고, UI도 `app/static/app.js:2390-2411`에서 `source_paths`를 `#context-box`의 `출처:` 줄로 렌더링하지만, 동일 contract의 browser smoke가 없었음

## 핵심 변경

- pre-seeded record: `answer_mode: "entity_card"`, `results` 배열에 `pearlabyss.com/200`과 `pearlabyss.com/300` dual-probe URL 포함, `pages` 배열에 해당 두 페이지 텍스트 포함
- 다시 불러오기 클릭 후 assert: `#response-origin-badge` = "WEB", `#context-box`에 `pearlabyss.com/200`과 `pearlabyss.com/300` 포함

## 검증

- `git diff --check` — 통과
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "history-card entity-card 다시 불러오기 후 dual-probe source path가 context box에 유지됩니다" --reporter=line` — 1 passed (6.6s)
- `make e2e-test` — 생략 (single-scenario 추가, shared browser helper 미변경)
- Python regression — 생략 (Playwright-only tightening)

## 남은 리스크

- latest-update variant의 source-path continuity browser smoke는 별도 라운드에서 추가 가능
- full `make e2e-test` suite 미실행으로 broader regression 가능성 잔존하나, isolated rerun에서 drift 신호 없음
