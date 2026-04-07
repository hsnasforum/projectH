## 변경 파일
- `verify/4/7/2026-04-07-entity-card-dual-probe-natural-reload-second-follow-up-continuity-tightening-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work`의 dual-probe natural-reload second-follow-up continuity 주장이 실제 트리와 focused rerun 기준으로 truthful한지 다시 확인하고, 같은 자연어 reload family 안에서 다음 current-risk 한 슬라이스를 고정하기 위해서입니다.
- dual-probe natural-reload family는 이번 `/work`로 initial reload 41/42, first follow-up 43/44, second follow-up 52까지 닫혔고, 다음으로 가장 가까운 user-visible gap은 actual-search natural-reload second-follow-up continuity입니다.

## 핵심 변경
- 최신 `/work`가 적은 구현 범위를 재확인했고, `tests/test_web_app.py`, `e2e/tests/web-smoke.spec.mjs`, `README.md`, `docs/ACCEPTANCE_CRITERIA.md`, `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md`, `docs/NEXT_STEPS.md`에 dual-probe natural-reload second-follow-up contract가 실제로 반영돼 있음을 확인했습니다. 새 service test, 새 browser scenario 52, smoke scenario count `52`, backlog/next-steps 동기화까지 현재 트리와 맞았습니다.
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_dual_probe_natural_reload_second_follow_up_preserves_response_origin_and_source_paths`를 다시 실행했고 `Ran 1 test in 0.086s`, `OK`를 확인했습니다.
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "entity-card dual-probe 자연어 reload 후 두 번째 follow-up에서 response origin badge와 answer-mode badge가 drift하지 않습니다" --reporter=line` 재실행 결과 `1 passed (7.3s)`였습니다.
- `git diff --check -- tests/test_web_app.py e2e/tests/web-smoke.spec.mjs README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md`는 clean이었습니다.
- 추가 direct probe에서는 actual-search natural-reload path의 reload, 첫 follow-up, 두 번째 follow-up 모두 `response_origin.badge='WEB'`, `provider='web'`, `answer_mode='entity_card'`, `verification_label='설명형 다중 출처 합의'`, `source_roles=['백과 기반']`를 유지했고, 두 번째 follow-up `active_context.source_paths`에도 `https://namu.wiki/w/%EB%B6%89%EC%9D%80%EC%82%AC%EB%A7%89`, `https://ko.wikipedia.org/wiki/%EB%B6%89%EC%9D%80%EC%82%AC%EB%A7%89`가 남았습니다. 반면 현재 contract는 `tests/test_web_app.py:16284`, `tests/test_web_app.py:16352`, `e2e/tests/web-smoke.spec.mjs:4889`, `e2e/tests/web-smoke.spec.mjs:5009`, `README.md:159`, `docs/ACCEPTANCE_CRITERIA.md:1366`, `docs/ACCEPTANCE_CRITERIA.md:1368`의 first follow-up까지만 닫혀 있어, 다음 Claude 실행 슬라이스를 `entity-card actual-search natural-reload second-follow-up continuity tightening`으로 좁혀 `.pipeline/claude_handoff.md`를 갱신했습니다.

## 검증
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_dual_probe_natural_reload_second_follow_up_preserves_response_origin_and_source_paths`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "entity-card dual-probe 자연어 reload 후 두 번째 follow-up에서 response origin badge와 answer-mode badge가 drift하지 않습니다" --reporter=line`
- `git diff --check -- tests/test_web_app.py e2e/tests/web-smoke.spec.mjs README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md`
- `python3 - <<'PY' ... actual-search natural-reload second-follow-up response_origin + source_paths direct probe ... PY`

## 남은 리스크
- dual-probe natural-reload family는 initial reload 41/42, first follow-up 43/44, second follow-up 52 기준으로 source-path + response-origin continuity가 닫혔습니다.
- actual-search natural-reload family는 first follow-up까지만 contract가 있고, 두 번째 follow-up continuity는 runtime truth가 있어도 service/browser/docs에서 아직 직접 잠겨 있지 않습니다.
- 전체 Python 회귀와 `make e2e-test`는 이번 focused verification 범위라 다시 실행하지 않았습니다.
