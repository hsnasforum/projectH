## 변경 파일
- `verify/4/7/2026-04-07-history-card-entity-card-dual-probe-response-origin-continuity-tightening-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work`의 dual-probe history-card response-origin continuity 주장이 실제 트리와 focused rerun 기준으로 truthful한지 다시 확인하고, 같은 family에서 남은 current-risk를 다음 Claude 슬라이스 하나로 고정하기 위해서입니다.
- history-card entity-card dual-probe family는 이번 round로 닫혔지만, history-card latest-update mixed-source family의 reload/follow-up 24/32는 아직 source-path continuity만 브라우저·문서에 적혀 있어 response-origin continuity가 동일한 강도로 잠겨 있지 않습니다.

## 핵심 변경
- 최신 `/work`가 적은 구현 범위를 재확인했고, `tests/test_web_app.py`, `e2e/tests/web-smoke.spec.mjs`, `README.md`, `docs/ACCEPTANCE_CRITERIA.md`, `docs/MILESTONES.md`에 dual-probe history-card reload/follow-up response-origin continuity assertion과 문구가 실제로 반영돼 있음을 확인했습니다.
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_dual_probe_entity_search_history_card_reload_exact_fields tests.test_web_app.WebAppServiceTest.test_handle_chat_entity_card_dual_probe_follow_up_preserves_source_paths`를 다시 실행했고 `Ran 2 tests in 0.079s`, `OK`를 확인했습니다.
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "history-card entity-card 다시 불러오기 후 dual-probe source path가 context box에 유지됩니다" --reporter=line` 재실행 결과 `1 passed (7.1s)`였습니다.
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "history-card entity-card 다시 불러오기 후 follow-up 질문에서 dual-probe source path가 context box에 유지됩니다" --reporter=line` 재실행 결과 `1 passed (7.0s)`였습니다.
- `git diff --check -- tests/test_web_app.py e2e/tests/web-smoke.spec.mjs README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md`는 clean이었습니다.
- 다음 Claude 실행 슬라이스를 `history-card latest-update mixed-source response-origin continuity tightening`으로 좁혀 `.pipeline/claude_handoff.md`를 갱신했습니다. 근거는 mixed-source browser scenarios 24/32와 대응 문서 설명이 아직 source-path only이고, `test_handle_chat_latest_update_mixed_source_follow_up_preserves_source_paths`도 source_paths만 확인하는 반면, stored-response-origin truth anchor(`test_handle_chat_load_web_search_record_id_mixed_source_latest_update_exact_fields`, `test_handle_chat_latest_update_reload_follow_up_preserves_stored_response_origin`)는 이미 존재하기 때문입니다.

## 검증
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_dual_probe_entity_search_history_card_reload_exact_fields tests.test_web_app.WebAppServiceTest.test_handle_chat_entity_card_dual_probe_follow_up_preserves_source_paths`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "history-card entity-card 다시 불러오기 후 dual-probe source path가 context box에 유지됩니다" --reporter=line`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "history-card entity-card 다시 불러오기 후 follow-up 질문에서 dual-probe source path가 context box에 유지됩니다" --reporter=line`
- `git diff --check -- tests/test_web_app.py e2e/tests/web-smoke.spec.mjs README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md`

## 남은 리스크
- history-card latest-update mixed-source reload/follow-up 24/32는 아직 브라우저 smoke와 문서에서 source-path continuity만 잠그고 있어 `WEB` badge, `최신 확인`, `공식+기사 교차 확인`, `보조 기사` · `공식 기반` continuity drift를 직접 막지 못합니다.
- 전체 Python 회귀와 `make e2e-test`는 이번 focused verification 범위라 다시 실행하지 않았습니다.
