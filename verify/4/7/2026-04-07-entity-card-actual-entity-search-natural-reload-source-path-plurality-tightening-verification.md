## 변경 파일
- `verify/4/7/2026-04-07-entity-card-actual-entity-search-natural-reload-source-path-plurality-tightening-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest `/work`인 `work/4/7/2026-04-07-entity-card-actual-entity-search-natural-reload-source-path-plurality-tightening.md`가 actual entity-search natural-reload source-path plurality를 서비스, 브라우저, 문서에서 truthful하게 닫았는지 다시 확인해야 했습니다.
- same-day latest `/verify`인 `verify/4/7/2026-04-07-history-card-entity-card-actual-entity-search-reload-follow-up-source-path-plurality-tightening-verification.md`가 다음 same-family risk를 natural-reload plurality로 고정했으므로, 이번 round가 그 slice를 실제로 닫았는지와 다음 exact slice를 다시 좁혀야 했습니다.

## 핵심 변경
- latest `/work`의 구현 주장은 current tree와 일치했습니다. `tests/test_web_app.py:8806`의 `test_handle_chat_actual_entity_search_natural_reload_preserves_source_paths`와 `tests/test_web_app.py:15957`의 `test_handle_chat_actual_entity_search_natural_reload_follow_up_preserves_source_paths`는 natural reload show-only와 follow-up 모두 `active_context.source_paths`에 `https://namu.wiki/w/%EB%B6%89%EC%9D%80%EC%82%AC%EB%A7%89`과 `https://ko.wikipedia.org/wiki/%EB%B6%89%EC%9D%80%EC%82%AC%EB%A7%89`가 남는지를 직접 잠그고 있었습니다.
- 브라우저 smoke도 current tree와 맞았습니다. `e2e/tests/web-smoke.spec.mjs:4013`의 show-only natural-reload 시나리오와 `e2e/tests/web-smoke.spec.mjs:4547`의 follow-up natural-reload 시나리오는 `#context-box`에 `namu.wiki`와 `ko.wikipedia.org`가 함께 남는지를 확인하고 있었습니다.
- 문서 sync도 current tree와 일치했습니다. `README.md:158-159`, `docs/ACCEPTANCE_CRITERIA.md:1367-1368`, `docs/MILESTONES.md:76-77`, `docs/TASK_BACKLOG.md:65-66`, `docs/NEXT_STEPS.md:16`이 natural-reload plurality를 반영하고 있었고, `rg -n '^test\\(' e2e/tests/web-smoke.spec.mjs | wc -l` 결과도 `49`였습니다.
- focused rerun도 다시 통과했습니다. `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_actual_entity_search_natural_reload_preserves_source_paths tests.test_web_app.WebAppServiceTest.test_handle_chat_actual_entity_search_natural_reload_follow_up_preserves_source_paths`는 `OK (2 tests, 0.078s)`, `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "entity-card 붉은사막 자연어 reload에서 source path가 context box에 유지됩니다" --reporter=line`는 `1 passed (6.5s)`, `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "entity-card 붉은사막 자연어 reload 후 follow-up에서 source path가 context box에 유지됩니다" --reporter=line`는 `1 passed (6.6s)`였습니다. `git diff --check -- tests/test_web_app.py e2e/tests/web-smoke.spec.mjs README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md`도 clean이었습니다.
- 다음 exact slice는 `entity-card actual-entity-search natural-reload response-origin truth-sync tightening`으로 좁혔습니다. 이는 현재 트리에서의 직접 확인입니다. actual-search runtime을 직접 probe하면 initial/reload/follow-up `response_origin.verification_label`이 모두 `설명형 다중 출처 합의`였지만, natural-reload exact-field service test `tests/test_web_app.py:8865-8922`와 follow-up response-origin service test `tests/test_web_app.py:16025-16088`는 아직 one-result fixture만 써서 single-source path만 잠급니다. 브라우저 smoke `e2e/tests/web-smoke.spec.mjs:3900-4002`와 `e2e/tests/web-smoke.spec.mjs:4667-4714`도 two-result actual-search family 이름을 쓰면서 `response_origin.verification_label: "설명형 단일 출처"` pre-seeded record를 그대로 사용합니다. 문서도 `README.md:152`, `README.md:157`, `docs/ACCEPTANCE_CRITERIA.md:1361`, `docs/ACCEPTANCE_CRITERIA.md:1366`, `docs/MILESTONES.md:70`, `docs/MILESTONES.md:75`, `docs/TASK_BACKLOG.md:59`, `docs/TASK_BACKLOG.md:64`에서 아직 single-source wording을 유지합니다.
- 따라서 다음 slice는 새 동작 추가가 아니라, 이미 shipped된 actual-search multi-source agreement origin을 service/browser/docs에서 truthful하게 잠그는 truth-sync tightening입니다. show-only natural reload exact-field와 follow-up response-origin drift prevention은 같은 family, 같은 파일, 같은 verification 축을 공유하므로 한 coherent slice로 묶는 편이 더 맞습니다.

