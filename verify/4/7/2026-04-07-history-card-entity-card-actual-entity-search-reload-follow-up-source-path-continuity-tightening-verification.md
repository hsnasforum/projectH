## 변경 파일
- `verify/4/7/2026-04-07-history-card-entity-card-actual-entity-search-reload-follow-up-source-path-continuity-tightening-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest `/work`인 `work/4/7/2026-04-07-history-card-entity-card-actual-entity-search-reload-follow-up-source-path-continuity-tightening.md`가 history-card entity-card actual-search reload follow-up source-path continuity를 서비스, 브라우저, 문서에서 truthful하게 닫았는지 다시 확인해야 했습니다.
- 직전 same-day `/verify`인 `verify/4/7/2026-04-07-history-card-entity-card-actual-entity-search-reload-source-path-continuity-tightening-verification.md`가 이 follow-up source-path continuity slice를 다음 작업으로 고정했으므로, 이번 round가 그 gap을 실제로 닫았는지와 다음 exact slice를 다시 좁혀야 했습니다.

## 핵심 변경
- latest `/work`의 구현 주장은 current tree와 일치했습니다. `tests/test_web_app.py:15268`의 `test_handle_chat_entity_card_actual_search_follow_up_preserves_source_paths`는 `WebSearchStore`에 직접 저장한 actual-search record를 `load_web_search_record_id` reload 후 follow-up으로 다시 불렀을 때 `second["session"]["active_context"]["source_paths"]`에 `https://namu.wiki/w/%EB%B6%89%EC%9D%80%EC%82%AC%EB%A7%89`가 유지되는지를 잠그고 있었습니다.
- 브라우저 smoke도 current tree와 맞았습니다. `e2e/tests/web-smoke.spec.mjs:2792`의 `history-card entity-card 다시 불러오기 후 follow-up 질문에서 actual-search source path가 context box에 유지됩니다` scenario는 pre-seeded record를 `다시 불러오기` click 후 follow-up으로 이어가고 `#context-box`에 `namu.wiki`가 남아 있는지를 확인하고 있었습니다.
- 문서 sync 역시 current tree와 맞았습니다. `README.md:161`, `docs/ACCEPTANCE_CRITERIA.md:1370`, `docs/MILESTONES.md:79`, `docs/TASK_BACKLOG.md:68`, `docs/NEXT_STEPS.md:16`이 이 시나리오를 반영하고 있었고, `rg -n '^test\\(' e2e/tests/web-smoke.spec.mjs | wc -l` 결과도 `49`였습니다.
- focused rerun도 다시 통과했습니다. `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_entity_card_actual_search_follow_up_preserves_source_paths`는 `OK (0.035s)`, `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "history-card entity-card 다시 불러오기 후 follow-up 질문에서 actual-search source path가 context box에 유지됩니다" --reporter=line`는 `1 passed (6.5s)`였습니다. `git diff --check -- tests/test_web_app.py e2e/tests/web-smoke.spec.mjs README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md`도 clean이었습니다.
- 다만 latest `/work`의 `## 남은 리스크` 한 줄은 current tree와 다릅니다. 이는 현재 트리에서의 직접 확인입니다. `/work`는 generic actual-search fixture가 단일 `namu.wiki` URL만 emit한다고 적었지만, 제가 같은 fixture shape로 직접 돌린 ad-hoc Python probe에서는 reload와 follow-up 모두 `source_paths`에 `namu.wiki`와 `ko.wikipedia`가 함께 남았습니다. 즉 현재 구현상 다중 URL은 이미 보존되고 있지만, 서비스 테스트/브라우저 smoke/문서는 둘째 URL을 아직 명시적으로 잠그지 않습니다.
- 다음 exact slice는 `history-card entity-card actual-entity-search reload source-path plurality tightening`으로 좁혔습니다. same-family current-risk는 "동작이 없는 것"보다 "이미 있는 다중 증거 보존이 lock되지 않은 것"에 가깝습니다. current tree에서는 show-only reload와 follow-up 둘 다 service `source_paths`에 `namu.wiki`, `ko.wikipedia`가 들어가지만, existing service/browser/docs는 모두 `namu.wiki`만 긍정 단언합니다. `rg -n "ko\\.wikipedia.*source path|위키백과.*source path|ko\\.wikipedia.*source_paths|ko\\.wikipedia.*#context-box|context box.*ko\\.wikipedia" tests/test_web_app.py e2e/tests/web-smoke.spec.mjs README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md`는 no match였습니다. follow-up plurality보다 show-only plurality가 더 작은 선행 gap이므로 그 순서를 먼저 택했습니다.

## 검증
- `nl -ba work/4/7/2026-04-07-history-card-entity-card-actual-entity-search-reload-follow-up-source-path-continuity-tightening.md | sed -n '1,220p'`
- `nl -ba verify/4/7/2026-04-07-history-card-entity-card-actual-entity-search-reload-source-path-continuity-tightening-verification.md | sed -n '1,260p'`
- `nl -ba tests/test_web_app.py | sed -n '15240,15330p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '2778,2860p'`
- `nl -ba README.md | sed -n '156,165p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '1364,1374p'`
- `nl -ba docs/MILESTONES.md | sed -n '74,82p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '64,70p'`
- `nl -ba docs/NEXT_STEPS.md | sed -n '14,18p'`
- `rg -n '^test\\(' e2e/tests/web-smoke.spec.mjs | wc -l`
  - `49`
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_entity_card_actual_search_follow_up_preserves_source_paths`
  - `OK (0.035s)`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "history-card entity-card 다시 불러오기 후 follow-up 질문에서 actual-search source path가 context box에 유지됩니다" --reporter=line`
  - `1 passed (6.5s)`
- `git diff --check -- tests/test_web_app.py e2e/tests/web-smoke.spec.mjs README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md`
  - clean
- `python3 - <<'PY' ...`
  - `reload_source_paths= ['https://namu.wiki/w/%EB%B6%89%EC%9D%80%EC%82%AC%EB%A7%89', 'https://ko.wikipedia.org/wiki/%EB%B6%89%EC%9D%80%EC%82%AC%EB%A7%89']`
  - `followup_source_paths= ['https://namu.wiki/w/%EB%B6%89%EC%9D%80%EC%82%AC%EB%A7%89', 'https://ko.wikipedia.org/wiki/%EB%B6%89%EC%9D%80%EC%82%AC%EB%A7%89']`
- `rg -n "ko\\.wikipedia.*source path|위키백과.*source path|ko\\.wikipedia.*source_paths|ko\\.wikipedia.*#context-box|context box.*ko\\.wikipedia" tests/test_web_app.py e2e/tests/web-smoke.spec.mjs README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md`
  - no match

## 남은 리스크
- `make e2e-test`와 전체 Python 회귀는 이번 verification에서 재실행하지 않았습니다. 이번 round는 service 1건 + browser 1건 focused continuity tightening 검증이었고, shared helper 변경 신호는 보이지 않았습니다.
- history-card entity-card actual-search reload family의 `namu.wiki` continuity는 now locked이지만, same-family의 multi-source source-path plurality(`ko.wikipedia` 포함)는 서비스/브라우저/문서에서 아직 명시적으로 잠겨 있지 않습니다.
