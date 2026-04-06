# entity-card zero-strong-slot browser natural-reload exact-field smoke tightening

날짜: 2026-04-07

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs` — entity-card zero-strong-slot browser natural-reload exact-field scenario 1건 추가 (scenario 38)
- `README.md` — scenario 38 추가
- `docs/ACCEPTANCE_CRITERIA.md` — browser natural-reload criteria 추가
- `docs/MILESTONES.md` — browser natural-reload smoke milestone 항목 추가
- `docs/TASK_BACKLOG.md` — backlog item 44 추가
- `docs/NEXT_STEPS.md` — scenario count 37→38 갱신, browser natural-reload 설명 삽입

## 사용 skill

- 없음

## 변경 이유

- 이전 truth-sync에서 scenario 37의 browser flow가 click-based임을 정직하게 밝혔고, 자연어 reload browser coverage가 아직 없다는 gap이 남아 있었음
- 접근: pre-seeded record → click reload로 서버 세션에 record 등록 → `sendRequest({user_text: "방금 검색한 결과 다시 보여줘"})` 자연어 reload → response origin badge assert
- 이 방식으로 서버 세션이 web_search_history를 알고 있는 상태에서 자연어 reload path를 browser에서 직접 테스트 가능

## 핵심 변경

- Step 1: pre-seeded record click reload (세션 등록 목적)
- Step 2: `sendRequest({user_text: "방금 검색한 결과 다시 보여줘"})` — record_id 없이 자연어만으로 reload
- Assert: `#response-origin-badge` = "WEB" + `.web`, `#response-answer-mode-badge` = "설명 카드", `#response-origin-detail`에 "설명형 단일 출처", "백과 기반" 포함

## 검증

- `git diff --check` — 통과
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "entity-card zero-strong-slot 방금 검색한 결과 다시 보여줘 자연어 reload에서 response origin badge와 answer-mode badge가 유지됩니다" --reporter=line` — 1 passed (6.8s)
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_zero_strong_slot_entity_card_natural_reload_exact_fields` — 기존 service test 재확인용으로만 유지 (새 service test 추가 불필요)
- `make e2e-test` — 생략 (shared browser helper 미변경)

## 남은 리스크

- full suite 미실행으로 broader regression 가능성 잔존하나, isolated rerun에서 drift 신호 없음
