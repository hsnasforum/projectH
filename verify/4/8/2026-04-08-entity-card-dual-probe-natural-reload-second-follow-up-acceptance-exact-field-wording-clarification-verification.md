# entity-card dual-probe natural-reload second-follow-up acceptance exact-field wording clarification verification

날짜: 2026-04-08

## 변경 파일
- `verify/4/8/2026-04-08-entity-card-dual-probe-natural-reload-second-follow-up-acceptance-exact-field-wording-clarification-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest `/work`는 entity-card dual-probe natural-reload second-follow-up acceptance wording 1줄을 exact-field wording으로 정렬했다고 보고했습니다. 이번 라운드에서는 그 docs-only closeout이 current tree 기준으로 실제 반영됐는지 다시 확인해야 했습니다.
- 동시에 same-day latest `/verify`와 current `.pipeline/claude_handoff.md`는 직전 dual-probe natural-reload initial/follow-up milestone/backlog verification/handoff에 머물러 있었으므로, newer `/work` 기준으로 persistent truth와 다음 한 슬라이스를 다시 고정할 필요가 있었습니다.

## 핵심 변경
- latest `/work`는 truthful했습니다. current [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1375)는 `/work` 주장대로 `response-origin exact-field drift 없음` wording으로 반영돼 있습니다.
- `/work`가 주장한 docs-only verification도 재현됐습니다. `git diff -- docs/ACCEPTANCE_CRITERIA.md`는 empty였고, `git diff --check -- docs/ACCEPTANCE_CRITERIA.md`는 clean이었습니다.
- entity-card dual-probe natural-reload second-follow-up acceptance line은 이번 라운드로 닫혔습니다. 다음 슬라이스는 `entity-card crimson-desert actual-search natural-reload second-follow-up acceptance exact-field wording clarification`으로 고정했습니다.
- 근거는 current acceptance line [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1376)이 아직 `response-origin drift 없음` generic phrasing으로 남아 있는 반면, current root docs/test/planning [README.md](/home/xpdlqj/code/projectH/README.md#L165), [docs/MILESTONES.md](/home/xpdlqj/code/projectH/docs/MILESTONES.md#L85), [docs/TASK_BACKLOG.md](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L74), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L5054)는 already exact-field contract를 직접 고정하기 때문입니다.
- 같은 acceptance family의 adjacent line [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1375)은 방금 exact-field wording으로 정렬됐으므로, same-family current-risk reduction 우선순위상 actual-search natural-reload second-follow-up line 1개만 정리하는 편이 가장 작은 coherent slice입니다.

## 검증
- `sed -n '1,260p' AGENTS.md`
- `sed -n '1,260p' work/README.md`
- `sed -n '1,260p' verify/README.md`
- `sed -n '1,260p' .pipeline/README.md`
- `sed -n '1,260p' .agents/skills/round-handoff/SKILL.md`
- `sed -n '1,260p' work/4/8/2026-04-08-entity-card-dual-probe-natural-reload-second-follow-up-acceptance-exact-field-wording-clarification.md`
- `sed -n '1,260p' verify/4/8/2026-04-08-entity-card-dual-probe-natural-reload-initial-follow-up-milestone-backlog-source-path-exact-field-wording-clarification-verification.md`
- `sed -n '1,260p' .pipeline/claude_handoff.md`
- `test -f docs/NEXT_STEPS.md && sed -n '1,220p' docs/NEXT_STEPS.md || echo docs_NEXT_STEPS_missing`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '1371,1378p'`
- `nl -ba README.md | sed -n '163,166p'`
- `nl -ba docs/MILESTONES.md | sed -n '83,86p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '72,75p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '4807,5025p'`
- `git diff -- docs/ACCEPTANCE_CRITERIA.md`
- `git diff --check -- docs/ACCEPTANCE_CRITERIA.md`
- `rg -n "response-origin drift 없음|response-origin exact-field drift 없음|dual-probe|actual-search" docs/ACCEPTANCE_CRITERIA.md README.md docs/MILESTONES.md docs/TASK_BACKLOG.md`
- `find work/4/8 -maxdepth 1 -type f | sort | rg "entity-card-crimson-desert-actual-search-natural-reload-second-follow-up-acceptance-exact-field-wording-clarification|entity-card-dual-probe-natural-reload-second-follow-up-acceptance-exact-field-wording-clarification|actual-search-natural-reload-second-follow-up"`
- `git status --short -- .pipeline/claude_handoff.md pipeline_gui/app.py pipeline_gui/view.py tests/test_pipeline_gui_app.py windows-launchers/README.md`
- `rg -n "actual-search.*두 번째 follow-up|actual-search.*second-follow-up|entity-card 붉은사막 actual-search" e2e/tests/web-smoke.spec.mjs`
- `test -f work/4/8/2026-04-08-entity-card-crimson-desert-actual-search-natural-reload-second-follow-up-acceptance-exact-field-wording-clarification.md && echo crimson_actual_nat_second_followup_acceptance_exists || echo crimson_actual_nat_second_followup_acceptance_missing`
- `git status --short -- .pipeline/claude_handoff.md verify/4/8/2026-04-08-entity-card-dual-probe-natural-reload-second-follow-up-acceptance-exact-field-wording-clarification-verification.md`
- `git diff --check -- .pipeline/claude_handoff.md`
- `git diff --no-index --check /dev/null verify/4/8/2026-04-08-entity-card-dual-probe-natural-reload-second-follow-up-acceptance-exact-field-wording-clarification-verification.md`
- Playwright rerun, `python3 -m unittest -v`, `make e2e-test`는 이번 docs-only verification 범위를 넘어가므로 재실행하지 않았습니다.

## 남은 리스크
- current acceptance line [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1376)은 아직 generic `response-origin drift 없음` phrasing으로 남아 있습니다.
- 이번 verification은 latest docs-only `/work` truth와 next slice selection까지만 다뤘으므로, browser/runtime health 자체는 다시 판정하지 않았습니다.
