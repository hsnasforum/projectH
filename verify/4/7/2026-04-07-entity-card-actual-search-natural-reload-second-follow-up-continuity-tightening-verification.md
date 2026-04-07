## 변경 파일
- `verify/4/7/2026-04-07-entity-card-actual-search-natural-reload-second-follow-up-continuity-tightening-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work`의 actual-search natural-reload second-follow-up continuity 주장이 실제 트리와 focused rerun 기준으로 truthful한지 다시 확인하고, entity-card family가 닫힌 뒤 같은 web-history continuity 축에서 다음 한 슬라이스를 좁히기 위해서입니다.
- 자동 handoff는 `needs_operator`로 비우지 않고, current MVP에서 바로 보이는 reload/follow-up continuity gap 중 가장 가까운 same-family slice 하나로 고정해야 합니다.

## 핵심 변경
- 최신 `/work`가 적은 구현 범위를 재확인했고, `tests/test_web_app.py`, `e2e/tests/web-smoke.spec.mjs`, `README.md`, `docs/ACCEPTANCE_CRITERIA.md`, `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md`, `docs/NEXT_STEPS.md`에 actual-search natural-reload second-follow-up contract가 실제로 반영돼 있음을 확인했습니다. 새 service test, 새 browser scenario 53, smoke scenario count `53`, backlog/next-steps 동기화까지 현재 트리와 맞았습니다.
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_actual_entity_search_natural_reload_second_follow_up_preserves_response_origin_and_source_paths`를 다시 실행했고 `Ran 1 test in 0.073s`, `OK`를 확인했습니다.
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "entity-card 붉은사막 자연어 reload 후 두 번째 follow-up에서 response origin badge와 answer-mode badge가 drift하지 않습니다" --reporter=line` 재실행 결과 `1 passed (7.2s)`였습니다.
- `git diff --check -- tests/test_web_app.py e2e/tests/web-smoke.spec.mjs README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md`는 clean이었습니다.
- 추가 direct probe와 coverage grep에서 entity-card second-follow-up family는 현재 트리 기준으로 모두 닫혀 있음을 확인했습니다. README 50~53, acceptance 1371~1374, e2e 2940/3063/4817/5064까지 second-follow-up contract가 있고, `/work`의 범위 주장과 충돌하는 남은 entity-card gap은 보이지 않았습니다.
- 다음 슬라이스를 좁히기 위해 latest-update second-follow-up을 mixed-source, single-source, news-only 세 갈래로 직접 probe했더니 모두 runtime에서는 `WEB` badge와 stored `answer_mode`/`verification_label`/`source_roles`, 그리고 대응 `source_paths`를 유지했습니다. 그중 mixed-source는 `store.steampowered.com` + `yna.co.kr` source-path plurality와 `공식+기사 교차 확인`, `보조 기사` · `공식 기반` response-origin을 함께 갖는 가장 넓은 latest-update branch이고, 현재 explicit contract도 `tests/test_web_app.py:15069`, `tests/test_web_app.py:15585`, `e2e/tests/web-smoke.spec.mjs:1449`, `e2e/tests/web-smoke.spec.mjs:3263`, `README.md:132`, `README.md:144`, `docs/ACCEPTANCE_CRITERIA.md:1341`, `docs/ACCEPTANCE_CRITERIA.md:1353`, `docs/MILESTONES.md:50`, `docs/MILESTONES.md:62`, `docs/TASK_BACKLOG.md:51`의 first follow-up까지만 닫혀 있습니다.
- 그래서 다음 Claude 실행 슬라이스를 `history-card latest-update mixed-source reload second-follow-up continuity tightening`으로 좁혀 `.pipeline/claude_handoff.md`를 갱신했습니다.

## 검증
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_actual_entity_search_natural_reload_second_follow_up_preserves_response_origin_and_source_paths`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "entity-card 붉은사막 자연어 reload 후 두 번째 follow-up에서 response origin badge와 answer-mode badge가 drift하지 않습니다" --reporter=line`
- `git diff --check -- tests/test_web_app.py e2e/tests/web-smoke.spec.mjs README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md`
- `rg -n "second-follow-up|두 번째 follow-up" README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md e2e/tests/web-smoke.spec.mjs`
- `rg -n "test_handle_chat_.*latest_update.*follow_up|test_handle_chat_.*latest_update.*exact_fields|mixed_source|single_source|news_only" tests/test_web_app.py`
- `python3 - <<'PY' ... latest-update mixed-source/single-source/news-only reload -> first follow-up -> second follow-up direct probe ... PY`
- `git status --short`

## 남은 리스크
- actual-search natural-reload second-follow-up contract은 truthful하게 닫혔고, entity-card second-follow-up family도 현재 확인 범위에서는 남은 user-visible gap이 보이지 않습니다.
- latest-update family는 second-follow-up continuity가 아직 contract로 잠겨 있지 않습니다. 이번 probe상 mixed-source, single-source, news-only 모두 runtime truth는 안정적이지만, handoff는 micro-slice 남발 대신 mixed-source 한 갈래만 먼저 잠그도록 좁혔습니다.
- 전체 Python 회귀와 `make e2e-test`는 이번 focused verification 범위라 다시 실행하지 않았습니다.
