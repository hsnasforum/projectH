## 변경 파일
- `verify/4/7/2026-04-07-entity-card-actual-entity-search-natural-reload-follow-up-response-origin-continuity-tightening-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest `/work`인 `work/4/7/2026-04-07-entity-card-actual-entity-search-natural-reload-follow-up-response-origin-continuity-tightening.md`가 실제로 actual entity-search natural-reload follow-up response-origin continuity를 서비스, 브라우저, 문서에서 truthful하게 닫았는지 다시 확인해야 했습니다.
- 직전 same-day `/verify`가 actual entity-search natural-reload follow-up response-origin continuity를 다음 slice로 고정했으므로, 이번 round의 진위와 그 뒤의 exact next slice를 다시 좁혀야 했습니다.

## 핵심 변경
- latest `/work`의 구현·문서·focused rerun 주장은 truthful했습니다. `tests/test_web_app.py:15770-15834`에는 `test_handle_chat_actual_entity_search_natural_reload_follow_up_preserves_response_origin`가 실제로 추가되어 있었고, actual entity search 이후 자연어 reload(`방금 검색한 결과 다시 보여줘`)와 `load_web_search_record_id + user_text` follow-up 뒤에도 `response_origin`의 `answer_mode`, `verification_label`, `source_roles`가 drift하지 않는지를 직접 잠그고 있었습니다.
- 브라우저 smoke도 current tree와 맞았습니다. `e2e/tests/web-smoke.spec.mjs:4226-4276`에는 `entity-card 붉은사막 자연어 reload 후 follow-up에서 response origin badge와 answer-mode badge가 drift하지 않습니다` scenario가 실제로 있었고, pre-seeded record를 click reload로 세션에 등록한 뒤 자연어 reload와 follow-up을 거쳐 `WEB`, `설명 카드`, `설명형 단일 출처`, `백과 기반`을 직접 확인하고 있었습니다.
- 문서 sync도 맞았습니다. `README.md:157`, `docs/ACCEPTANCE_CRITERIA.md:1366`, `docs/MILESTONES.md:75`, `docs/TASK_BACKLOG.md:64`, `docs/NEXT_STEPS.md:16`이 scenario `45` 기준으로 정렬돼 있었고, `rg -n '^test\\(' e2e/tests/web-smoke.spec.mjs | wc -l` 결과도 `45`였습니다. `git diff --check -- tests/test_web_app.py e2e/tests/web-smoke.spec.mjs README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md`도 clean이었습니다.
- focused rerun도 다시 통과했습니다. `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_actual_entity_search_natural_reload_follow_up_preserves_response_origin`는 `OK (0.052s)`, `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "entity-card 붉은사막 자연어 reload 후 follow-up에서 response origin badge와 answer-mode badge가 drift하지 않습니다" --reporter=line`는 `1 passed (6.5s)`였습니다.
- 다만 `work/4/7/2026-04-07-entity-card-actual-entity-search-natural-reload-follow-up-response-origin-continuity-tightening.md:35-52`의 family 종결 선언은 current tree 기준으로는 과장입니다. 이는 현재 트리에서의 추론입니다. `tests/test_web_app.py:8746-8804`와 `e2e/tests/web-smoke.spec.mjs:3685-3779`는 actual entity-search natural-reload exact-field만 잠그고 있고, actual entity-search natural-reload source-path continuity에 해당하는 service/browser/doc match는 검색되지 않았습니다. `rg -n "붉은사막 자연어 reload.*source path|actual entity-search.*source path|actual_entity_search.*source_paths|entity-card 붉은사막.*context box|붉은사막.*context box" ...` 결과도 dual-probe 변형만 남고 generic actual-search match는 없었습니다.
- 다음 exact slice는 `entity-card actual-entity-search natural-reload source-path continuity tightening`으로 고정했습니다. 같은 entity-card natural-reload family에서 가장 좁은 남은 current-risk reduction은 generic actual-search path가 자연어 reload 뒤에도 source path를 context box와 `active_context.source_paths`에서 유지하는지를 서비스와 브라우저에서 직접 잠그는 것입니다. follow-up source-path보다 show-only source-path가 더 작은 선행 gap이므로 그 순서를 먼저 택했습니다.

## 검증
- `nl -ba work/4/7/2026-04-07-entity-card-actual-entity-search-natural-reload-follow-up-response-origin-continuity-tightening.md | sed -n '1,240p'`
- `nl -ba verify/4/7/2026-04-07-entity-card-dual-probe-natural-reload-follow-up-response-origin-continuity-tightening-verification.md | sed -n '1,240p'`
- `nl -ba tests/test_web_app.py | sed -n '15720,15820p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '4220,4345p'`
- `nl -ba README.md | sed -n '153,162p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '1362,1370p'`
- `nl -ba docs/MILESTONES.md | sed -n '71,77p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '60,66p'`
- `nl -ba docs/NEXT_STEPS.md | sed -n '15,17p'`
- `git diff --check -- tests/test_web_app.py e2e/tests/web-smoke.spec.mjs README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md`
  - clean
- `rg -n '^test\\(' e2e/tests/web-smoke.spec.mjs | wc -l`
  - `45`
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_actual_entity_search_natural_reload_follow_up_preserves_response_origin`
  - `OK (0.052s)`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "entity-card 붉은사막 자연어 reload 후 follow-up에서 response origin badge와 answer-mode badge가 drift하지 않습니다" --reporter=line`
  - `1 passed (6.5s)`
- `rg -n "붉은사막 자연어 reload.*source path|actual entity-search.*source path|actual_entity_search.*source_paths|entity-card 붉은사막.*context box|붉은사막.*context box" tests/test_web_app.py e2e/tests/web-smoke.spec.mjs README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md`
  - dual-probe 관련 match만 존재, generic actual-search match 없음
- `rg -n "actual_entity_search_natural_reload.*source|actual entity-search.*follow-up.*source|붉은사막 자연어 reload 후 follow-up.*source|붉은사막 검색 결과.*source path" tests/test_web_app.py e2e/tests/web-smoke.spec.mjs README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md`
  - `README.md:157`만 hit, source-path continuity implementation/doc match 없음
- `nl -ba tests/test_web_app.py | sed -n '8746,8804p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '3685,3779p'`

## 남은 리스크
- `make e2e-test`와 전체 Python 회귀는 이번 verification에서 재실행하지 않았습니다. 이번 round는 service 1건 + browser 1건 focused continuity tightening 검증이었고, shared helper 변경 신호는 보이지 않았습니다.
- actual entity-search natural-reload follow-up response-origin continuity는 now locked이지만, generic actual entity-search natural-reload source-path continuity는 아직 service/browser 모두 비어 있습니다. 따라서 `/work`의 family 종결 선언을 그대로 수용하기는 어렵습니다.
