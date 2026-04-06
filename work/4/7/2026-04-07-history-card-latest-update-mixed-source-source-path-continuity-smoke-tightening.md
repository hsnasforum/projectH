# history-card latest-update mixed-source source-path continuity smoke tightening

날짜: 2026-04-07

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs` — latest-update reload mixed-source source-path continuity scenario 1건 추가 (scenario 24)
- `README.md` — scenario 24 추가
- `docs/ACCEPTANCE_CRITERIA.md` — latest-update mixed-source source-path continuity criteria 추가
- `docs/MILESTONES.md` — latest-update mixed-source source-path continuity smoke milestone 항목 추가
- `docs/TASK_BACKLOG.md` — backlog item 30 추가
- `docs/NEXT_STEPS.md` — scenario count 23→24 갱신, latest-update mixed-source source-path continuity 설명 삽입

## 사용 skill

- 없음

## 변경 이유

- entity-card dual-probe source-path continuity는 scenario 23에서 이미 브라우저까지 잠갔지만, latest-update variant의 `#context-box` source-path continuity는 미검증
- service regression `tests/test_web_app.py:8155-8445`와 UI 렌더 경로 `app/static/app.js:2390-2411`은 이미 존재하므로 browser contract까지 끌어올리는 작업

## 핵심 변경

- pre-seeded record: `answer_mode: "latest_update"`, `results`/`pages` 배열에 `store.steampowered.com/sale/summer2026`과 `www.yna.co.kr/view/AKR20260401000100017` 포함
- 다시 불러오기 클릭 후 assert: `#response-origin-badge` = "WEB", `#context-box`에 `store.steampowered.com`과 `yna.co.kr` 포함

## 검증

- `git diff --check` — 통과
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "history-card latest-update 다시 불러오기 후 mixed-source source path가 context box에 유지됩니다" --reporter=line` — 1 passed (6.6s)
- `make e2e-test` — 생략 (single-scenario 추가, shared browser helper 미변경)
- Python regression — 생략 (Playwright-only tightening)

## 남은 리스크

- history-card reload family의 주요 variant(entity-card/latest-update × badge continuity/follow-up/noisy exclusion/source-path)가 이제 브라우저까지 모두 잠겼으므로, 이 family의 remaining risk는 매우 낮음
- full `make e2e-test` suite 미실행으로 broader regression 가능성 잔존하나, isolated rerun에서 drift 신호 없음
