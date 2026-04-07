## 변경 파일
- `verify/4/7/2026-04-07-entity-card-actual-entity-search-natural-reload-follow-up-source-path-continuity-tightening-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest `/work`인 `work/4/7/2026-04-07-entity-card-actual-entity-search-natural-reload-follow-up-source-path-continuity-tightening.md`가 actual entity-search natural-reload follow-up source-path continuity를 서비스, 브라우저, 문서에서 truthful하게 닫았는지 다시 확인해야 했습니다.
- 직전 same-day `/verify`인 `verify/4/7/2026-04-07-entity-card-actual-entity-search-natural-reload-source-path-continuity-tightening-verification.md`가 이 follow-up source-path continuity slice를 다음 작업으로 고정했으므로, 이번 round가 그 gap을 실제로 닫았는지와 다음 exact slice를 다시 좁혀야 했습니다.

## 핵심 변경
- latest `/work`의 구현 주장은 current tree와 일치했습니다. `tests/test_web_app.py:15823`의 `test_handle_chat_actual_entity_search_natural_reload_follow_up_preserves_source_paths`는 actual entity search 후 자연어 reload와 follow-up(`이 검색 결과 요약해줘` + `load_web_search_record_id`)를 거친 뒤 `third["session"]["active_context"]["source_paths"]`에 `https://namu.wiki/w/%EB%B6%89%EC%9D%80%EC%82%AC%EB%A7%89`가 유지되는지를 직접 잠그고 있었습니다.
- 브라우저 smoke도 current tree와 맞았습니다. `e2e/tests/web-smoke.spec.mjs:4331`의 `entity-card 붉은사막 자연어 reload 후 follow-up에서 source path가 context box에 유지됩니다` scenario는 pre-seeded entity-card record를 click reload로 세션에 등록한 뒤 자연어 reload와 follow-up을 보내고 `#context-box`에 `namu.wiki`가 남아 있는지를 확인하고 있었습니다.
- 문서 sync 역시 current tree와 맞았습니다. `README.md:159`, `docs/ACCEPTANCE_CRITERIA.md:1368`, `docs/MILESTONES.md:77`, `docs/TASK_BACKLOG.md:66`, `docs/NEXT_STEPS.md:16`이 이 시나리오를 반영하고 있었고, `rg -n '^test\\(' e2e/tests/web-smoke.spec.mjs | wc -l` 결과도 `47`이었습니다.
- focused rerun도 다시 통과했습니다. `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_actual_entity_search_natural_reload_follow_up_preserves_source_paths`는 `OK (0.047s)`, `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "entity-card 붉은사막 자연어 reload 후 follow-up에서 source path가 context box에 유지됩니다" --reporter=line`는 `1 passed (6.5s)`였습니다. `git diff --check -- tests/test_web_app.py e2e/tests/web-smoke.spec.mjs README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md`도 clean이었습니다.
- actual entity-search natural-reload family는 current tree 기준으로 이제 닫혔습니다. 이는 현재 트리에서의 추론입니다. natural-reload exact-field, show-only source-path, follow-up source-path, follow-up response-origin에 해당하는 service/browser/doc match가 각각 `tests/test_web_app.py:8746`, `tests/test_web_app.py:8799`, `tests/test_web_app.py:15823`, `tests/test_web_app.py:15885`와 `e2e/tests/web-smoke.spec.mjs:3685`, `e2e/tests/web-smoke.spec.mjs:3798`, `e2e/tests/web-smoke.spec.mjs:4331`, `e2e/tests/web-smoke.spec.mjs:4450`, 그리고 `README.md:152-159`, `docs/ACCEPTANCE_CRITERIA.md:1361-1368`, `docs/MILESTONES.md:70-77`에 정렬돼 있었습니다.
- 다음 exact slice는 `history-card entity-card actual-entity-search reload source-path continuity tightening`으로 좁혔습니다. current tree에는 generic entity-card reload의 adjacent coverage가 이미 있습니다. `tests/test_web_app.py:14603`, `tests/test_web_app.py:14703`, `tests/test_web_app.py:14797`, `tests/test_web_app.py:14893`는 entity-card `load_web_search_record_id` reload/follow-up에서 claim coverage, stored summary, stored response origin continuity를 잠그고 있고, `e2e/tests/web-smoke.spec.mjs:1112`는 generic history-card reload response-origin badge continuity를 브라우저에서 확인합니다. 반면 generic actual-search click reload에서 `source_paths`와 context box의 `namu.wiki` continuity를 잠그는 service/browser/doc match는 검색되지 않았고, source-path continuity match는 dual-probe reload/follow-up 쪽만 존재했습니다. `rg -n "history-card entity-card .*source path|entity-card 검색 → load_web_search_record_id reload.*source_paths|history-card.*붉은사막.*context box|load_web_search_record_id.*namu\\.wiki" ...` 결과도 dual-probe entries만 반환했고, tests-only `rg -n "entity-card 검색 → load_web_search_record_id reload.*source_paths|actual_entity_search.*load_web_search_record.*source|load_web_search_record_id.*source_paths.*namu|entity-card.*reload.*source_paths" tests/test_web_app.py`는 no match였습니다. 따라서 click reload show-only source-path이 follow-up source-path보다 더 작은 선행 gap이므로 그 순서를 먼저 택했습니다.

## 검증
- `nl -ba work/4/7/2026-04-07-entity-card-actual-entity-search-natural-reload-follow-up-source-path-continuity-tightening.md | sed -n '1,220p'`
- `nl -ba verify/4/7/2026-04-07-entity-card-actual-entity-search-natural-reload-source-path-continuity-tightening-verification.md | sed -n '1,260p'`
- `nl -ba tests/test_web_app.py | sed -n '15800,15895p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '4390,4485p'`
- `nl -ba README.md | sed -n '154,166p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '1362,1374p'`
- `nl -ba docs/MILESTONES.md | sed -n '71,81p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '60,69p'`
- `nl -ba docs/NEXT_STEPS.md | sed -n '14,18p'`
- `rg -n '^test\\(' e2e/tests/web-smoke.spec.mjs | wc -l`
  - `47`
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_actual_entity_search_natural_reload_follow_up_preserves_source_paths`
  - `OK (0.047s)`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "entity-card 붉은사막 자연어 reload 후 follow-up에서 source path가 context box에 유지됩니다" --reporter=line`
  - `1 passed (6.5s)`
- `git diff --check -- tests/test_web_app.py e2e/tests/web-smoke.spec.mjs README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md`
  - clean
- `rg -n "history-card entity-card .*source path|entity-card 검색 → load_web_search_record_id reload.*source_paths|history-card.*붉은사막.*context box|load_web_search_record_id.*namu\\.wiki" tests/test_web_app.py e2e/tests/web-smoke.spec.mjs README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md`
  - dual-probe reload/follow-up source-path continuity match만 존재
- `rg -n "entity-card 검색 → load_web_search_record_id reload.*source_paths|actual_entity_search.*load_web_search_record.*source|load_web_search_record_id.*source_paths.*namu|entity-card.*reload.*source_paths" tests/test_web_app.py`
  - no match

## 남은 리스크
- `make e2e-test`와 전체 Python 회귀는 이번 verification에서 재실행하지 않았습니다. 이번 round는 service 1건 + browser 1건 focused continuity tightening 검증이었고, shared helper 변경 신호는 보이지 않았습니다.
- actual entity-search natural-reload family는 now locked로 볼 수 있지만, adjacent history-card click reload generic actual-search source-path continuity는 아직 service/browser/doc 모두 비어 있습니다.
