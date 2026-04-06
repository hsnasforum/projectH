# history-card latest-update single-source source-path continuity smoke tightening

날짜: 2026-04-07

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs` — latest-update single-source reload source-path continuity scenario 1건 추가 (scenario 28)
- `README.md` — scenario 28 추가
- `docs/ACCEPTANCE_CRITERIA.md` — single-source source-path continuity criteria 추가
- `docs/MILESTONES.md` — single-source source-path continuity smoke milestone 항목 추가
- `docs/TASK_BACKLOG.md` — backlog item 34 추가
- `docs/NEXT_STEPS.md` — scenario count 27→28 갱신, single-source source-path continuity 설명 삽입

## 사용 skill

- 없음

## 변경 이유

- mixed-source source-path continuity는 scenario 24에서, news-only source-path continuity는 scenario 27에서 이미 잠갔지만, single-source source-path continuity(`#context-box`에 단일 URL 유지)는 미검증
- single-source verification-label continuity(scenario 25)는 origin detail만 확인하고 context box는 미확인

## 핵심 변경

- pre-seeded record: `answer_mode: "latest_update"`, single result (`example.com/seoul-weather`)
- 다시 불러오기 클릭 후 assert: `#response-origin-badge` = "WEB", `#context-box`에 `example.com/seoul-weather` 포함

## 검증

- `git diff --check` — 통과
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "history-card latest-update single-source 다시 불러오기 후 source path가 context box에 유지됩니다" --reporter=line` — 1 passed (6.6s)
- `make e2e-test` — 생략 (single-scenario 추가, shared browser helper 미변경)
- Python regression — 생략 (Playwright-only tightening)

## 남은 리스크

- full `make e2e-test` suite 미실행으로 broader regression 가능성 잔존하나, isolated rerun에서 drift 신호 없음
- history-card reload family의 source-path continuity가 entity-card(dual-probe), latest-update(mixed/news/single) 모두 잠겼으므로 이 축의 remaining risk는 낮음
