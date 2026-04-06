# history-card latest-update news-only source-path continuity smoke tightening

날짜: 2026-04-07

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs` — latest-update news-only reload source-path continuity scenario 1건 추가 (scenario 27)
- `README.md` — scenario 27 추가
- `docs/ACCEPTANCE_CRITERIA.md` — news-only source-path continuity criteria 추가
- `docs/MILESTONES.md` — news-only source-path continuity smoke milestone 항목 추가
- `docs/TASK_BACKLOG.md` — backlog item 33 추가
- `docs/NEXT_STEPS.md` — scenario count 26→27 갱신, news-only source-path continuity 설명 삽입

## 사용 skill

- 없음

## 변경 이유

- mixed-source source-path continuity는 scenario 24에서, news-only verification-label continuity는 scenario 26에서 이미 잠갔지만, news-only source-path continuity(`#context-box`에 기사 URL 유지)는 미검증
- UI 렌더 경로 `app/static/app.js:2397-2405`와 service reload 경로가 이미 준비되어 있으므로 browser contract만 추가

## 핵심 변경

- pre-seeded record: `answer_mode: "latest_update"`, news pair (`hankyung.com` + `mk.co.kr`)
- 다시 불러오기 클릭 후 assert: `#response-origin-badge` = "WEB", `#context-box`에 `hankyung.com`과 `mk.co.kr` 포함

## 검증

- `git diff --check` — 통과
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "history-card latest-update news-only 다시 불러오기 후 기사 source path가 context box에 유지됩니다" --reporter=line` — 1 passed (6.7s)
- `make e2e-test` — 생략 (single-scenario 추가, shared browser helper 미변경)
- Python regression — 생략 (Playwright-only tightening)

## 남은 리스크

- full `make e2e-test` suite 미실행으로 broader regression 가능성 잔존하나, isolated rerun에서 drift 신호 없음
