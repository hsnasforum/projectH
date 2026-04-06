# history-card latest-update mixed-source follow-up source-path continuity tightening

날짜: 2026-04-07

## 변경 파일

- `tests/test_web_app.py` — `test_handle_chat_latest_update_mixed_source_follow_up_preserves_source_paths` 추가
- `e2e/tests/web-smoke.spec.mjs` — latest-update mixed-source follow-up source-path continuity scenario 1건 추가 (scenario 32)
- `README.md` — scenario 32 추가
- `docs/ACCEPTANCE_CRITERIA.md` — mixed-source follow-up source-path continuity criteria 추가
- `docs/MILESTONES.md` — mixed-source follow-up source-path continuity service + browser smoke milestone 항목 추가
- `docs/TASK_BACKLOG.md` — backlog item 38 추가
- `docs/NEXT_STEPS.md` — scenario count 31→32 갱신, mixed-source follow-up source-path continuity 설명 삽입

## 사용 skill

- 없음

## 변경 이유

- latest-update follow-up response-origin continuity는 mixed/single/news 3개 variant가 모두 닫혔지만, follow-up source-path continuity는 entity-card dual-probe만 scenario 31에서 잠김
- mixed-source latest-update show-only source-path continuity는 scenario 24에서, follow-up response-origin은 scenario 20에서 잠갔으나, follow-up source-path는 미검증

## 핵심 변경

- **서비스 테스트**: mixed-source latest_update 검색 → `load_web_search_record_id + user_text` follow-up에서 `active_context.source_paths`에 `store.steampowered.com`, `yna.co.kr` 보존 assert
- **브라우저 smoke**: pre-seeded mixed-source record → 다시 불러오기 → follow-up → `#context-box`에 `store.steampowered.com`, `yna.co.kr` 포함 assert

## 검증

- `git diff --check` — 통과
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_latest_update_mixed_source_follow_up_preserves_source_paths` — OK (0.030s)
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "history-card latest-update mixed-source 다시 불러오기 후 follow-up 질문에서 source path가 context box에 유지됩니다" --reporter=line` — 1 passed (6.8s)
- `make e2e-test` — 생략 (shared browser helper 미변경, isolated rerun에서 drift 신호 없음)

## 남은 리스크

- single-source/news-only follow-up source-path continuity는 별도 라운드에서 추가 가능
- full suite 미실행으로 broader regression 가능성 잔존하나, isolated rerun에서 drift 신호 없음
