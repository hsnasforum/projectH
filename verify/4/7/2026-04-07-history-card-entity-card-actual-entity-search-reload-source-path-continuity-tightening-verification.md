## 변경 파일
- `verify/4/7/2026-04-07-history-card-entity-card-actual-entity-search-reload-source-path-continuity-tightening-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest `/work`인 `work/4/7/2026-04-07-history-card-entity-card-actual-entity-search-reload-source-path-continuity-tightening.md`가 history-card entity-card actual-search reload source-path continuity를 서비스, 브라우저, 문서에서 truthful하게 닫았는지 다시 확인해야 했습니다.
- 직전 same-day `/verify`인 `verify/4/7/2026-04-07-entity-card-actual-entity-search-natural-reload-follow-up-source-path-continuity-tightening-verification.md`가 이 click reload source-path continuity slice를 다음 작업으로 고정했으므로, 이번 round가 그 gap을 실제로 닫았는지와 다음 exact slice를 다시 좁혀야 했습니다.

## 핵심 변경
- latest `/work`의 구현 주장은 current tree와 일치했습니다. `tests/test_web_app.py:8567`의 `test_handle_chat_actual_entity_search_reload_preserves_active_context_source_paths`는 actual entity search 후 `load_web_search_record_id` reload에서 `result["session"]["active_context"]["source_paths"]`에 `https://namu.wiki/w/%EB%B6%89%EC%9D%80%EC%82%AC%EB%A7%89`가 유지되는지를 직접 잠그고 있었습니다.
- 브라우저 smoke도 current tree와 맞았습니다. `e2e/tests/web-smoke.spec.mjs:1840`의 `history-card entity-card 다시 불러오기 후 actual-search source path가 context box에 유지됩니다` scenario는 pre-seeded entity-card record를 `다시 불러오기` click으로 불러온 뒤 `#context-box`에 `namu.wiki`가 남아 있는지를 확인하고 있었습니다.
- 문서 sync 역시 current tree와 맞았습니다. `README.md:160`, `docs/ACCEPTANCE_CRITERIA.md:1369`, `docs/MILESTONES.md:78`, `docs/TASK_BACKLOG.md:67`, `docs/NEXT_STEPS.md:16`이 이 시나리오를 반영하고 있었고, `rg -n '^test\\(' e2e/tests/web-smoke.spec.mjs | wc -l` 결과도 `48`이었습니다.
- focused rerun도 다시 통과했습니다. `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_actual_entity_search_reload_preserves_active_context_source_paths`는 `OK (0.060s)`, `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "history-card entity-card 다시 불러오기 후 actual-search source path가 context box에 유지됩니다" --reporter=line`는 `1 passed (6.5s)`였습니다. `git diff --check -- tests/test_web_app.py e2e/tests/web-smoke.spec.mjs README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md`도 clean이었습니다. `/work`에 적힌 타깃과 범위는 맞았고, 제 rerun의 소요 시간만 약간 달랐습니다.
- 다음 exact slice는 `history-card entity-card actual-entity-search reload follow-up source-path continuity tightening`으로 좁혔습니다. 이는 current tree 기준 추론입니다. generic history-card entity-card reload family에는 인접 커버리지가 이미 있습니다. `tests/test_web_app.py:14947`는 `load_web_search_record_id + user_text` follow-up에서 stored response origin continuity를 잠그고, `e2e/tests/web-smoke.spec.mjs:1332`는 generic history-card reload follow-up response-origin badge continuity를 브라우저에서 확인합니다. 또한 dual-probe follow-up source-path continuity 패턴도 `tests/test_web_app.py:15268`과 `e2e/tests/web-smoke.spec.mjs:2792`에 이미 있습니다. 반면 generic actual-search click reload 뒤 follow-up에서 `source_paths`와 context box의 `namu.wiki` continuity를 잠그는 service/browser/doc match는 검색되지 않았습니다. `rg -n "history-card entity-card.*follow-up.*source path.*namu|다시 불러오기 후 follow-up.*namu\\.wiki|load_web_search_record_id.*user_text.*source_paths.*namu|actual_entity_search.*reload_follow_up.*source|history-card entity-card actual-search.*follow-up|follow-up 질문에서 actual-search source path" tests/test_web_app.py e2e/tests/web-smoke.spec.mjs README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md`는 no match였습니다.

## 검증
- `nl -ba work/4/7/2026-04-07-history-card-entity-card-actual-entity-search-reload-source-path-continuity-tightening.md | sed -n '1,220p'`
- `nl -ba verify/4/7/2026-04-07-entity-card-actual-entity-search-natural-reload-follow-up-source-path-continuity-tightening-verification.md | sed -n '1,260p'`
- `nl -ba tests/test_web_app.py | sed -n '8558,8588p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '1940,2025p'`
- `nl -ba README.md | sed -n '133,162p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '1342,1372p'`
- `nl -ba docs/MILESTONES.md | sed -n '52,80p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '58,68p'`
- `nl -ba docs/NEXT_STEPS.md | sed -n '14,18p'`
- `rg -n '^test\\(' e2e/tests/web-smoke.spec.mjs | wc -l`
  - `48`
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_actual_entity_search_reload_preserves_active_context_source_paths`
  - `OK (0.060s)`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "history-card entity-card 다시 불러오기 후 actual-search source path가 context box에 유지됩니다" --reporter=line`
  - `1 passed (6.5s)`
- `git diff --check -- tests/test_web_app.py e2e/tests/web-smoke.spec.mjs README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md`
  - clean
- `rg -n "history-card entity-card.*follow-up.*source path.*namu|다시 불러오기 후 follow-up.*namu\\.wiki|load_web_search_record_id.*user_text.*source_paths.*namu|actual_entity_search.*reload_follow_up.*source|history-card entity-card actual-search.*follow-up|follow-up 질문에서 actual-search source path" tests/test_web_app.py e2e/tests/web-smoke.spec.mjs README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md`
  - no match
- `rg -n "follow_up_preserves_source_paths|history-card entity-card 다시 불러오기 후 follow-up 질문에서 dual-probe source path가 context box에 유지됩니다|load_web_search_record_id \\+ user_text follow-up에서.*source_paths" tests/test_web_app.py e2e/tests/web-smoke.spec.mjs`
  - dual-probe 및 latest-update 계열 follow-up source-path continuity 패턴만 존재

## 남은 리스크
- `make e2e-test`와 전체 Python 회귀는 이번 verification에서 재실행하지 않았습니다. 이번 round는 service 1건 + browser 1건 focused continuity tightening 검증이었고, shared helper 변경 신호는 보이지 않았습니다.
- history-card entity-card actual-search reload show-only source-path continuity는 now locked이지만, same-family의 follow-up source-path continuity는 아직 service/browser/doc 모두 비어 있습니다.
