# history-card entity-card zero-strong-slot follow-up response-origin continuity tightening

날짜: 2026-04-07

## 변경 파일

- `tests/test_web_app.py` — `test_handle_chat_zero_strong_slot_entity_card_history_card_reload_follow_up_preserves_stored_response_origin` 추가
- `e2e/tests/web-smoke.spec.mjs` — zero-strong-slot entity-card follow-up response-origin continuity scenario 1건 추가 (scenario 36)
- `README.md` — scenario 36 추가
- `docs/ACCEPTANCE_CRITERIA.md` — zero-strong-slot follow-up drift prevention criteria 추가
- `docs/MILESTONES.md` — zero-strong-slot follow-up continuity service + browser smoke milestone 항목 추가
- `docs/TASK_BACKLOG.md` — backlog item 42 추가
- `docs/NEXT_STEPS.md` — scenario count 35→36 갱신, zero-strong-slot follow-up continuity 설명 삽입

## 사용 skill

- 없음

## 변경 이유

- generic entity-card follow-up continuity는 service+browser로 잠겨 있지만, zero-strong-slot variant를 별도로 지목한 follow-up contract는 미검증
- zero-strong-slot show-only reload continuity는 scenario 35에서 잠갔으므로, 같은 fixture로 follow-up path까지 확장

## 핵심 변경

- **서비스 테스트**: zero-strong-slot entity-card 검색 → `load_web_search_record_id + user_text` follow-up에서 `answer_mode`, `verification_label`, `source_roles` exact-field 유지 assert
- **브라우저 smoke**: pre-seeded zero-strong-slot record → 다시 불러오기 → follow-up → `#response-origin-badge` = "WEB", `#response-answer-mode-badge` = "설명 카드", `#response-origin-detail`에 "설명형 단일 출처", "백과 기반" 포함 assert

## 검증

- `git diff --check` — 통과
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_zero_strong_slot_entity_card_history_card_reload_follow_up_preserves_stored_response_origin` — OK (0.041s)
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "history-card entity-card zero-strong-slot 다시 불러오기 후 follow-up 질문에서 response origin badge와 answer-mode badge가 drift하지 않습니다" --reporter=line` — 1 passed (7.0s)
- `make e2e-test` — 생략 (shared browser helper 미변경)

## 남은 리스크

- full suite 미실행으로 broader regression 가능성 잔존하나, isolated rerun에서 drift 신호 없음
