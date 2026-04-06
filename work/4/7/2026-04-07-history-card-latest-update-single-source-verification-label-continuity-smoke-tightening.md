# history-card latest-update single-source verification-label continuity smoke tightening

날짜: 2026-04-07

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs` — latest-update single-source reload verification-label continuity scenario 1건 추가 (scenario 25)
- `README.md` — scenario 25 추가
- `docs/ACCEPTANCE_CRITERIA.md` — single-source verification-label continuity criteria 추가
- `docs/MILESTONES.md` — single-source verification-label continuity smoke milestone 항목 추가
- `docs/TASK_BACKLOG.md` — backlog item 31 추가
- `docs/NEXT_STEPS.md` — scenario count 24→25 갱신, single-source verification-label continuity 설명 삽입

## 사용 skill

- 없음

## 변경 이유

- 기존 latest-update reload smoke는 모두 mixed-source `공식+기사 교차 확인` + `보조 기사`·`공식 기반` 조합만 검증하고, `단일 출처 참고` + `보조 출처` single-source variant는 미검증
- service regression `tests/test_web_app.py:8233-8299`에서 single-source latest_update reload exact fields가 이미 잠겨 있으므로, browser contract까지 끌어올리는 작업

## 핵심 변경

- pre-seeded record: `answer_mode: "latest_update"`, `verification_label: "단일 출처 참고"`, `source_roles: ["보조 출처"]`, single result (`example.com/seoul-weather`)
- 다시 불러오기 클릭 후 assert: `#response-origin-badge` = "WEB" + `.web` class, `#response-answer-mode-badge` = "최신 확인", `#response-origin-detail`에 "단일 출처 참고", "보조 출처" 포함

## 검증

- `git diff --check` — 통과
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "history-card latest-update single-source 다시 불러오기 후 단일 출처 참고 verification label과 보조 출처 source role이 유지됩니다" --reporter=line` — 1 passed (6.6s)
- `make e2e-test` — 생략 (single-scenario 추가, shared browser helper 미변경)
- Python regression — 생략 (Playwright-only tightening)

## 남은 리스크

- full `make e2e-test` suite 미실행으로 broader regression 가능성 잔존하나, isolated rerun에서 drift 신호 없음
