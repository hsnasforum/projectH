# history-card entity-card dual-probe click-reload follow-up milestone/backlog response-origin/source-path exact-field wording clarification verification

날짜: 2026-04-08

## 변경 파일
- `verify/4/8/2026-04-08-history-card-entity-card-dual-probe-click-reload-follow-up-milestone-backlog-response-origin-source-path-exact-field-wording-clarification-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest `/work`는 history-card entity-card dual-probe click-reload follow-up planning 2줄을 `response-origin/source-path exact-field drift-prevention` wording으로 정렬했다고 보고했습니다. 이번 라운드에서는 그 docs-only closeout이 current tree 기준으로 실제 반영됐는지 다시 확인해야 했습니다.
- 동시에 same-day latest `/verify`와 current `.pipeline/claude_handoff.md`는 직전 initial planning verification/handoff에 머물러 있었으므로, newer `/work` 기준으로 persistent truth와 다음 한 슬라이스를 다시 고정할 필요가 있었습니다.

## 핵심 변경
- latest `/work`는 truthful했습니다. current [docs/MILESTONES.md](/home/xpdlqj/code/projectH/docs/MILESTONES.md#L61), [docs/TASK_BACKLOG.md](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L50)는 모두 `/work` 주장대로 `source-path + response-origin exact-field drift-prevention` wording으로 반영돼 있습니다.
- `/work`가 주장한 docs-only verification도 재현됐습니다. `git diff -- docs/MILESTONES.md docs/TASK_BACKLOG.md`는 empty였고, `git diff --check -- docs/MILESTONES.md docs/TASK_BACKLOG.md`는 clean이었습니다. 추가로 `git diff -- README.md docs/ACCEPTANCE_CRITERIA.md e2e/tests/web-smoke.spec.mjs`도 empty였습니다.
- dual-probe click-reload planning family는 initial/follow-up pair까지 이번 라운드로 닫혔습니다. 다음 슬라이스는 `history-card entity-card dual-probe click-reload initial + follow-up acceptance exact-field wording clarification`으로 고정했습니다.
- 근거는 current shipped docs/test 중 [README.md](/home/xpdlqj/code/projectH/README.md#L135), [README.md](/home/xpdlqj/code/projectH/README.md#L143), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L1966), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L3149)는 `pearlabyss.com/200`, `pearlabyss.com/300`, `WEB`, `설명 카드`, `설명형 다중 출처 합의`, `공식 기반` · `백과 기반` exact-field를 이미 직접 고정하는 반면, [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1344), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1352)는 아직 `response-origin continuity` / `drift 없음` generic framing으로 남아 있기 때문입니다.
- initial line 하나와 follow-up line 하나를 따로 micro-slice로 쪼개기보다, 같은 file·same-family·same verification axis인 acceptance pair를 한 번에 정렬하는 편이 더 작은 coherent slice입니다.

## 검증
- `sed -n '1,220p' AGENTS.md`
- `sed -n '1,220p' work/README.md`
- `sed -n '1,220p' verify/README.md`
- `sed -n '1,220p' .pipeline/README.md`
- `sed -n '1,260p' work/4/8/2026-04-08-history-card-entity-card-dual-probe-click-reload-follow-up-milestone-backlog-response-origin-source-path-exact-field-wording-clarification.md`
- `sed -n '1,260p' verify/4/8/2026-04-08-history-card-entity-card-dual-probe-click-reload-initial-milestone-backlog-response-origin-source-path-exact-field-wording-clarification-verification.md`
- `sed -n '1,260p' .pipeline/claude_handoff.md`
- `nl -ba docs/MILESTONES.md | sed -n '53,64p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '42,53p'`
- `nl -ba README.md | sed -n '135,146p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '1344,1355p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '1966,1984p;3149,3166p;3281,3298p;3470,3487p;3574,3591p'`
- `git diff -- docs/MILESTONES.md docs/TASK_BACKLOG.md`
- `git diff --check -- docs/MILESTONES.md docs/TASK_BACKLOG.md`
- `git diff -- README.md docs/ACCEPTANCE_CRITERIA.md e2e/tests/web-smoke.spec.mjs`
- `rg -n "entity-card dual-probe" work/4/8 verify/4/8 .pipeline/claude_handoff.md`
- `test -f work/4/8/2026-04-08-history-card-entity-card-dual-probe-click-reload-docs-exact-field-wording-clarification.md && echo combined_docs_exists || echo combined_docs_missing`
- `test -f work/4/8/2026-04-08-history-card-entity-card-dual-probe-click-reload-initial-docs-exact-field-wording-clarification.md && echo initial_docs_exists || echo initial_docs_missing`
- `test -f work/4/8/2026-04-08-history-card-entity-card-dual-probe-click-reload-follow-up-docs-exact-field-wording-clarification.md && echo followup_docs_exists || echo followup_docs_missing`
- `git status --short -- .pipeline/claude_handoff.md pipeline_gui/app.py pipeline_gui/view.py tests/test_pipeline_gui_app.py windows-launchers/README.md`
- `git status --short -- .pipeline/claude_handoff.md verify/4/8/2026-04-08-history-card-entity-card-dual-probe-click-reload-follow-up-milestone-backlog-response-origin-source-path-exact-field-wording-clarification-verification.md`
- `git diff --check -- .pipeline/claude_handoff.md`
- `git diff --no-index --check /dev/null verify/4/8/2026-04-08-history-card-entity-card-dual-probe-click-reload-follow-up-milestone-backlog-response-origin-source-path-exact-field-wording-clarification-verification.md`
- Playwright rerun, `python3 -m unittest -v`, `make e2e-test`는 이번 docs-only verification 범위를 넘어가므로 재실행하지 않았습니다.

## 남은 리스크
- current shipped acceptance pair [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1344), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1352)는 아직 generic wording으로 남아 있습니다.
- 이번 verification은 latest docs-only `/work` truth와 next slice selection까지만 다뤘으므로, browser/runtime health 자체는 다시 판정하지 않았습니다.
