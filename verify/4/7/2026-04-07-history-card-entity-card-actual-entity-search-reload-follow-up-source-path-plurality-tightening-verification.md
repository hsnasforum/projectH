## 변경 파일
- `verify/4/7/2026-04-07-history-card-entity-card-actual-entity-search-reload-follow-up-source-path-plurality-tightening-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest `/work`인 `work/4/7/2026-04-07-history-card-entity-card-actual-entity-search-reload-follow-up-source-path-plurality-tightening.md`가 history-card entity-card actual-search click-reload 후 follow-up source-path plurality를 서비스, 브라우저, 문서에서 truthful하게 닫았는지 다시 확인해야 했습니다.
- same-day latest `/verify`인 `verify/4/7/2026-04-07-history-card-entity-card-actual-entity-search-reload-source-path-plurality-tightening-verification.md`가 다음 same-family risk를 follow-up plurality로 고정했으므로, 이번 round가 그 slice를 실제로 닫았는지와 다음 exact slice를 다시 좁혀야 했습니다.

## 핵심 변경
- latest `/work`의 구현 주장은 current tree와 일치했습니다. `tests/test_web_app.py:15274`의 `test_handle_chat_entity_card_actual_search_follow_up_preserves_source_paths`는 follow-up 후 `active_context.source_paths`에 `https://namu.wiki/w/%EB%B6%89%EC%9D%80%EC%82%AC%EB%A7%89`과 `https://ko.wikipedia.org/wiki/%EB%B6%89%EC%9D%80%EC%82%AC%EB%A7%89`가 모두 남는지를 직접 잠그고 있었습니다.
- 브라우저 smoke도 current tree와 맞았습니다. `e2e/tests/web-smoke.spec.mjs:2793`의 `history-card entity-card 다시 불러오기 후 follow-up 질문에서 actual-search source path가 context box에 유지됩니다` scenario는 `#context-box`에 `namu.wiki`와 `ko.wikipedia.org`가 함께 남는지를 확인하고 있었습니다.
- 문서 sync도 current tree와 일치했습니다. `README.md:161`, `docs/ACCEPTANCE_CRITERIA.md:1370`, `docs/MILESTONES.md:79`, `docs/TASK_BACKLOG.md:68`, `docs/NEXT_STEPS.md:16`이 follow-up plurality를 반영하고 있었고, `rg -n '^test\\(' e2e/tests/web-smoke.spec.mjs | wc -l` 결과도 `49`였습니다.
- focused rerun도 다시 통과했습니다. `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_entity_card_actual_search_follow_up_preserves_source_paths`는 `OK (0.034s)`, `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "history-card entity-card 다시 불러오기 후 follow-up 질문에서 actual-search source path가 context box에 유지됩니다" --reporter=line`는 `1 passed (6.4s)`였습니다. `git diff --check -- tests/test_web_app.py e2e/tests/web-smoke.spec.mjs README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md`도 clean이었습니다.
- 다음 exact slice는 `entity-card actual-entity-search natural-reload source-path plurality tightening`으로 좁혔습니다. 이는 현재 트리에서의 직접 확인입니다. `tests/test_web_app.py:8806-8857`와 `tests/test_web_app.py:15951-16011`은 natural-reload show-only와 follow-up 경로를 아직 `namu.wiki` continuity까지만 잠그고 있고, `e2e/tests/web-smoke.spec.mjs:4013-4108`와 `e2e/tests/web-smoke.spec.mjs:4546-4655`도 pre-seeded record에 두 URL이 있음에도 `#context-box`에서는 `namu.wiki`만 assert합니다. 문서도 `README.md:158-159`, `docs/ACCEPTANCE_CRITERIA.md:1367-1368`, `docs/MILESTONES.md:76-77`, `docs/TASK_BACKLOG.md:65-66`에서 여전히 `namu.wiki`만 적고 있습니다.
- 다만 ad-hoc probe에서는 actual entity-search의 natural reload와 follow-up 모두 `source_paths`에 `namu.wiki`와 `ko.wikipedia`가 함께 남았습니다. 따라서 다음 slice는 새 기능 추가가 아니라, 이미 있는 natural-reload plurality 보존을 service/browser/docs에서 명시적으로 lock하는 tightening입니다. show-only와 follow-up은 같은 파일과 verification 경로를 공유하고 구현 보존 상태도 같으므로, 이번에는 한 coherent slice로 묶는 편이 더 맞습니다.

## 검증
- `sed -n '1,240p' work/4/7/2026-04-07-history-card-entity-card-actual-entity-search-reload-follow-up-source-path-plurality-tightening.md`
- `sed -n '1,260p' verify/4/7/2026-04-07-history-card-entity-card-actual-entity-search-reload-source-path-plurality-tightening-verification.md`
- `nl -ba tests/test_web_app.py | sed -n '15274,15355p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '2793,2898p'`
- `nl -ba README.md | sed -n '158,163p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '1367,1372p'`
- `nl -ba docs/MILESTONES.md | sed -n '77,80p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '66,69p'`
- `nl -ba docs/NEXT_STEPS.md | sed -n '15,17p'`
- `rg -n '^test\\(' e2e/tests/web-smoke.spec.mjs | wc -l`
  - `49`
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_entity_card_actual_search_follow_up_preserves_source_paths`
  - `OK (0.034s)`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "history-card entity-card 다시 불러오기 후 follow-up 질문에서 actual-search source path가 context box에 유지됩니다" --reporter=line`
  - `1 passed (6.4s)`
- `git diff --check -- tests/test_web_app.py e2e/tests/web-smoke.spec.mjs README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md`
  - clean
- `python3 - <<'PY' ...`
  - `natural_reload_source_paths= ['https://namu.wiki/w/%EB%B6%89%EC%9D%80%EC%82%AC%EB%A7%89', 'https://ko.wikipedia.org/wiki/%EB%B6%89%EC%9D%80%EC%82%AC%EB%A7%89']`
  - `natural_followup_source_paths= ['https://namu.wiki/w/%EB%B6%89%EC%9D%80%EC%82%AC%EB%A7%89', 'https://ko.wikipedia.org/wiki/%EB%B6%89%EC%9D%80%EC%82%AC%EB%A7%89']`

## 남은 리스크
- `make e2e-test`와 전체 Python 회귀는 이번 verification에서 재실행하지 않았습니다. 이번 round는 click-reload follow-up plurality tightening 1건에 대한 focused rerun이었고, shared helper 변경 신호는 보이지 않았습니다.
- history-card click-reload actual-search plurality는 show-only + follow-up 모두 now locked입니다. 남은 같은 family risk는 natural-reload actual-search plurality가 service/browser/docs에서 아직 명시적으로 잠겨 있지 않다는 점입니다.
