# entity-card crimson-desert actual-search natural-reload follow-up milestone/backlog source-path + response-origin exact-field wording clarification verification

날짜: 2026-04-08

## 변경 파일
- `verify/4/8/2026-04-08-entity-card-crimson-desert-actual-search-natural-reload-follow-up-milestone-backlog-source-path-response-origin-exact-field-wording-clarification-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest `/work`는 entity-card `붉은사막` actual-search natural-reload follow-up milestone/backlog 2줄을 exact-field wording으로 정렬했다고 보고했습니다. 이번 라운드에서는 그 docs-only closeout이 current tree 기준으로 실제 반영됐는지 다시 확인해야 했습니다.
- 동시에 same-day latest `/verify`와 current `.pipeline/claude_handoff.md`는 직전 zero-strong-slot natural-reload follow-up verification/handoff에 머물러 있었으므로, newer `/work` 기준으로 persistent truth와 다음 한 슬라이스를 다시 고정할 필요가 있었습니다.

## 핵심 변경
- latest `/work`는 truthful했습니다. current [docs/MILESTONES.md](/home/xpdlqj/code/projectH/docs/MILESTONES.md#L75), [docs/TASK_BACKLOG.md](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L64)은 모두 `/work` 주장대로 `source-path + response-origin exact-field drift-prevention` wording으로 반영돼 있습니다.
- `/work`가 주장한 docs-only verification도 재현됐습니다. `git diff -- docs/MILESTONES.md docs/TASK_BACKLOG.md`는 empty였고, `git diff --check -- docs/MILESTONES.md docs/TASK_BACKLOG.md`는 clean이었습니다.
- entity-card `붉은사막` actual-search natural-reload follow-up planning pair는 이번 라운드로 닫혔습니다. 다음 슬라이스는 `entity-card dual-probe natural-reload initial + follow-up milestone/backlog source-path exact-field wording clarification`으로 고정했습니다.
- 근거는 current planning docs [docs/MILESTONES.md](/home/xpdlqj/code/projectH/docs/MILESTONES.md#L71), [docs/MILESTONES.md](/home/xpdlqj/code/projectH/docs/MILESTONES.md#L73), [docs/TASK_BACKLOG.md](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L60), [docs/TASK_BACKLOG.md](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L62)이 아직 generic `source-path continuity` framing으로 남아 있는 반면, current root docs/test [README.md](/home/xpdlqj/code/projectH/README.md#L153), [README.md](/home/xpdlqj/code/projectH/README.md#L155), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1362), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1364), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L4377), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L4615)은 `pearlabyss.com/ko-KR/Board/Detail?_boardNo=200`, `pearlabyss.com/ko-KR/Board/Detail?_boardNo=300` exact source path를 이미 직접 고정하기 때문입니다.
- 같은 family의 response-origin exact-field pair [docs/MILESTONES.md](/home/xpdlqj/code/projectH/docs/MILESTONES.md#L72), [docs/MILESTONES.md](/home/xpdlqj/code/projectH/docs/MILESTONES.md#L74), [docs/TASK_BACKLOG.md](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L61), [docs/TASK_BACKLOG.md](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L63)은 이미 정렬돼 있으므로, current-risk reduction 우선순위상 source-path planning 4줄만 정리하는 편이 더 작은 coherent slice입니다.

## 검증
- `sed -n '1,220p' AGENTS.md`
- `sed -n '1,220p' work/README.md`
- `sed -n '1,220p' verify/README.md`
- `sed -n '1,220p' .pipeline/README.md`
- `sed -n '1,220p' .agents/skills/round-handoff/SKILL.md`
- `sed -n '1,260p' work/4/8/2026-04-08-entity-card-crimson-desert-actual-search-natural-reload-follow-up-milestone-backlog-source-path-response-origin-exact-field-wording-clarification.md`
- `sed -n '1,260p' verify/4/8/2026-04-08-entity-card-zero-strong-slot-natural-reload-follow-up-milestone-backlog-exact-field-wording-clarification-verification.md`
- `sed -n '1,260p' .pipeline/claude_handoff.md`
- `test -f docs/NEXT_STEPS.md && sed -n '1,220p' docs/NEXT_STEPS.md || echo docs_NEXT_STEPS_missing`
- `nl -ba docs/MILESTONES.md | sed -n '71,85p'; nl -ba docs/TASK_BACKLOG.md | sed -n '60,74p'; nl -ba README.md | sed -n '153,166p'; nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '1362,1377p'; nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '4377,4825p;4879,5070p'`
- `git diff -- docs/MILESTONES.md docs/TASK_BACKLOG.md`
- `git diff --check -- docs/MILESTONES.md docs/TASK_BACKLOG.md`
- `test -f work/4/8/2026-04-08-entity-card-dual-probe-natural-reload-initial-follow-up-milestone-backlog-source-path-exact-field-wording-clarification.md && echo dual_nat_initial_followup_exists || echo dual_nat_initial_followup_missing; test -f work/4/8/2026-04-08-entity-card-dual-probe-natural-reload-initial-milestone-backlog-source-path-exact-field-wording-clarification.md && echo dual_nat_initial_exists || echo dual_nat_initial_missing; test -f work/4/8/2026-04-08-entity-card-dual-probe-natural-reload-follow-up-milestone-backlog-source-path-exact-field-wording-clarification.md && echo dual_nat_followup_exists || echo dual_nat_followup_missing; test -f work/4/8/2026-04-08-entity-card-crimson-desert-actual-search-natural-reload-second-follow-up-milestone-backlog-source-path-response-origin-exact-field-wording-clarification.md && echo crimson_nat_second_followup_exists || echo crimson_nat_second_followup_missing`
- `git status --short -- .pipeline/claude_handoff.md pipeline_gui/app.py pipeline_gui/view.py tests/test_pipeline_gui_app.py windows-launchers/README.md`
- Playwright rerun, `python3 -m unittest -v`, `make e2e-test`는 이번 docs-only verification 범위를 넘어가므로 재실행하지 않았습니다.

## 남은 리스크
- current planning lines [docs/MILESTONES.md](/home/xpdlqj/code/projectH/docs/MILESTONES.md#L71), [docs/MILESTONES.md](/home/xpdlqj/code/projectH/docs/MILESTONES.md#L73), [docs/TASK_BACKLOG.md](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L60), [docs/TASK_BACKLOG.md](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L62)은 아직 generic source-path continuity wording으로 남아 있습니다.
- 이번 verification은 latest docs-only `/work` truth와 next slice selection까지만 다뤘으므로, browser/runtime health 자체는 다시 판정하지 않았습니다.
