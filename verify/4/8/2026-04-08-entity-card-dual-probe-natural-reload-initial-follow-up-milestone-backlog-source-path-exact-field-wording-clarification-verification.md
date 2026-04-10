# entity-card dual-probe natural-reload initial + follow-up milestone/backlog source-path exact-field wording clarification verification

날짜: 2026-04-08

## 변경 파일
- `verify/4/8/2026-04-08-entity-card-dual-probe-natural-reload-initial-follow-up-milestone-backlog-source-path-exact-field-wording-clarification-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest `/work`는 entity-card dual-probe natural-reload initial/follow-up milestone/backlog source-path wording 4줄을 exact-field drift-prevention wording으로 정렬했다고 보고했습니다. 이번 라운드에서는 그 docs-only closeout이 current tree 기준으로 실제 반영됐는지 다시 확인해야 했습니다.
- 동시에 same-day latest `/verify`와 current `.pipeline/claude_handoff.md`는 직전 crimson-desert actual-search natural-reload follow-up milestone/backlog verification/handoff에 머물러 있었으므로, newer `/work` 기준으로 persistent truth와 다음 한 슬라이스를 다시 고정할 필요가 있었습니다.

## 핵심 변경
- latest `/work`는 truthful했습니다. current [docs/MILESTONES.md](/home/xpdlqj/code/projectH/docs/MILESTONES.md#L71), [docs/MILESTONES.md](/home/xpdlqj/code/projectH/docs/MILESTONES.md#L73), [docs/TASK_BACKLOG.md](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L60), [docs/TASK_BACKLOG.md](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L62)은 모두 `/work` 주장대로 `source-path exact-field drift-prevention` wording으로 반영돼 있습니다.
- `/work`가 주장한 docs-only verification도 재현됐습니다. `git diff -- docs/MILESTONES.md docs/TASK_BACKLOG.md`는 empty였고, `git diff --check -- docs/MILESTONES.md docs/TASK_BACKLOG.md`는 clean이었습니다.
- entity-card dual-probe natural-reload initial/follow-up planning pair는 이번 라운드로 닫혔습니다. 다음 슬라이스는 `entity-card dual-probe natural-reload second-follow-up acceptance exact-field wording clarification`으로 고정했습니다.
- 근거는 current acceptance line [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1375)이 아직 `response-origin drift 없음` generic phrasing으로 남아 있는 반면, current root docs/test/planning [README.md](/home/xpdlqj/code/projectH/README.md#L164), [docs/MILESTONES.md](/home/xpdlqj/code/projectH/docs/MILESTONES.md#L84), [docs/TASK_BACKLOG.md](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L73), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L4807)은 already exact-field contract를 직접 고정하기 때문입니다.
- 같은 acceptance family의 adjacent line [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1374)는 already `response-origin exact-field drift 없음` wording으로 정렬돼 있으므로, natural-reload second-follow-up line 1개만 정리하는 편이 same-family current-risk reduction 우선순위에 맞는 가장 작은 coherent slice입니다.

## 검증
- `sed -n '1,260p' AGENTS.md`
- `sed -n '1,260p' work/README.md`
- `sed -n '1,260p' verify/README.md`
- `sed -n '1,260p' .pipeline/README.md`
- `sed -n '1,260p' work/4/8/2026-04-08-entity-card-dual-probe-natural-reload-initial-follow-up-milestone-backlog-source-path-exact-field-wording-clarification.md`
- `sed -n '1,260p' verify/4/8/2026-04-08-entity-card-crimson-desert-actual-search-natural-reload-follow-up-milestone-backlog-source-path-response-origin-exact-field-wording-clarification-verification.md`
- `sed -n '1,260p' .pipeline/claude_handoff.md`
- `sed -n '1,220p' .agents/skills/round-handoff/SKILL.md`
- `test -f docs/NEXT_STEPS.md && sed -n '1,220p' docs/NEXT_STEPS.md || echo docs_NEXT_STEPS_missing`
- `nl -ba docs/MILESTONES.md | sed -n '68,79p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '57,68p'`
- `nl -ba README.md | sed -n '150,160p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '1359,1369p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '4370,4625p'`
- `git diff -- docs/MILESTONES.md docs/TASK_BACKLOG.md`
- `git diff --check -- docs/MILESTONES.md docs/TASK_BACKLOG.md`
- `rg -n "dual-probe|pearlabyss\\.com/ko-KR/Board/Detail\\?_boardNo=200|pearlabyss\\.com/ko-KR/Board/Detail\\?_boardNo=300" docs/MILESTONES.md docs/TASK_BACKLOG.md README.md docs/ACCEPTANCE_CRITERIA.md e2e/tests/web-smoke.spec.mjs`
- `find work/4/8 -maxdepth 1 -type f | sort | rg "dual-probe|crimson-desert|zero-strong-slot|actual-search|natural-reload"`
- `git status --short -- .pipeline/claude_handoff.md pipeline_gui/app.py pipeline_gui/view.py tests/test_pipeline_gui_app.py windows-launchers/README.md`
- `nl -ba README.md | sed -n '161,165p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '1371,1376p'`
- `nl -ba docs/MILESTONES.md | sed -n '82,85p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '71,74p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '4807,4880p'`
- `test -f work/4/8/2026-04-08-entity-card-dual-probe-natural-reload-second-follow-up-acceptance-exact-field-wording-clarification.md && echo dual_nat_second_followup_acceptance_exists || echo dual_nat_second_followup_acceptance_missing`
- `git status --short -- .pipeline/claude_handoff.md verify/4/8/2026-04-08-entity-card-dual-probe-natural-reload-initial-follow-up-milestone-backlog-source-path-exact-field-wording-clarification-verification.md`
- `git diff --check -- .pipeline/claude_handoff.md`
- `git diff --no-index --check /dev/null verify/4/8/2026-04-08-entity-card-dual-probe-natural-reload-initial-follow-up-milestone-backlog-source-path-exact-field-wording-clarification-verification.md`
- Playwright rerun, `python3 -m unittest -v`, `make e2e-test`는 이번 docs-only verification 범위를 넘어가므로 재실행하지 않았습니다.

## 남은 리스크
- current acceptance line [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1375)은 아직 generic `response-origin drift 없음` phrasing으로 남아 있습니다.
- 이번 verification은 latest docs-only `/work` truth와 next slice selection까지만 다뤘으므로, browser/runtime health 자체는 다시 판정하지 않았습니다.
