# entity-card dual-probe natural-reload second-follow-up milestone/backlog response-origin exact-field wording clarification verification

날짜: 2026-04-08

## 변경 파일
- `verify/4/8/2026-04-08-entity-card-dual-probe-natural-reload-second-follow-up-milestone-backlog-response-origin-exact-field-wording-clarification-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest `/work`는 [docs/MILESTONES.md](/home/xpdlqj/code/projectH/docs/MILESTONES.md#L84), [docs/TASK_BACKLOG.md](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L73)의 dual-probe natural-reload second-follow-up planning-doc wording을 exact-field drift-prevention framing으로 정렬했다고 보고했습니다. 이번 라운드에서는 그 docs-only change가 current tree 기준으로 실제 반영됐는지 다시 확인해야 했습니다.
- 동시에 latest same-day `/verify`는 dual-probe natural-reload follow-up까지의 truth만 고정하고 있었으므로, newer `/work`에 맞춰 current truth와 next single slice를 다시 맞출 필요가 있었습니다.

## 핵심 변경
- latest `/work`는 truthful했습니다. current [docs/MILESTONES.md](/home/xpdlqj/code/projectH/docs/MILESTONES.md#L84)와 [docs/TASK_BACKLOG.md](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L73)는 모두 `source-path + response-origin exact-field drift-prevention` wording으로 바뀌어 있었고, `/work`가 주장한 dual-probe natural-reload second-follow-up planning-doc clarification이 실제 tree에 반영돼 있었습니다.
- current root docs와 test wording과의 정렬도 맞았습니다. [README.md](/home/xpdlqj/code/projectH/README.md#L164), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1375), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L4800)는 이미 source-path 유지와 `WEB`, `설명 카드`, `설명형 다중 출처 합의`, `공식 기반` · `백과 기반` drift-prevention contract를 직접 드러내고 있었고, current planning docs도 여기에 맞춰졌습니다.
- docs-only check도 truthful했습니다. `git diff -- docs/MILESTONES.md docs/TASK_BACKLOG.md`는 empty였고, `git diff --check -- docs/MILESTONES.md docs/TASK_BACKLOG.md`는 clean이었습니다.
- 다음 슬라이스는 `history-card entity-card dual-probe click-reload second-follow-up milestone/backlog response-origin exact-field wording clarification`으로 고정했습니다. current [docs/MILESTONES.md](/home/xpdlqj/code/projectH/docs/MILESTONES.md#L83)와 [docs/TASK_BACKLOG.md](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L72)는 아직 generic `source-path + response-origin continuity` framing으로 남아 있지만, [README.md](/home/xpdlqj/code/projectH/README.md#L163), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1374), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L3074)는 source-path 유지와 `WEB`, `설명 카드`, `설명형 다중 출처 합의`, `공식 기반` · `백과 기반` drift-prevention을 더 직접적으로 드러냅니다.

## 검증
- `sed -n '1,260p' AGENTS.md`
- `sed -n '1,260p' work/README.md`
- `sed -n '1,260p' verify/README.md`
- `sed -n '1,260p' .pipeline/README.md`
- `sed -n '1,260p' .agents/skills/round-handoff/SKILL.md`
- `sed -n '1,260p' work/4/8/2026-04-08-entity-card-dual-probe-natural-reload-second-follow-up-milestone-backlog-response-origin-exact-field-wording-clarification.md`
- `sed -n '1,260p' verify/4/8/2026-04-08-entity-card-dual-probe-natural-reload-follow-up-milestone-backlog-response-origin-exact-field-wording-clarification-verification.md`
- `sed -n '1,260p' .pipeline/claude_handoff.md`
- `sed -n '1,260p' docs/NEXT_STEPS.md`
- `sed -n '1,260p' docs/MILESTONES.md`
- `sed -n '1,260p' docs/TASK_BACKLOG.md`
- `git status --short`
- `nl -ba docs/MILESTONES.md | sed -n '83,85p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '72,74p'`
- `nl -ba README.md | sed -n '163,165p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '1374,1375p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '4798,4804p;3072,3078p'`
- `git diff -- docs/MILESTONES.md docs/TASK_BACKLOG.md`
- `git diff --check -- docs/MILESTONES.md docs/TASK_BACKLOG.md`
- `rg -n "dual-probe.*second-follow-up|response-origin continuity|exact-field drift-prevention|history-card entity-card .*second-follow-up" docs/MILESTONES.md docs/TASK_BACKLOG.md README.md docs/ACCEPTANCE_CRITERIA.md e2e/tests/web-smoke.spec.mjs`
- `nl -ba README.md | sed -n '163,166p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '1374,1376p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '3074,3078p;4800,4804p;5047,5051p'`
- `ls work/4/8 | rg 'dual-probe|crimson-desert.*second-follow-up.*response-origin-exact-field'`
- `ls verify/4/8 | rg 'dual-probe|crimson-desert.*second-follow-up.*response-origin-exact-field'`
- Playwright rerun, `python3 -m unittest -v`, `make e2e-test`는 이번 docs-only verification 범위를 넘어가므로 재실행하지 않았습니다.

## 남은 리스크
- 이번 verification은 latest `/work` truth와 next docs-only slice selection까지만 다뤘으므로, browser/runtime health 자체는 다시 판정하지 않았습니다.
- adjacent planning-doc family에는 아직 generic `continuity` phrasing이 남아 있습니다. 다만 이번 라운드에서는 latest `/work`가 닫은 dual-probe second-follow-up과 가장 가까운 same-family current-risk reduction인 history-card entity-card dual-probe click-reload second-follow-up wording부터 좁게 다루는 편이 맞습니다.
