# history-card entity-card actual-search click-reload initial + follow-up + second-follow-up acceptance exact-field wording clarification verification

날짜: 2026-04-08

## 변경 파일
- `verify/4/8/2026-04-08-history-card-entity-card-actual-search-click-reload-initial-follow-up-second-follow-up-acceptance-exact-field-wording-clarification-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest `/work`는 history-card entity-card actual-search click-reload initial/follow-up/second-follow-up acceptance 3줄을 exact-field wording으로 정렬했다고 보고했습니다. 이번 라운드에서는 그 docs-only closeout이 current tree 기준으로 실제 반영됐는지 다시 확인해야 했습니다.
- 동시에 same-day latest `/verify`와 current `.pipeline/claude_handoff.md`는 직전 dual-probe click-reload second-follow-up acceptance verification/handoff에 머물러 있었으므로, newer `/work` 기준으로 persistent truth와 다음 한 슬라이스를 다시 고정할 필요가 있었습니다.

## 핵심 변경
- latest `/work`는 truthful했습니다. current [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1371), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1372), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1373)은 모두 `/work` 주장대로 actual-search source-path plurality와 response-origin exact-field wording으로 반영돼 있습니다.
- `/work`가 주장한 docs-only verification도 재현됐습니다. `git diff -- docs/ACCEPTANCE_CRITERIA.md`는 empty였고, `git diff --check -- docs/ACCEPTANCE_CRITERIA.md`는 clean이었습니다.
- history-card entity-card actual-search click-reload acceptance family는 initial/follow-up/second-follow-up까지 이번 라운드로 닫혔습니다. 다음 슬라이스는 `history-card entity-card actual-search click-reload initial + follow-up milestone/backlog source-path plurality + response-origin exact-field wording clarification`으로 고정했습니다.
- 근거는 current planning docs [docs/MILESTONES.md](/home/xpdlqj/code/projectH/docs/MILESTONES.md#L80), [docs/MILESTONES.md](/home/xpdlqj/code/projectH/docs/MILESTONES.md#L81), [docs/TASK_BACKLOG.md](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L69), [docs/TASK_BACKLOG.md](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L70)이 아직 generic `source-path plurality + response-origin continuity` framing으로 남아 있는 반면, current root docs/test [README.md](/home/xpdlqj/code/projectH/README.md#L160), [README.md](/home/xpdlqj/code/projectH/README.md#L161), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1371), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1372), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L1856), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L2835)은 `namu.wiki`, `ko.wikipedia.org`, `WEB`, `설명 카드`, `설명형 다중 출처 합의`, `백과 기반` exact-field contract를 이미 직접 고정하기 때문입니다.
- initial/follow-up planning pair 4줄은 same file-set·same family·same verification axis이므로, 한 번에 exact-field wording으로 정렬하는 편이 더 작은 coherent slice입니다.

## 검증
- `sed -n '1,220p' .agents/skills/round-handoff/SKILL.md`
- `sed -n '1,220p' AGENTS.md`
- `sed -n '1,220p' work/README.md`
- `sed -n '1,220p' verify/README.md`
- `sed -n '1,220p' .pipeline/README.md`
- `sed -n '1,260p' work/4/8/2026-04-08-history-card-entity-card-actual-search-click-reload-initial-follow-up-second-follow-up-acceptance-exact-field-wording-clarification.md`
- `sed -n '1,280p' verify/4/8/2026-04-08-history-card-entity-card-dual-probe-click-reload-second-follow-up-acceptance-exact-field-wording-clarification-verification.md`
- `sed -n '1,260p' .pipeline/claude_handoff.md`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '1371,1376p'`
- `git diff -- docs/ACCEPTANCE_CRITERIA.md`
- `git diff --check -- docs/ACCEPTANCE_CRITERIA.md`
- `nl -ba docs/MILESTONES.md | sed -n '80,82p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '69,71p'`
- `nl -ba README.md | sed -n '160,162p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '1856,1874p;2835,2853p;2957,2975p'`
- `rg -n "history-card entity-card .*actual-search|response-origin continuity|exact-field drift-prevention|exact-field drift 없음" docs/MILESTONES.md docs/TASK_BACKLOG.md docs/ACCEPTANCE_CRITERIA.md README.md e2e/tests/web-smoke.spec.mjs`
- `test -f work/4/8/2026-04-08-history-card-entity-card-actual-search-click-reload-initial-follow-up-milestone-backlog-source-path-plurality-response-origin-exact-field-wording-clarification.md && echo actual_plan_pair_exists || echo actual_plan_pair_missing`
- `test -f work/4/8/2026-04-08-history-card-entity-card-actual-search-click-reload-initial-milestone-backlog-source-path-plurality-response-origin-exact-field-wording-clarification.md && echo actual_initial_plan_exists || echo actual_initial_plan_missing`
- `test -f work/4/8/2026-04-08-history-card-entity-card-actual-search-click-reload-follow-up-milestone-backlog-source-path-plurality-response-origin-exact-field-wording-clarification.md && echo actual_followup_plan_exists || echo actual_followup_plan_missing`
- `git status --short -- .pipeline/claude_handoff.md pipeline_gui/app.py pipeline_gui/view.py tests/test_pipeline_gui_app.py windows-launchers/README.md`
- Playwright rerun, `python3 -m unittest -v`, `make e2e-test`는 이번 docs-only verification 범위를 넘어가므로 재실행하지 않았습니다.

## 남은 리스크
- current planning lines [docs/MILESTONES.md](/home/xpdlqj/code/projectH/docs/MILESTONES.md#L80), [docs/MILESTONES.md](/home/xpdlqj/code/projectH/docs/MILESTONES.md#L81), [docs/TASK_BACKLOG.md](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L69), [docs/TASK_BACKLOG.md](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L70)은 아직 generic continuity wording으로 남아 있습니다.
- 이번 verification은 latest docs-only `/work` truth와 next slice selection까지만 다뤘으므로, browser/runtime health 자체는 다시 판정하지 않았습니다.
