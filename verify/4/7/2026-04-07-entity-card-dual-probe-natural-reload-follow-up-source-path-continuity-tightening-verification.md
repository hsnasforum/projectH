## 변경 파일
- `verify/4/7/2026-04-07-entity-card-dual-probe-natural-reload-follow-up-source-path-continuity-tightening-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest `/work`인 `work/4/7/2026-04-07-entity-card-dual-probe-natural-reload-follow-up-source-path-continuity-tightening.md`가 실제로 dual-probe natural-reload follow-up source-path continuity를 서비스, 브라우저, 문서에서 truthful하게 닫았는지 다시 확인해야 했습니다.
- 직전 same-day `/verify`가 `entity-card dual-probe browser natural-reload exact-field smoke tightening`을 닫고 이번 source-path follow-up round를 다음 slice로 고정했으므로, 이번 round의 진위와 다음 exact slice를 새로 확정할 필요가 있었습니다.

## 핵심 변경
- latest `/work`는 truthful했습니다. `tests/test_web_app.py:15565-15664`에는 `test_handle_chat_dual_probe_natural_reload_follow_up_preserves_source_paths`가 실제로 추가되어 있었고, dual-probe entity search 이후 자연어 reload(`방금 검색한 결과 다시 보여줘`)와 `load_web_search_record_id + user_text` follow-up 뒤에도 `active_context.source_paths`에 `pearlabyss.com/ko-KR/Board/Detail?_boardNo=200`, `...300` 두 URL이 모두 남는지를 직접 잠그고 있었습니다.
- 브라우저 smoke도 current tree와 맞았습니다. `e2e/tests/web-smoke.spec.mjs:4035-4162`에는 `entity-card dual-probe 자연어 reload 후 follow-up에서 source path가 context box에 유지됩니다` scenario가 실제로 있었고, pre-seeded record를 click reload로 세션에 등록한 뒤 자연어 reload와 follow-up을 거쳐 `#context-box`에 두 probe URL이 유지되는지를 확인하고 있었습니다.
- 문서 sync도 맞았습니다. `README.md:155`, `docs/ACCEPTANCE_CRITERIA.md:1364`, `docs/MILESTONES.md:73`, `docs/TASK_BACKLOG.md:62`, `docs/NEXT_STEPS.md:16`이 scenario `43` 기준으로 정렬돼 있었고, `rg -n '^test\\(' e2e/tests/web-smoke.spec.mjs | wc -l` 결과도 `43`이었습니다. `git diff --check -- tests/test_web_app.py e2e/tests/web-smoke.spec.mjs README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md`도 clean이었습니다.
- focused rerun도 다시 통과했습니다. `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_dual_probe_natural_reload_follow_up_preserves_source_paths`는 `OK (0.066s)`, `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "entity-card dual-probe 자연어 reload 후 follow-up에서 source path가 context box에 유지됩니다" --reporter=line`는 `1 passed (6.5s)`였습니다.
- 다음 exact slice는 `entity-card dual-probe natural-reload follow-up response-origin continuity tightening`으로 고정했습니다. 이 판단은 current tree 기준 추론입니다. generic entity-card follow-up response-origin continuity는 `tests/test_web_app.py:14840-14920`와 `e2e/tests/web-smoke.spec.mjs:1332-1445`에 있고, zero-strong-slot natural-reload follow-up response-origin continuity도 `tests/test_web_app.py:15489-15564`와 `e2e/tests/web-smoke.spec.mjs:3568-3683`에 이미 있습니다. 반면 dual-probe natural-reload follow-up response-origin continuity는 서비스, 브라우저, 문서 어디에도 현재 매치가 없었습니다. 따라서 같은 family의 가장 좁은 current-risk reduction은 follow-up 단계에서도 `WEB` badge, `설명 카드` answer-mode badge, `설명형 단일 출처`, `백과 기반`이 drift하지 않는지를 직접 잠그는 것입니다.

## 검증
- `nl -ba work/4/7/2026-04-07-entity-card-dual-probe-natural-reload-follow-up-source-path-continuity-tightening.md | sed -n '1,240p'`
- `nl -ba tests/test_web_app.py | sed -n '15520,15690p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '4028,4170p'`
- `nl -ba README.md | sed -n '148,158p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '1358,1368p'`
- `nl -ba docs/MILESTONES.md | sed -n '67,76p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '56,65p'`
- `nl -ba docs/NEXT_STEPS.md | sed -n '14,18p'`
- `git diff --check -- tests/test_web_app.py e2e/tests/web-smoke.spec.mjs README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md`
  - clean
- `rg -n '^test\\(' e2e/tests/web-smoke.spec.mjs | wc -l`
  - `43`
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_dual_probe_natural_reload_follow_up_preserves_source_paths`
  - `OK (0.066s)`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "entity-card dual-probe 자연어 reload 후 follow-up에서 source path가 context box에 유지됩니다" --reporter=line`
  - `1 passed (6.5s)`
- `rg -n "dual-probe.*natural.*follow.*response_origin|dual-probe.*natural.*follow.*response origin|dual-probe.*natural.*follow.*answer_mode|dual-probe.*natural.*follow.*verification_label|dual-probe.*natural.*follow.*source_roles|자연어 reload 후 follow-up.*dual-probe.*response|entity-card dual-probe 자연어 reload 후 follow-up.*response" tests/test_web_app.py e2e/tests/web-smoke.spec.mjs README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md`
  - no matches
- `nl -ba tests/test_web_app.py | sed -n '14840,14920p'`
- `nl -ba tests/test_web_app.py | sed -n '15489,15565p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '1328,1445p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '3568,3684p'`

## 남은 리스크
- `make e2e-test`와 전체 Python 회귀는 이번 verification에서 재실행하지 않았습니다. 이번 round는 service 1건 + browser 1건 focused continuity tightening 검증이었고, shared helper 변경 신호는 보이지 않았습니다.
- dual-probe natural-reload follow-up 경로에서 source-path continuity는 now locked이지만, response-origin continuity는 아직 service/browser 모두 비어 있어 follow-up 단계의 origin-detail drift 리스크가 남아 있습니다.
