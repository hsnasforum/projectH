## 변경 파일
- `verify/4/7/2026-04-07-entity-card-zero-strong-slot-natural-reload-source-path-continuity-tightening-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work`의 zero-strong-slot 자연어 reload source-path continuity 주장이 실제 트리와 focused rerun 기준으로 truthful한지 다시 확인하고, 같은 zero-strong-slot family에서 남은 current-risk를 다음 Claude 슬라이스 하나로 고정하기 위해서입니다.
- zero-strong-slot family는 history-card 35/36과 natural-reload 38/39까지 source-path + response-origin continuity가 닫혔고, 남은 가장 가까운 same-family gap은 scenario 37의 click-reload second follow-up source-path continuity입니다.

## 핵심 변경
- 최신 `/work`가 적은 구현 범위를 재확인했고, `tests/test_web_app.py`, `e2e/tests/web-smoke.spec.mjs`, `README.md`, `docs/ACCEPTANCE_CRITERIA.md`, `docs/MILESTONES.md`에 zero-strong-slot natural-reload source-path continuity assertion과 문구가 실제로 반영돼 있음을 확인했습니다.
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_zero_strong_slot_entity_card_natural_reload_exact_fields tests.test_web_app.WebAppServiceTest.test_handle_chat_zero_strong_slot_entity_card_natural_reload_follow_up_preserves_stored_response_origin`를 다시 실행했고 `Ran 2 tests in 0.082s`, `OK`를 확인했습니다.
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "entity-card zero-strong-slot 방금 검색한 결과 다시 보여줘 자연어 reload에서 response origin badge와 answer-mode badge가 유지됩니다" --reporter=line` 재실행 결과 `1 passed (7.0s)`였습니다.
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "entity-card zero-strong-slot 자연어 reload 후 follow-up에서 response origin badge와 answer-mode badge가 drift하지 않습니다" --reporter=line` 재실행 결과 `1 passed (7.1s)`였습니다.
- `git diff --check -- tests/test_web_app.py e2e/tests/web-smoke.spec.mjs README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md`는 clean이었습니다.
- 추가 direct probe에서는 zero-strong-slot entity-card click-reload 후 첫 follow-up과 두 번째 follow-up 모두 `active_context.source_paths`에 `https://namu.wiki/w/testgame`, `https://ko.wikipedia.org/wiki/testgame`가 유지됐고, 두 번째 follow-up `response_origin`도 `entity_card`, `설명형 단일 출처`, `백과 기반`으로 유지됐습니다. 현재 browser scenario 37과 docs 37은 아직 response-origin continuity만 적고 있어, 다음 Claude 실행 슬라이스를 `entity-card zero-strong-slot click-reload second-follow-up source-path continuity tightening`으로 좁혀 `.pipeline/claude_handoff.md`를 갱신했습니다.

## 검증
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_zero_strong_slot_entity_card_natural_reload_exact_fields tests.test_web_app.WebAppServiceTest.test_handle_chat_zero_strong_slot_entity_card_natural_reload_follow_up_preserves_stored_response_origin`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "entity-card zero-strong-slot 방금 검색한 결과 다시 보여줘 자연어 reload에서 response origin badge와 answer-mode badge가 유지됩니다" --reporter=line`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "entity-card zero-strong-slot 자연어 reload 후 follow-up에서 response origin badge와 answer-mode badge가 drift하지 않습니다" --reporter=line`
- `git diff --check -- tests/test_web_app.py e2e/tests/web-smoke.spec.mjs README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md`
- `python3 - <<'PY' ... zero-strong-slot click-reload second-follow-up source_paths direct probe ... PY`

## 남은 리스크
- zero-strong-slot history-card 35/36과 자연어 reload 38/39 family는 이번 round로 닫혔습니다.
- click-reload second follow-up 37은 runtime에서 `namu.wiki`, `ko.wikipedia.org` source path가 유지되지만, 현재 브라우저 smoke와 문서는 아직 response-origin continuity만 적고 있어 source-path continuity drift를 직접 막지 못합니다.
- 전체 Python 회귀와 `make e2e-test`는 이번 focused verification 범위라 다시 실행하지 않았습니다.
