# history-card entity-card actual-search click-reload initial + follow-up milestone/backlog source-path plurality + response-origin exact-field wording clarification verification

날짜: 2026-04-08

## 변경 파일
- `verify/4/8/2026-04-08-history-card-entity-card-actual-search-click-reload-initial-follow-up-milestone-backlog-source-path-plurality-response-origin-exact-field-wording-clarification-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest `/work`는 history-card entity-card actual-search click-reload initial/follow-up milestone/backlog 4줄을 exact-field wording으로 정렬했다고 보고했습니다. 이번 라운드에서는 그 docs-only closeout이 current tree 기준으로 실제 반영됐는지 다시 확인해야 했습니다.
- 동시에 same-day latest `/verify`와 current `.pipeline/claude_handoff.md`는 직전 acceptance exact-field verification/handoff에 머물러 있었으므로, newer `/work` 기준으로 persistent truth와 다음 한 슬라이스를 다시 고정할 필요가 있었습니다.

## 핵심 변경
- latest `/work`는 truthful했습니다. current [docs/MILESTONES.md](/home/xpdlqj/code/projectH/docs/MILESTONES.md#L80), [docs/MILESTONES.md](/home/xpdlqj/code/projectH/docs/MILESTONES.md#L81), [docs/TASK_BACKLOG.md](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L69), [docs/TASK_BACKLOG.md](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L70)은 모두 `/work` 주장대로 actual-search source-path plurality와 response-origin exact-field wording으로 반영돼 있습니다.
- `/work`가 주장한 docs-only verification도 재현됐습니다. `git diff -- docs/MILESTONES.md docs/TASK_BACKLOG.md`는 empty였고, `git diff --check -- docs/MILESTONES.md docs/TASK_BACKLOG.md`는 clean이었습니다.
- history-card entity-card actual-search click-reload planning family의 initial/follow-up pair는 이번 라운드로 닫혔습니다. 다음 슬라이스는 `history-card entity-card zero-strong-slot click-reload initial + follow-up + second-follow-up milestone/backlog exact-field wording clarification`으로 고정했습니다.
- 근거는 current planning docs [docs/MILESTONES.md](/home/xpdlqj/code/projectH/docs/MILESTONES.md#L65), [docs/MILESTONES.md](/home/xpdlqj/code/projectH/docs/MILESTONES.md#L66), [docs/MILESTONES.md](/home/xpdlqj/code/projectH/docs/MILESTONES.md#L67), [docs/TASK_BACKLOG.md](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L54), [docs/TASK_BACKLOG.md](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L55), [docs/TASK_BACKLOG.md](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L56)이 아직 generic `response-origin + source-path continuity` framing으로 남아 있는 반면, current root docs/test [README.md](/home/xpdlqj/code/projectH/README.md#L147), [README.md](/home/xpdlqj/code/projectH/README.md#L148), [README.md](/home/xpdlqj/code/projectH/README.md#L149), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1356), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1357), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1358), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L3689), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L3791), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L3908)은 `WEB`, `설명 카드`, `설명형 단일 출처`, `백과 기반`, `namu.wiki`, `ko.wikipedia.org` exact-field contract를 이미 직접 고정하기 때문입니다.
- zero-strong-slot click-reload initial/follow-up/second-follow-up planning 6줄은 same file-set·same family·same verification axis이므로, 한 번에 exact-field wording으로 정렬하는 편이 더 작은 coherent slice입니다.

## 검증
- `sed -n '1,260p' work/4/8/2026-04-08-history-card-entity-card-actual-search-click-reload-initial-follow-up-milestone-backlog-source-path-plurality-response-origin-exact-field-wording-clarification.md`
- `sed -n '1,260p' verify/4/8/2026-04-08-history-card-entity-card-actual-search-click-reload-initial-follow-up-second-follow-up-acceptance-exact-field-wording-clarification-verification.md`
- `sed -n '1,260p' .pipeline/claude_handoff.md`
- `nl -ba docs/MILESTONES.md | sed -n '80,83p'; nl -ba docs/TASK_BACKLOG.md | sed -n '69,72p'; nl -ba README.md | sed -n '160,163p'; nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '1371,1374p'; nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '1856,1874p;2835,2853p;2957,2975p'`
- `git diff -- docs/MILESTONES.md docs/TASK_BACKLOG.md`
- `git diff --check -- docs/MILESTONES.md docs/TASK_BACKLOG.md`
- `rg -n "response-origin continuity|source-path plurality|exact-field drift-prevention|exact-field drift 없음|source path\\(|source-path" docs/MILESTONES.md docs/TASK_BACKLOG.md docs/ACCEPTANCE_CRITERIA.md README.md | sed -n '1,240p'`
- `nl -ba docs/MILESTONES.md | sed -n '65,69p'; nl -ba docs/TASK_BACKLOG.md | sed -n '54,58p'; nl -ba README.md | sed -n '147,150p'; nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '1356,1360p'; nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '3900,3985p;4080,4175p;4280,4375p'`
- `test -f work/4/8/2026-04-08-history-card-entity-card-zero-strong-slot-click-reload-initial-follow-up-second-follow-up-milestone-backlog-exact-field-wording-clarification.md && echo zero_slot_click_plan_exists || echo zero_slot_click_plan_missing`
- `rg -n "zero-strong-slot|설명형 단일 출처|백과 기반|source-path continuity|response-origin \\+ source-path continuity|verification-label" docs/MILESTONES.md docs/TASK_BACKLOG.md docs/ACCEPTANCE_CRITERIA.md README.md e2e/tests/web-smoke.spec.mjs | sed -n '1,220p'`
- `rg -n "history-card entity-card.*zero-strong-slot.*다시 불러오기|entity-card zero-strong-slot.*두 번째 follow-up|zero-strong-slot click-reload second-follow-up|설명형 단일 출처" e2e/tests/web-smoke.spec.mjs README.md docs/ACCEPTANCE_CRITERIA.md | sed -n '1,220p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '1108,1455p'; nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '3888,3925p'`
- `git status --short -- .pipeline/claude_handoff.md verify/4/8/2026-04-08-history-card-entity-card-actual-search-click-reload-initial-follow-up-milestone-backlog-source-path-plurality-response-origin-exact-field-wording-clarification-verification.md`
- `git diff --check -- .pipeline/claude_handoff.md`
- `git diff --no-index --check /dev/null verify/4/8/2026-04-08-history-card-entity-card-actual-search-click-reload-initial-follow-up-milestone-backlog-source-path-plurality-response-origin-exact-field-wording-clarification-verification.md`
- Playwright rerun, `python3 -m unittest -v`, `make e2e-test`는 이번 docs-only verification 범위를 넘어가므로 재실행하지 않았습니다.

## 남은 리스크
- current planning lines [docs/MILESTONES.md](/home/xpdlqj/code/projectH/docs/MILESTONES.md#L65), [docs/MILESTONES.md](/home/xpdlqj/code/projectH/docs/MILESTONES.md#L66), [docs/MILESTONES.md](/home/xpdlqj/code/projectH/docs/MILESTONES.md#L67), [docs/TASK_BACKLOG.md](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L54), [docs/TASK_BACKLOG.md](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L55), [docs/TASK_BACKLOG.md](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L56)은 아직 generic continuity wording으로 남아 있습니다.
- 이번 verification은 latest docs-only `/work` truth와 next slice selection까지만 다뤘으므로, browser/runtime health 자체는 다시 판정하지 않았습니다.
