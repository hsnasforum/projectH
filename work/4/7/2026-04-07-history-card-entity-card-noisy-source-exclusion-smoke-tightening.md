# history-card entity-card noisy-source exclusion smoke tightening

날짜: 2026-04-07

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs` — entity-card reload noisy single-source claim exclusion scenario 1건 추가 (scenario 22)
- `README.md` — scenario 22 추가
- `docs/ACCEPTANCE_CRITERIA.md` — entity-card noisy-source exclusion criteria 추가
- `docs/MILESTONES.md` — entity-card noisy-source exclusion smoke milestone 항목 추가
- `docs/TASK_BACKLOG.md` — backlog item 28 추가
- `docs/NEXT_STEPS.md` — scenario count 21→22 갱신, entity-card noisy-source exclusion 설명 삽입

## 사용 skill

- 없음

## 변경 이유

- service regression `tests/test_web_app.py:9431-9548`에서 entity-card reload 후 noisy single-source claim(`출시일`, `2025`)이 본문에 미노출되는지 이미 잠겨 있지만, 동일 contract의 browser smoke가 없었음
- latest-update noisy-source exclusion은 scenario 21에서 이미 브라우저까지 잠갔으므로, entity-card variant를 같은 수준으로 올리는 것이 natural next step

## 핵심 변경

- pre-seeded record: `answer_mode: "entity_card"`, `source_roles: ["백과 기반"]` (noisy blog 미포함), `results`/`pages` 배열에는 noisy `blog.example.com` 출처 포함, `summary_text`에 "확인된 사실:" + "교차 확인" 포함
- 다시 불러오기 클릭 후:
  - positive assert: `#response-origin-badge` = "WEB", `#response-answer-mode-badge` = "설명 카드", origin detail에 "설명형 단일 출처", "백과 기반", response body에 "확인된 사실:", "교차 확인"
  - negative assert: origin detail에 "blog.example.com" 미포함, response body에 "출시일", "2025", "로그인 회원가입 구독 광고" 미포함

## 검증

- `git diff --check` — 통과
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "history-card entity-card 다시 불러오기 후 noisy single-source claim이 본문과 origin detail에 노출되지 않습니다" --reporter=line` — 1 passed (6.6s)
- `make e2e-test` — 생략 (single-scenario 추가, shared browser helper 미변경)
- Python regression — 생략 (Playwright-only tightening)

## 남은 리스크

- full `make e2e-test` suite 미실행으로 broader regression 가능성 잔존하나, isolated rerun에서 drift 신호 없음
- history-card reload family의 주요 variant(entity-card/latest-update × show-only/follow-up/noisy)가 이제 브라우저까지 잠겼으므로, 이 family의 remaining risk는 낮음
