# entity-card zero-strong-slot natural-reload initial + follow-up docs browser-prefix wording clarification verification

날짜: 2026-04-08

## 변경 파일
- `verify/4/8/2026-04-08-entity-card-zero-strong-slot-natural-reload-initial-follow-up-docs-browser-prefix-wording-clarification-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest `/work`는 zero-strong-slot natural-reload initial/follow-up docs 4곳의 browser-prefix wording이 current tree 기준으로 실제 반영됐다고 보고했습니다. 이번 라운드에서는 그 docs-only change가 truthful한지 다시 확인해야 했습니다.
- zero-strong-slot docs set이 이번 `/work`로 닫혔으므로, 다음 Claude 라운드에는 adjacent natural-reload family에서 남아 있는 가장 작은 browser-prefix wording gap 1건만 고정해야 했습니다.

## 핵심 변경
- latest `/work`의 observable end state는 truthful하셨습니다. [README.md](/home/xpdlqj/code/projectH/README.md#L150), [README.md](/home/xpdlqj/code/projectH/README.md#L151), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1359), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1360)에는 `/work`가 주장한 `browser 자연어 reload` framing과 suffix 제거가 실제로 반영돼 있었고, current sibling docs/test가 말하는 browser natural-reload contract와 정렬됩니다.
- docs-only claimed check도 truthful했습니다. `git diff -- README.md docs/ACCEPTANCE_CRITERIA.md`는 empty였고, `git diff --check -- README.md docs/ACCEPTANCE_CRITERIA.md`는 clean이었습니다.
- next slice는 `entity-card crimson-desert natural-reload initial docs browser-prefix wording clarification`으로 고정했습니다. current docs [README.md](/home/xpdlqj/code/projectH/README.md#L152), [README.md](/home/xpdlqj/code/projectH/README.md#L158), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1361), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1367)은 붉은사막 initial natural-reload exact-field/noisy-exclusion 및 source-path plurality truth를 적고 있지만 `browser 자연어 reload` framing을 direct prefix로는 충분히 드러내지 않습니다. 반면 sibling docs [docs/MILESTONES.md](/home/xpdlqj/code/projectH/docs/MILESTONES.md#L70), [docs/MILESTONES.md](/home/xpdlqj/code/projectH/docs/MILESTONES.md#L76), [docs/TASK_BACKLOG.md](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L59), [docs/TASK_BACKLOG.md](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L65)와 current test title/body [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L4244), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L4316), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L4288), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L4308) already browser natural-reload contract를 직접 고정하므로, runtime을 건드리지 않고 README/acceptance wording만 그 축에 맞추는 편이 가장 작은 next slice입니다.

## 검증
- `sed -n '1,220p' AGENTS.md`
- `sed -n '1,220p' work/README.md`
- `sed -n '1,220p' verify/README.md`
- `sed -n '1,220p' .pipeline/README.md`
- `sed -n '1,220p' .agents/skills/round-handoff/SKILL.md`
- `sed -n '1,220p' work/4/8/2026-04-08-entity-card-zero-strong-slot-natural-reload-initial-follow-up-docs-browser-prefix-wording-clarification.md`
- `sed -n '1,240p' verify/4/8/2026-04-08-history-card-entity-card-zero-strong-slot-click-reload-second-follow-up-docs-entity-prefix-wording-clarification-verification.md`
- `git status --short`
- `nl -ba README.md | sed -n '150,151p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '1359,1360p'`
- `nl -ba README.md | sed -n '152,159p'`
- `nl -ba docs/MILESTONES.md | sed -n '70,77p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '1361,1368p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '59,66p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '4244,4322p'`
- `rg -n "붉은사막|dual-probe|browser natural-reload exact-field|browser 자연어 reload" README.md docs/MILESTONES.md docs/ACCEPTANCE_CRITERIA.md docs/TASK_BACKLOG.md | sed -n '1,240p'`
- `git diff -- README.md docs/ACCEPTANCE_CRITERIA.md`
- `git diff --check -- README.md docs/ACCEPTANCE_CRITERIA.md`
- `python3 -m unittest -v`, `make e2e-test`, Playwright rerun은 이번 docs-only verification 범위를 넘어가므로 재실행하지 않았습니다.

## 남은 리스크
- zero-strong-slot docs set은 이번 라운드로 닫혔지만, 붉은사막 initial natural-reload docs는 README/acceptance에서 아직 `browser 자연어 reload` framing이 sibling docs와 test title만큼 직접적이지 않습니다.
- 다른 family는 이번 verification 범위 밖이라 재판정하지 않았습니다.
