# entity-card dual-probe natural-reload follow-up milestone/backlog response-origin exact-field wording clarification verification

날짜: 2026-04-08

## 변경 파일
- `verify/4/8/2026-04-08-entity-card-dual-probe-natural-reload-follow-up-milestone-backlog-response-origin-exact-field-wording-clarification-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest `/work`는 [docs/MILESTONES.md](/home/xpdlqj/code/projectH/docs/MILESTONES.md#L74), [docs/TASK_BACKLOG.md](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L63)의 dual-probe natural-reload follow-up planning-doc wording을 exact-field drift-prevention framing으로 정렬했다고 보고했습니다. 이번 라운드에서는 그 docs-only change가 current tree 기준으로 실제 반영됐는지 다시 확인해야 했습니다.
- 동시에 latest same-day `/verify`는 이전 crimson-desert family를 기준으로 다음 슬라이스를 잡고 있었으므로, newer `/work`에 맞춰 current truth와 next single slice를 다시 고정할 필요가 있었습니다.

## 핵심 변경
- latest `/work`는 truthful했습니다. current [docs/MILESTONES.md](/home/xpdlqj/code/projectH/docs/MILESTONES.md#L74)와 [docs/TASK_BACKLOG.md](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L63)는 모두 `response-origin exact-field drift-prevention` wording으로 바뀌어 있었고, `/work`가 주장한 dual-probe natural-reload follow-up planning-doc clarification이 실제 tree에 반영돼 있었습니다.
- current root docs와 test wording과의 정렬도 맞았습니다. [README.md](/home/xpdlqj/code/projectH/README.md#L156), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1365), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L4737)는 이미 `WEB`, `설명 카드`, `설명형 다중 출처 합의`, `공식 기반` · `백과 기반` drift-prevention contract를 직접 드러내고 있었고, current planning docs도 여기에 맞춰졌습니다.
- docs-only check도 truthful했습니다. `git diff -- docs/MILESTONES.md docs/TASK_BACKLOG.md`는 empty였고, `git diff --check -- docs/MILESTONES.md docs/TASK_BACKLOG.md`는 clean이었습니다.
- 다음 슬라이스는 `entity-card dual-probe natural-reload second-follow-up milestone/backlog response-origin exact-field wording clarification`으로 고정했습니다. current [docs/MILESTONES.md](/home/xpdlqj/code/projectH/docs/MILESTONES.md#L84)와 [docs/TASK_BACKLOG.md](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L73)는 아직 generic `source-path + response-origin continuity` framing으로 남아 있지만, [README.md](/home/xpdlqj/code/projectH/README.md#L164), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1375), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L4800)는 source-path 유지와 `WEB`, `설명 카드`, `설명형 다중 출처 합의`, `공식 기반` · `백과 기반` drift-prevention을 더 직접적으로 드러냅니다.

## 검증
- `sed -n '1,260p' AGENTS.md`
- `sed -n '1,260p' work/README.md`
- `sed -n '1,260p' verify/README.md`
- `sed -n '1,260p' .pipeline/README.md`
- `sed -n '1,260p' .agents/skills/round-handoff/SKILL.md`
- `sed -n '1,260p' work/4/8/2026-04-08-entity-card-dual-probe-natural-reload-follow-up-milestone-backlog-response-origin-exact-field-wording-clarification.md`
- `sed -n '1,260p' verify/4/8/2026-04-08-entity-card-crimson-desert-actual-search-natural-reload-follow-up-milestone-backlog-response-origin-exact-field-wording-clarification-verification.md`
- `sed -n '1,260p' .pipeline/claude_handoff.md`
- `sed -n '1,260p' docs/NEXT_STEPS.md`
- `sed -n '1,260p' docs/MILESTONES.md`
- `sed -n '1,260p' docs/TASK_BACKLOG.md`
- `git status --short`
- `nl -ba docs/MILESTONES.md | sed -n '71,76p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '60,64p'`
- `nl -ba README.md | sed -n '153,157p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '1363,1366p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '4735,4741p;4800,4806p'`
- `git diff -- docs/MILESTONES.md docs/TASK_BACKLOG.md`
- `git diff --check -- docs/MILESTONES.md docs/TASK_BACKLOG.md`
- `ls -1t verify/4/8 | sed -n '1,5p'`
- `nl -ba docs/MILESTONES.md | sed -n '82,85p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '72,74p'`
- `nl -ba README.md | sed -n '163,165p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '1374,1375p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '4798,4804p'`
- `rg -n "dual-probe.*second-follow-up|pearlabyss.com/200|response-origin continuity" docs/MILESTONES.md docs/TASK_BACKLOG.md README.md docs/ACCEPTANCE_CRITERIA.md e2e/tests/web-smoke.spec.mjs`
- `ls work/4/8 | rg 'dual-probe.*second-follow-up.*(milestone|backlog|wording)'`
- `ls verify/4/8 | rg 'dual-probe.*second-follow-up.*(milestone|backlog|wording)'`
- Playwright rerun, `python3 -m unittest -v`, `make e2e-test`는 이번 docs-only verification 범위를 넘어가므로 재실행하지 않았습니다.

## 남은 리스크
- 이번 verification은 latest `/work` truth와 next docs-only slice selection까지만 다뤘으므로, browser/runtime health 자체는 다시 판정하지 않았습니다.
- adjacent planning-doc family에는 아직 generic `continuity` phrasing이 남아 있습니다. 다만 이번 라운드에서는 latest `/work`가 닫은 dual-probe natural-reload follow-up과 가장 가까운 same-family current-risk reduction인 natural-reload second-follow-up wording부터 좁게 다루는 편이 맞습니다.