## 검증
- `sed -n '1,260p' work/4/7/2026-04-07-entity-card-actual-entity-search-natural-reload-source-path-plurality-tightening.md`
- `sed -n '1,260p' verify/4/7/2026-04-07-history-card-entity-card-actual-entity-search-reload-follow-up-source-path-plurality-tightening-verification.md`
- `nl -ba tests/test_web_app.py | sed -n '8800,8865p'`
- `nl -ba tests/test_web_app.py | sed -n '15948,16020p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '4010,4112p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '4544,4658p'`
- `nl -ba README.md | sed -n '156,161p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '1365,1370p'`
- `nl -ba docs/MILESTONES.md | sed -n '75,79p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '64,68p'`
- `nl -ba docs/NEXT_STEPS.md | sed -n '15,17p'`
- `rg -n '^test\\(' e2e/tests/web-smoke.spec.mjs | wc -l`
  - `49`
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_actual_entity_search_natural_reload_preserves_source_paths tests.test_web_app.WebAppServiceTest.test_handle_chat_actual_entity_search_natural_reload_follow_up_preserves_source_paths`
  - `OK (2 tests, 0.078s)`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "entity-card 붉은사막 자연어 reload에서 source path가 context box에 유지됩니다" --reporter=line`
  - `1 passed (6.5s)`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "entity-card 붉은사막 자연어 reload 후 follow-up에서 source path가 context box에 유지됩니다" --reporter=line`
  - `1 passed (6.6s)`
- `git diff --check -- tests/test_web_app.py e2e/tests/web-smoke.spec.mjs README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md`
  - clean
- `python3 - <<'PY' ...`
  - `initial_origin= {'provider': 'web', 'badge': 'WEB', 'label': '외부 웹 설명 카드', 'model': None, 'kind': 'assistant', 'answer_mode': 'entity_card', 'source_roles': ['백과 기반'], 'verification_label': '설명형 다중 출처 합의'}`
  - `reload_origin= {'provider': 'web', 'badge': 'WEB', 'label': '외부 웹 설명 카드', 'model': None, 'kind': 'assistant', 'answer_mode': 'entity_card', 'source_roles': ['백과 기반'], 'verification_label': '설명형 다중 출처 합의'}`
  - `followup_origin= {'provider': 'web', 'badge': 'WEB', 'label': '외부 웹 설명 카드', 'model': None, 'kind': 'assistant', 'answer_mode': 'entity_card', 'source_roles': ['백과 기반'], 'verification_label': '설명형 다중 출처 합의'}`
- `nl -ba tests/test_web_app.py | sed -n '8865,8923p'`
- `nl -ba tests/test_web_app.py | sed -n '16020,16088p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '3900,4012p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '4665,4740p'`

## 남은 리스크
- `make e2e-test`와 전체 Python 회귀는 이번 verification에서 재실행하지 않았습니다. 이번 round는 natural-reload source-path plurality tightening 1건에 대한 focused rerun이었고, shared helper 변경 신호는 보이지 않았습니다.
- actual-search source-path plurality는 click-reload + natural-reload 모두 show-only + follow-up에서 now locked입니다. 남은 같은 family risk는 natural-reload response-origin docs/smoke/service fixture가 actual multi-source agreement truth를 아직 명시적으로 잠그지 않는다는 점입니다.
