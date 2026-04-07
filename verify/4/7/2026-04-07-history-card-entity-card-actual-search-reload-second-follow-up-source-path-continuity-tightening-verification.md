## 변경 파일
- `verify/4/7/2026-04-07-history-card-entity-card-actual-search-reload-second-follow-up-source-path-continuity-tightening-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work`의 actual-search click-reload second-follow-up source-path continuity 주장이 실제 트리와 focused rerun 기준으로 truthful한지 다시 확인하고, 같은 history-card entity-card family 안에서 다음 current-risk 한 슬라이스를 고정하기 위해서입니다.
- actual-search click-reload family는 이번 `/work`로 reload 48, first follow-up 49, second follow-up 50까지 닫혔고, 다음으로 가장 가까운 user-visible risk는 dual-probe click-reload second-follow-up response-origin continuity입니다.

## 핵심 변경
- 최신 `/work`가 적은 구현 범위를 재확인했고, `tests/test_web_app.py`, `e2e/tests/web-smoke.spec.mjs`, `README.md`, `docs/ACCEPTANCE_CRITERIA.md`, `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md`, `docs/NEXT_STEPS.md`에 actual-search second-follow-up contract가 실제로 반영돼 있음을 확인했습니다. 새 service test, 새 browser scenario 50, smoke scenario count `50`, backlog/next-steps 동기화까지 현재 트리와 맞았습니다.
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_actual_entity_search_history_card_reload_second_follow_up_preserves_source_paths`를 다시 실행했고 `Ran 1 test in 0.081s`, `OK`를 확인했습니다.
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "history-card entity-card 다시 불러오기 후 두 번째 follow-up 질문에서 actual-search source path가 context box에 유지됩니다" --reporter=line` 재실행 결과 `1 passed (7.0s)`였습니다.
- `git diff --check -- tests/test_web_app.py e2e/tests/web-smoke.spec.mjs README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md`는 clean이었습니다.
- 추가 stored-record direct probe에서는 dual-probe click-reload path의 reload, 첫 follow-up, 두 번째 follow-up 모두 `active_context.source_paths`에 `https://www.pearlabyss.com/200`, `https://www.pearlabyss.com/300`, `https://namu.wiki/w/test`가 유지됐습니다. 하지만 두 번째 follow-up `response_origin`은 `provider='web'`를 유지하면서도 `badge='SYSTEM'`으로 drift했고, `answer_mode='entity_card'`, `verification_label='설명형 다중 출처 합의'`, `source_roles=['공식 기반', '백과 기반']`만 남아 있었습니다. 현재 contract는 `tests/test_web_app.py`의 dual-probe reload exact-fields와 first follow-up source-path, `e2e/tests/web-smoke.spec.mjs`의 scenarios 23/31, `README.md`/`docs/ACCEPTANCE_CRITERIA.md`/`docs/MILESTONES.md`의 23/31 설명까지만 닫혀 있어, 다음 Claude 실행 슬라이스를 `history-card entity-card dual-probe reload second-follow-up response-origin continuity tightening`으로 좁혀 `.pipeline/claude_handoff.md`를 갱신했습니다.

## 검증
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_actual_entity_search_history_card_reload_second_follow_up_preserves_source_paths`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "history-card entity-card 다시 불러오기 후 두 번째 follow-up 질문에서 actual-search source path가 context box에 유지됩니다" --reporter=line`
- `git diff --check -- tests/test_web_app.py e2e/tests/web-smoke.spec.mjs README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md`
- `python3 - <<'PY' ... dual-probe stored-record click-reload second-follow-up response_origin direct probe ... PY`

## 남은 리스크
- actual-search click-reload family는 reload 48, first follow-up 49, second follow-up 50 기준으로 source-path + response-origin continuity가 닫혔습니다.
- dual-probe click-reload second-follow-up은 source path가 유지되더라도 stored-record path의 `response_origin.badge`가 `SYSTEM`으로 drift할 수 있어, 현재 user-visible badge continuity가 직접 잠겨 있지 않습니다.
- 전체 Python 회귀와 `make e2e-test`는 이번 focused verification 범위라 다시 실행하지 않았습니다.
