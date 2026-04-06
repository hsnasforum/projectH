# entity-card zero-strong-slot browser natural-reload follow-up response-origin continuity smoke tightening

날짜: 2026-04-07

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs` — entity-card zero-strong-slot browser natural-reload follow-up continuity scenario 1건 추가 (scenario 39)
- `README.md` — scenario 39 추가
- `docs/ACCEPTANCE_CRITERIA.md` — browser natural-reload follow-up continuity criteria 추가
- `docs/MILESTONES.md` — browser natural-reload follow-up continuity smoke milestone 항목 추가
- `docs/TASK_BACKLOG.md` — backlog item 45 추가
- `docs/NEXT_STEPS.md` — scenario count 38→39 갱신, browser natural-reload follow-up continuity 설명 삽입

## 사용 skill

- 없음

## 변경 이유

- scenario 38에서 browser natural-reload show-only exact-field를 잠갔지만, natural reload 후 follow-up에서 response origin이 drift하지 않는지는 browser에서 미검증
- service test `tests/test_web_app.py:15489-15563`이 natural reload follow-up continuity를 이미 잠그고 있으므로, browser contract만 추가

## 핵심 변경

- Step 1: click reload로 서버 세션에 record 등록
- Step 2: `sendRequest({user_text: "방금 검색한 결과 다시 보여줘"})` 자연어 reload
- Step 3: `sendRequest({user_text, load_web_search_record_id})` follow-up
- Assert: `#response-origin-badge` = "WEB" + `.web`, `#response-answer-mode-badge` = "설명 카드", `#response-origin-detail`에 "설명형 단일 출처", "백과 기반" 포함

## 검증

- `git diff --check` — 통과
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "entity-card zero-strong-slot 자연어 reload 후 follow-up에서 response origin badge와 answer-mode badge가 drift하지 않습니다" --reporter=line` — 1 passed (6.9s)
- `make e2e-test` — 생략 (shared browser helper 미변경)

## 남은 리스크

- full suite 미실행으로 broader regression 가능성 잔존하나, isolated rerun에서 drift 신호 없음
