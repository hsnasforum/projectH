# entity-card crimson-desert natural-reload second-follow-up docs browser-prefix wording clarification verification

날짜: 2026-04-08

## 변경 파일
- `verify/4/8/2026-04-08-entity-card-crimson-desert-natural-reload-second-follow-up-docs-browser-prefix-wording-clarification-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest `/work`는 붉은사막 natural-reload second-follow-up docs 3곳의 browser-prefix wording이 current tree 기준으로 실제 반영됐다고 보고했습니다. 이번 라운드에서는 그 docs-only change가 truthful한지 다시 확인해야 했습니다.
- same natural-reload docs family에서 crimson-desert set이 닫힌 뒤, 다음 Claude 라운드는 남은 dual-probe browser-prefix wording gap을 한 coherent docs slice로만 넘겨야 했습니다.

## 핵심 변경
- latest `/work`의 observable end state는 truthful하셨습니다. [README.md](/home/xpdlqj/code/projectH/README.md#L165), [README.md](/home/xpdlqj/code/projectH/README.md#L167), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1370)에는 `/work`가 주장한 `browser 자연어 reload 후 두 번째 follow-up` framing이 실제로 반영돼 있었고, sibling docs/test가 말하는 browser natural-reload second-follow-up contract와 정렬됩니다.
- docs-only claimed check도 truthful했습니다. `git diff -- README.md docs/ACCEPTANCE_CRITERIA.md`는 empty였고, `git diff --check -- README.md docs/ACCEPTANCE_CRITERIA.md`는 clean이었습니다.
- next slice는 `entity-card dual-probe natural-reload docs browser-prefix wording clarification`으로 고정했습니다. current docs [README.md](/home/xpdlqj/code/projectH/README.md#L153), [README.md](/home/xpdlqj/code/projectH/README.md#L154), [README.md](/home/xpdlqj/code/projectH/README.md#L155), [README.md](/home/xpdlqj/code/projectH/README.md#L156), [README.md](/home/xpdlqj/code/projectH/README.md#L164), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1362), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1363), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1364), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1365), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1375)는 dual-probe source-path continuity와 exact-field drift truth를 적고 있지만 `browser 자연어 reload` framing을 direct prefix로는 충분히 드러내지 않습니다. 반면 sibling docs [docs/MILESTONES.md](/home/xpdlqj/code/projectH/docs/MILESTONES.md#L71), [docs/MILESTONES.md](/home/xpdlqj/code/projectH/docs/MILESTONES.md#L72), [docs/MILESTONES.md](/home/xpdlqj/code/projectH/docs/MILESTONES.md#L73), [docs/MILESTONES.md](/home/xpdlqj/code/projectH/docs/MILESTONES.md#L74), [docs/TASK_BACKLOG.md](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L60), [docs/TASK_BACKLOG.md](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L61), [docs/TASK_BACKLOG.md](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L62), [docs/TASK_BACKLOG.md](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L63)와 current test/body [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L4370), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L4485), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L4608), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L4737), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L4800), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L4463), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L4701), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L4711) already browser natural-reload initial/follow-up/second-follow-up contract를 직접 고정하므로, runtime을 건드리지 않고 README/acceptance wording만 그 축에 맞추는 편이 가장 작은 same-family current-risk reduction입니다.

## 검증
- `sed -n '1,220p' AGENTS.md`
- `sed -n '1,220p' work/README.md`
- `sed -n '1,220p' verify/README.md`
- `sed -n '1,220p' .pipeline/README.md`
- `sed -n '1,220p' .agents/skills/round-handoff/SKILL.md`
- `sed -n '1,220p' work/4/8/2026-04-08-entity-card-crimson-desert-natural-reload-second-follow-up-docs-browser-prefix-wording-clarification.md`
- `sed -n '1,240p' verify/4/8/2026-04-08-entity-card-crimson-desert-natural-reload-follow-up-docs-browser-prefix-wording-clarification-verification.md`
- `git status --short`
- `nl -ba README.md | sed -n '153,167p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '1362,1370p'`
- `nl -ba docs/MILESTONES.md | sed -n '70,79p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '59,68p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '4370,4805p'`
- `rg -n "dual-probe.*자연어 reload" README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md e2e/tests/web-smoke.spec.mjs`
- `git diff -- README.md docs/ACCEPTANCE_CRITERIA.md`
- `git diff --check -- README.md docs/ACCEPTANCE_CRITERIA.md`
- `python3 -m unittest -v`, `make e2e-test`, Playwright rerun은 이번 docs-only verification 범위를 넘어가므로 재실행하지 않았습니다.

## 남은 리스크
- 붉은사막 natural-reload docs browser-prefix는 이번 라운드로 닫혔지만, dual-probe natural-reload docs는 README/acceptance에서 아직 `browser 자연어 reload` framing이 initial, follow-up, second-follow-up 전 구간에 걸쳐 sibling docs와 test title/body만큼 직접적이지 않습니다.
- history-card 계열이나 other family wording gap은 이번 verification 범위 밖이라 재판정하지 않았습니다.
