# history-card latest-update reload response-origin continuity smoke tightening

날짜: 2026-04-07

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs` — latest-update reload response-origin continuity scenario 1건 추가

## 사용 skill

- 없음 (단일 파일 Playwright scenario 추가)

## 변경 이유

- service regression `tests/test_web_app.py:8155-8231`에서 latest-update reload의 `answer_mode`, `verification_label`, `source_roles` exact field continuity가 이미 잠겨 있지만, Playwright smoke에는 history-card badge row의 latest-update 표시만 확인하고 reload 후 response origin continuity는 아직 잠기지 않았음
- entity_card reload scenario는 이미 존재(`web-smoke.spec.mjs:1112-1220`)하지만 latest_update variant는 없었음

## 핵심 변경

- `e2e/tests/web-smoke.spec.mjs`에 "history-card latest-update 다시 불러오기 후 response origin badge와 answer-mode badge가 유지됩니다" scenario 추가
- pre-seeded record: `answer_mode: "latest_update"`, `verification_label: "공식+기사 교차 확인"`, `source_roles: ["보조 기사", "공식 기반"]`
- 다시 불러오기 클릭 후 assert: `#response-origin-badge` = "WEB" + `.web` class, `#response-answer-mode-badge` = "최신 확인", `#response-origin-detail`에 "공식+기사 교차 확인", "보조 기사", "공식 기반" 포함

## 검증

- `git diff --check -- e2e/tests/web-smoke.spec.mjs` — 통과
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "history-card latest-update 다시 불러오기 후 response origin badge와 answer-mode badge가 유지됩니다" --reporter=line` — 1 passed (6.7s)
- `python3 -m unittest -v tests.test_web_app` — 생략 (Playwright-only tightening, Python backend 미변경)
- `make e2e-test` — 생략 (single-scenario 추가, shared browser helper 미변경)

## 남은 리스크

- latest-update reload follow-up path continuity는 이번 라운드 범위 밖 (entity_card follow-up pattern과 동일한 구조로 추후 추가 가능)
- noisy community host exclusion variant는 별도 라운드에서 처리
- full `make e2e-test` suite 미실행으로 broader regression 가능성 잔존하나, isolated rerun에서 drift 신호 없음
