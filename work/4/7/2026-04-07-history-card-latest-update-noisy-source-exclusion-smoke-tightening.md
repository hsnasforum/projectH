# history-card latest-update noisy-source exclusion smoke tightening

날짜: 2026-04-07

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs` — latest-update reload noisy community source exclusion scenario 1건 추가 (scenario 21)
- `README.md` — scenario 21 추가
- `docs/ACCEPTANCE_CRITERIA.md` — noisy-source exclusion criteria 추가
- `docs/MILESTONES.md` — noisy-source exclusion smoke milestone 항목 추가
- `docs/TASK_BACKLOG.md` — backlog item 27 추가
- `docs/NEXT_STEPS.md` — scenario count 20→21 갱신, noisy-source exclusion 설명 삽입

## 사용 skill

- 없음

## 변경 이유

- service regression `tests/test_web_app.py:9764-9854`에서 latest-update reload 후 noisy community source가 `source_roles`와 본문에 미노출되는지 이미 잠겨 있지만, 동일 contract의 browser smoke가 없었음
- latest-update reload continuity (scenario 18)와 follow-up continuity (scenario 20)는 clean source_roles만 다루고, noisy source의 negative assertion은 미검증

## 핵심 변경

- pre-seeded record: `answer_mode: "latest_update"`, `source_roles: ["보조 기사", "공식 기반"]` (noisy community 미포함), `results`/`pages` 배열에는 noisy `brunch.co.kr` 출처 포함
- 다시 불러오기 클릭 후 positive assert: `#response-origin-badge` = "WEB", `#response-answer-mode-badge` = "최신 확인", origin detail에 "공식+기사 교차 확인", "보조 기사", "공식 기반"
- negative assert: origin detail에 "보조 커뮤니티", "brunch" 미포함, response body에 "brunch", "로그인 회원가입 구독 광고" 미포함

## 검증

- `git diff --check` — 통과
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "history-card latest-update 다시 불러오기 후 noisy community source가 본문과 origin detail에 노출되지 않습니다" --reporter=line` — 1 passed (4.7s)
- `make e2e-test` — 생략 (single-scenario 추가, shared browser helper 미변경)
- Python regression — 생략 (Playwright-only tightening)

## 남은 리스크

- entity-card variant의 noisy-source exclusion browser smoke는 별도 라운드에서 추가 가능
- full `make e2e-test` suite 미실행으로 broader regression 가능성 잔존하나, isolated rerun에서 drift 신호 없음
