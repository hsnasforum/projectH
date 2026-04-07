## 변경 파일
- `verify/4/7/2026-04-07-entity-card-zero-strong-slot-click-reload-second-follow-up-source-path-continuity-tightening-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work`의 zero-strong-slot click-reload second-follow-up source-path continuity 주장이 실제 트리와 focused rerun 기준으로 truthful한지 다시 확인하고, 다음 Claude 실행 슬라이스를 same-family 다음 current-risk 하나로 고정하기 위해서입니다.
- zero-strong-slot family는 이번 `/work`로 35~39 service/browser/docs continuity가 닫혔고, 다음으로 가장 가까운 user-visible gap은 actual-search click-reload second-follow-up source-path continuity입니다.

## 핵심 변경
- 최신 `/work`가 적은 구현 범위를 재확인했고, `tests/test_web_app.py`, `e2e/tests/web-smoke.spec.mjs`, `README.md`, `docs/ACCEPTANCE_CRITERIA.md`, `docs/MILESTONES.md`에 scenario 37의 zero-strong-slot click-reload second-follow-up source-path continuity와 response-origin continuity가 실제로 반영돼 있음을 확인했습니다.
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_zero_strong_slot_entity_card_history_card_reload_second_follow_up_preserves_source_paths`를 다시 실행했고 `Ran 1 test in 0.072s`, `OK`를 확인했습니다.
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "entity-card zero-strong-slot 다시 불러오기 후 두 번째 follow-up 질문에서 response origin badge와 answer-mode badge가 drift하지 않습니다" --reporter=line` 재실행 결과 `1 passed (7.1s)`였습니다.
- `git diff --check -- tests/test_web_app.py e2e/tests/web-smoke.spec.mjs README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md`는 clean이었습니다.
- 추가 direct probe에서는 actual-search click-reload path의 reload, 첫 follow-up, 두 번째 follow-up 모두 `active_context.source_paths`에 `https://namu.wiki/w/%EB%B6%89%EC%9D%80%EC%82%AC%EB%A7%89`, `https://ko.wikipedia.org/wiki/%EB%B6%89%EC%9D%80%EC%82%AC%EB%A7%89`가 함께 유지됐습니다. 반면 현재 고정된 contract는 `tests/test_web_app.py`의 reload/첫 follow-up assertions, `e2e/tests/web-smoke.spec.mjs`의 scenarios 48/49, `README.md`/`docs/ACCEPTANCE_CRITERIA.md`/`docs/MILESTONES.md`의 48/49 설명까지만 닫혀 있어, 다음 Claude 실행 슬라이스를 `history-card entity-card actual-search reload second-follow-up source-path continuity tightening`으로 좁혀 `.pipeline/claude_handoff.md`를 갱신했습니다.

## 검증
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_zero_strong_slot_entity_card_history_card_reload_second_follow_up_preserves_source_paths`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "entity-card zero-strong-slot 다시 불러오기 후 두 번째 follow-up 질문에서 response origin badge와 answer-mode badge가 drift하지 않습니다" --reporter=line`
- `git diff --check -- tests/test_web_app.py e2e/tests/web-smoke.spec.mjs README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md`
- `python3 - <<'PY' ... actual-search click-reload second-follow-up source_paths direct probe ... PY`

## 남은 리스크
- zero-strong-slot entity-card family의 click-reload/natural-reload source-path continuity는 history-card 35/36, second-follow-up 37, natural-reload 38/39 기준으로 닫혔습니다.
- actual-search click-reload second-follow-up은 runtime truth가 이미 존재하지만, 현재 service/browser/docs contract는 reload와 첫 follow-up까지만 잠가 두어서 두 번째 follow-up source-path drift를 직접 막지 못합니다.
- 전체 Python 회귀와 `make e2e-test`는 이번 focused verification 범위라 다시 실행하지 않았습니다.
