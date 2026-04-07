# entity-card crimson-desert natural-reload follow-up actual-search response-origin docs wording clarification verification

날짜: 2026-04-07

## 변경 파일
- `verify/4/7/2026-04-07-entity-card-crimson-desert-natural-reload-follow-up-actual-search-response-origin-docs-wording-clarification-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest `/work`는 crimson natural-reload follow-up response-origin docs line 4곳에 `actual-search` qualifier를 추가해 same-family docs ambiguity를 닫았다고 주장했습니다. 이번 라운드에서는 그 docs-only change와 `남은 리스크 없음` 판단이 current tree와 맞는지 다시 확인할 필요가 있었습니다.
- rerun 결과 [README.md:157](/home/xpdlqj/code/projectH/README.md:157), [docs/MILESTONES.md:75](/home/xpdlqj/code/projectH/docs/MILESTONES.md:75), [docs/ACCEPTANCE_CRITERIA.md:1366](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md:1366), [docs/TASK_BACKLOG.md:64](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md:64)이 now actual-search follow-up response-origin line으로 정렬되어 있고, already-synced source-path/second-follow-up lines인 [README.md:159](/home/xpdlqj/code/projectH/README.md:159), [README.md:165](/home/xpdlqj/code/projectH/README.md:165), [docs/MILESTONES.md:77](/home/xpdlqj/code/projectH/docs/MILESTONES.md:77), [docs/MILESTONES.md:85](/home/xpdlqj/code/projectH/docs/MILESTONES.md:85), [docs/ACCEPTANCE_CRITERIA.md:1368](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md:1368), [docs/ACCEPTANCE_CRITERIA.md:1376](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md:1376), [docs/TASK_BACKLOG.md:66](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md:66), [docs/TASK_BACKLOG.md:74](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md:74), [docs/NEXT_STEPS.md:16](/home/xpdlqj/code/projectH/docs/NEXT_STEPS.md:16)과 함께 docs family closure를 이룹니다.
- 이 정리는 dedicated browser/service anchors인 [e2e/tests/web-smoke.spec.mjs:4990](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs:4990), [tests/test_web_app.py:16511](/home/xpdlqj/code/projectH/tests/test_web_app.py:16511), [e2e/tests/web-smoke.spec.mjs:4870](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs:4870), [tests/test_web_app.py:16443](/home/xpdlqj/code/projectH/tests/test_web_app.py:16443), [e2e/tests/web-smoke.spec.mjs:5045](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs:5045), [tests/test_web_app.py:16582](/home/xpdlqj/code/projectH/tests/test_web_app.py:16582)와도 맞았습니다.

## 핵심 변경
- latest `/work`를 truthful로 판정했습니다. docs-only wording correction, `git diff --check` clean, `rg -c '^test\\(' e2e/tests/web-smoke.spec.mjs = 75` 주장은 current tree와 일치했습니다.
- 다음 Claude 슬라이스를 `entity-card crimson-desert natural-reload actual-search browser-anchor naming clarification`으로 고정했습니다.

## 검증
- `sed -n '1,220p' AGENTS.md`
- `sed -n '1,220p' work/README.md`
- `sed -n '1,220p' verify/README.md`
- `sed -n '1,260p' .pipeline/README.md`
- `sed -n '1,220p' .agents/skills/round-handoff/SKILL.md`
- `sed -n '1,260p' work/4/7/2026-04-07-entity-card-crimson-desert-natural-reload-follow-up-actual-search-response-origin-docs-wording-clarification.md`
- `sed -n '1,260p' verify/4/7/2026-04-07-entity-card-crimson-desert-natural-reload-follow-up-second-follow-up-actual-search-docs-wording-clarification-verification.md`
- `git diff --check -- README.md docs/MILESTONES.md docs/ACCEPTANCE_CRITERIA.md docs/TASK_BACKLOG.md`
- `nl -ba README.md | sed -n '156,160p'`
- `nl -ba docs/MILESTONES.md | sed -n '74,78p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '1365,1369p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '63,67p'`
- `nl -ba docs/NEXT_STEPS.md | sed -n '16,16p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '4868,5105p'`
- `nl -ba tests/test_web_app.py | sed -n '16511,16581p'`
- `rg -n "entity-card 붉은사막 actual-search" README.md docs/MILESTONES.md docs/ACCEPTANCE_CRITERIA.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md e2e/tests/web-smoke.spec.mjs tests/test_web_app.py`
- `rg -n "entity-actual-search-natural-reload-followup-sp|entity-actual-natural-reload-followup-origin|entity-actual-natural-reload-second-followup-origin|test_handle_chat_actual_entity_search_natural_reload_follow_up_preserves_source_paths|test_handle_chat_actual_entity_search_natural_reload_follow_up_preserves_response_origin|test_handle_chat_actual_entity_search_natural_reload_second_follow_up_preserves_response_origin_and_source_paths" e2e/tests/web-smoke.spec.mjs tests/test_web_app.py`
- `rg -c '^test\\(' e2e/tests/web-smoke.spec.mjs`
- docs-only verification round이므로 `python3 -m unittest -v`, Playwright, `make e2e-test`는 재실행하지 않았습니다.

## 남은 리스크
- docs family 자체는 닫혔지만, same-family current-risk는 browser anchor naming ambiguity가 남는 점입니다. [e2e/tests/web-smoke.spec.mjs:4870](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs:4870), [e2e/tests/web-smoke.spec.mjs:4990](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs:4990), [e2e/tests/web-smoke.spec.mjs:5045](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs:5045)의 browser test title은 still generic `entity-card 붉은사막 자연어 reload 후 ...`로 보이는데, service anchors는 [tests/test_web_app.py:16443](/home/xpdlqj/code/projectH/tests/test_web_app.py:16443), [tests/test_web_app.py:16511](/home/xpdlqj/code/projectH/tests/test_web_app.py:16511), [tests/test_web_app.py:16582](/home/xpdlqj/code/projectH/tests/test_web_app.py:16582)처럼 actual entity-search branch를 직접 명시합니다.
- response-origin browser test의 session ids도 [e2e/tests/web-smoke.spec.mjs:4991](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs:4991), [e2e/tests/web-smoke.spec.mjs:5046](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs:5046)에서 `actual-search` spelling 없이 남아 있습니다. 따라서 다음 라운드는 runtime을 건드리지 않고 e2e browser anchor title/session-id/comment를 actual-search branch에 맞춰 정리하는 test-only clarification이 가장 작고 reviewable한 same-family current-risk reduction입니다.
