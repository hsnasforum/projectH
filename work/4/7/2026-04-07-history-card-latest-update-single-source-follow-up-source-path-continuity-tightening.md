# history-card latest-update single-source follow-up source-path continuity tightening

날짜: 2026-04-07

## 변경 파일

- `tests/test_web_app.py` — `test_handle_chat_latest_update_single_source_follow_up_preserves_source_paths` 추가
- `e2e/tests/web-smoke.spec.mjs` — latest-update single-source follow-up source-path continuity scenario 1건 추가 (scenario 33)
- `README.md` — scenario 33 추가
- `docs/ACCEPTANCE_CRITERIA.md` — single-source follow-up source-path continuity criteria 추가
- `docs/MILESTONES.md` — single-source follow-up source-path continuity service + browser smoke milestone 항목 추가
- `docs/TASK_BACKLOG.md` — backlog item 39 추가
- `docs/NEXT_STEPS.md` — scenario count 32→33 갱신, single-source follow-up source-path continuity 설명 삽입

## 사용 skill

- 없음

## 변경 이유

- follow-up source-path continuity는 entity-card dual-probe(scenario 31)와 latest-update mixed-source(scenario 32)만 잠겨 있고, single-source one-URL shape는 미검증

## 핵심 변경

- **서비스 테스트**: single-source latest_update 검색 → `load_web_search_record_id + user_text` follow-up에서 `active_context.source_paths`에 `example.com/seoul-weather` 보존 assert
- **브라우저 smoke**: pre-seeded single-source record → 다시 불러오기 → follow-up → `#context-box`에 `example.com/seoul-weather` 포함 assert

## 검증

- `git diff --check` — 통과
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_latest_update_single_source_follow_up_preserves_source_paths` — OK (0.027s)
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "history-card latest-update single-source 다시 불러오기 후 follow-up 질문에서 source path가 context box에 유지됩니다" --reporter=line` — 1 passed (6.8s)
- `make e2e-test` — 생략 (shared browser helper 미변경, isolated rerun에서 drift 신호 없음)

## 남은 리스크

- news-only follow-up source-path continuity는 별도 라운드 대상
- full suite 미실행으로 broader regression 가능성 잔존하나, isolated rerun에서 drift 신호 없음
