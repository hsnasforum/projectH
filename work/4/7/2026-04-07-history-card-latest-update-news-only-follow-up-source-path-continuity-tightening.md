# history-card latest-update news-only follow-up source-path continuity tightening

날짜: 2026-04-07

## 변경 파일

- `tests/test_web_app.py` — `test_handle_chat_latest_update_news_only_follow_up_preserves_source_paths` 추가
- `e2e/tests/web-smoke.spec.mjs` — latest-update news-only follow-up source-path continuity scenario 1건 추가 (scenario 34)
- `README.md` — scenario 34 추가
- `docs/ACCEPTANCE_CRITERIA.md` — news-only follow-up source-path continuity criteria 추가
- `docs/MILESTONES.md` — news-only follow-up source-path continuity service + browser smoke milestone 항목 추가
- `docs/TASK_BACKLOG.md` — backlog item 40 추가
- `docs/NEXT_STEPS.md` — scenario count 33→34 갱신, news-only follow-up source-path continuity 설명 삽입

## 사용 skill

- 없음

## 변경 이유

- follow-up source-path continuity가 entity-card dual-probe(scenario 31), latest-update mixed-source(scenario 32), latest-update single-source(scenario 33)까지 닫혔지만, news-only variant는 미검증
- news-only show-only source-path continuity(scenario 27)와 news-only follow-up response-origin continuity(scenario 30)는 이미 있었으므로 같은 fixture로 follow-up source-path만 추가

## 핵심 변경

- **서비스 테스트**: news-only latest_update 검색(hankyung+mk) → `load_web_search_record_id + user_text` follow-up에서 `active_context.source_paths`에 `hankyung.com`, `mk.co.kr` 보존 assert
- **브라우저 smoke**: pre-seeded news-only record → 다시 불러오기 → follow-up → `#context-box`에 `hankyung.com`, `mk.co.kr` 포함 assert

## 검증

- `git diff --check` — 통과
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_latest_update_news_only_follow_up_preserves_source_paths` — OK (0.029s)
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "history-card latest-update news-only 다시 불러오기 후 follow-up 질문에서 기사 source path가 context box에 유지됩니다" --reporter=line` — 1 passed (6.8s)
- `make e2e-test` — 생략 (shared browser helper 미변경, isolated rerun에서 drift 신호 없음)

## 남은 리스크

- follow-up source-path continuity family가 entity-card dual-probe + latest-update mixed/single/news 4개 variant 모두 service+browser로 닫혔으므로, 이 family의 remaining risk는 매우 낮음
- full suite 미실행으로 broader regression 가능성 잔존하나, isolated rerun에서 drift 신호 없음
