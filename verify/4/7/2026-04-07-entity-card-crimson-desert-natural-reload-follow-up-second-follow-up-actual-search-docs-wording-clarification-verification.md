# entity-card crimson-desert natural-reload follow-up/second-follow-up actual-search docs wording clarification verification

날짜: 2026-04-07

## 변경 파일
- `verify/4/7/2026-04-07-entity-card-crimson-desert-natural-reload-follow-up-second-follow-up-actual-search-docs-wording-clarification-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest `/work`는 crimson natural-reload follow-up/second-follow-up continuity docs에 `actual-search` qualifier를 넣어 same-family ambiguity를 정리했고, 남은 리스크가 없다고 주장했습니다. 이번 라운드에서는 그 wording change 자체와 completion 서술이 current browser/service anchors와 모두 맞는지 다시 확인할 필요가 있었습니다.
- rerun 결과 [README.md:159](/home/xpdlqj/code/projectH/README.md:159), [README.md:165](/home/xpdlqj/code/projectH/README.md:165), [docs/MILESTONES.md:77](/home/xpdlqj/code/projectH/docs/MILESTONES.md:77), [docs/MILESTONES.md:85](/home/xpdlqj/code/projectH/docs/MILESTONES.md:85), [docs/ACCEPTANCE_CRITERIA.md:1368](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md:1368), [docs/ACCEPTANCE_CRITERIA.md:1376](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md:1376), [docs/TASK_BACKLOG.md:66](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md:66), [docs/TASK_BACKLOG.md:74](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md:74), [docs/NEXT_STEPS.md:16](/home/xpdlqj/code/projectH/docs/NEXT_STEPS.md:16)의 source-path plus second-follow-up continuity wording은 actual-search branch에 맞게 정렬되어 있었습니다.
- 다만 follow-up response-origin line은 아직 generic하게 남아 있습니다. [README.md:157](/home/xpdlqj/code/projectH/README.md:157), [docs/MILESTONES.md:75](/home/xpdlqj/code/projectH/docs/MILESTONES.md:75), [docs/ACCEPTANCE_CRITERIA.md:1366](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md:1366), [docs/TASK_BACKLOG.md:64](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md:64)은 still `entity-card 붉은사막 자연어 reload 후 follow-up` response-origin continuity를 generic line으로 적고 있지만, dedicated anchors인 [e2e/tests/web-smoke.spec.mjs:4990](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs:4990)와 [tests/test_web_app.py:16511](/home/xpdlqj/code/projectH/tests/test_web_app.py:16511)은 actual entity-search branch를 직접 가리킵니다.

## 핵심 변경
- latest `/work`를 partial-truth로 판정했습니다. source-path/second-follow-up wording clarification, `git diff --check` clean, `rg -c '^test\\(' e2e/tests/web-smoke.spec.mjs = 75` 주장은 current tree와 일치했습니다.
- 다만 `/work`의 `남은 리스크 없음`은 과장입니다. follow-up response-origin docs line 네 곳이 아직 generic해서, noisy-exclusion line과의 branch 구분이 완전히 닫히지 않았습니다.
- 다음 Claude 슬라이스를 `entity-card crimson-desert natural-reload follow-up actual-search response-origin docs wording clarification`으로 고정했습니다.

## 검증
- `sed -n '1,220p' AGENTS.md`
- `sed -n '1,220p' work/README.md`
- `sed -n '1,220p' verify/README.md`
- `sed -n '1,260p' .pipeline/README.md`
- `sed -n '1,220p' .agents/skills/round-handoff/SKILL.md`
- `sed -n '1,260p' work/4/7/2026-04-07-entity-card-crimson-desert-natural-reload-follow-up-second-follow-up-actual-search-docs-wording-clarification.md`
- `sed -n '1,260p' verify/4/7/2026-04-07-entity-card-crimson-desert-natural-reload-follow-up-second-follow-up-actual-search-docs-provenance-overstatement-correction-verification.md`
- `git diff --check -- README.md docs/NEXT_STEPS.md docs/MILESTONES.md docs/ACCEPTANCE_CRITERIA.md docs/TASK_BACKLOG.md`
- `nl -ba README.md | sed -n '156,166p'`
- `nl -ba docs/MILESTONES.md | sed -n '75,86p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '1366,1378p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '64,75p'`
- `nl -ba docs/NEXT_STEPS.md | sed -n '16,16p'`
- `rg -n "actual-search|entity-actual-search-natural-reload-followup-sp|test_handle_chat_actual_entity_search_natural_reload_follow_up_preserves_source_paths|test_handle_chat_actual_entity_search_natural_reload_second_follow_up_preserves_response_origin_and_source_paths|붉은사막 자연어 reload 후 follow-up|붉은사막 자연어 reload 후 두 번째 follow-up" README.md docs/MILESTONES.md docs/ACCEPTANCE_CRITERIA.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md e2e/tests/web-smoke.spec.mjs tests/test_web_app.py`
- `rg -c '^test\\(' e2e/tests/web-smoke.spec.mjs`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '4988,5043p'`
- `nl -ba tests/test_web_app.py | sed -n '16511,16581p'`
- `git status --short | sed -n '1,60p'`
- docs-only verification round이므로 `python3 -m unittest -v`, Playwright, `make e2e-test`는 재실행하지 않았습니다.

## 남은 리스크
- same-family smallest current-risk는 follow-up response-origin wording ambiguity입니다. [README.md:157](/home/xpdlqj/code/projectH/README.md:157), [docs/MILESTONES.md:75](/home/xpdlqj/code/projectH/docs/MILESTONES.md:75), [docs/ACCEPTANCE_CRITERIA.md:1366](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md:1366), [docs/TASK_BACKLOG.md:64](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md:64)이 아직 generic follow-up line을 유지해, 바로 옆 actual-search source-path line과 noisy-exclusion line 사이에서 branch 구분이 약합니다.
- dedicated anchors는 [e2e/tests/web-smoke.spec.mjs:4990](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs:4990), [tests/test_web_app.py:16511](/home/xpdlqj/code/projectH/tests/test_web_app.py:16511)처럼 actual entity-search response-origin continuity를 직접 적습니다. 따라서 다음 라운드는 runtime/tests를 건드리지 않고 위 네 문서의 follow-up response-origin line에만 `actual-search` qualifier를 넣는 docs-only clarification이 가장 작고 reviewable합니다.
