# history-card entity-card dual-probe follow-up source-path continuity tightening

날짜: 2026-04-07

## 변경 파일

- `tests/test_web_app.py` — `test_handle_chat_entity_card_dual_probe_follow_up_preserves_source_paths` 추가
- `e2e/tests/web-smoke.spec.mjs` — entity-card dual-probe follow-up source-path continuity scenario 1건 추가 (scenario 31)
- `README.md` — scenario 31 추가
- `docs/ACCEPTANCE_CRITERIA.md` — entity-card dual-probe follow-up source-path continuity criteria 추가
- `docs/MILESTONES.md` — entity-card dual-probe follow-up source-path continuity service + browser smoke milestone 항목 추가
- `docs/TASK_BACKLOG.md` — backlog item 37 추가
- `docs/NEXT_STEPS.md` — scenario count 30→31 갱신, entity-card dual-probe follow-up source-path continuity 설명 삽입

## 사용 skill

- 없음

## 변경 이유

- entity-card dual-probe source-path continuity는 show-only reload에서 service(`tests/test_web_app.py:8508-8565`)와 browser(scenario 23)로 이미 잠갔지만, follow-up path에서는 response-origin drift prevention만 잠겨 있고 source-path continuity는 미검증
- latest-update follow-up family는 mixed/single/news 3개 variant가 모두 닫혔으므로, entity-card follow-up의 남은 gap으로 넘어가는 것이 자연스러운 next step

## 핵심 변경

- **서비스 테스트**: dual-probe entity-card record → `load_web_search_record_id + user_text` follow-up에서 `active_context.source_paths`에 `pearlabyss.com/200`, `pearlabyss.com/300` 보존 assert
- **브라우저 smoke**: pre-seeded dual-probe record → 다시 불러오기 → follow-up 전송 → `#context-box`에 `pearlabyss.com/200`, `pearlabyss.com/300` 포함 assert

## 검증

- `git diff --check` — 통과
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_entity_card_dual_probe_follow_up_preserves_source_paths` — OK (0.023s)
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "history-card entity-card 다시 불러오기 후 follow-up 질문에서 dual-probe source path가 context box에 유지됩니다" --reporter=line` — 1 passed (6.8s)
- `make e2e-test` — 생략 (shared browser helper 미변경, isolated rerun에서 drift 신호 없음)

## 남은 리스크

- full Python regression suite 미실행 (isolated 1건만 확인)
- full `make e2e-test` suite 미실행으로 broader regression 가능성 잔존하나, isolated rerun에서 drift 신호 없음
