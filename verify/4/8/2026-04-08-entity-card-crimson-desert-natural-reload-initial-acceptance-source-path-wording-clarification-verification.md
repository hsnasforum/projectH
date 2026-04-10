# entity-card crimson-desert natural-reload initial acceptance source-path wording clarification verification

날짜: 2026-04-08

## 변경 파일
- `verify/4/8/2026-04-08-entity-card-crimson-desert-natural-reload-initial-acceptance-source-path-wording-clarification-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest `/work`는 [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1367)의 entity-card crimson-desert natural-reload initial acceptance source-path wording을 sibling README와 current test title에 더 가깝게 맞췄다고 보고했습니다. 이번 라운드에서는 그 docs-only change가 current tree 기준으로 실제 반영됐는지 다시 확인해야 했습니다.
- 동시에 `/work` closeout 전체가 truthful한지 판정하고, same crimson-desert natural-reload family 안에서 다음 한 슬라이스를 다시 좁혀야 했습니다.

## 핵심 변경
- latest `/work`의 docs change 자체는 truthful했습니다. [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1367)에 `/work`가 주장한 `source path(... provenance)` compact wording이 실제로 반영돼 있었습니다.
- `/work`가 주장한 docs-only check도 truthful했습니다. `git diff -- docs/ACCEPTANCE_CRITERIA.md`는 empty였고, `git diff --check -- docs/ACCEPTANCE_CRITERIA.md`는 clean이었습니다.
- 다만 `/work` closeout 전체는 fully truthful하지 않았습니다. [README.md](/home/xpdlqj/code/projectH/README.md#L158)은 아직 `source path(... provenance 포함)` wording으로 남아 있어, current acceptance [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1367) 및 current browser smoke title [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L4316)의 compact source-path pattern과 완전히 정렬되지는 않았습니다. 따라서 `/work`의 `crimson-desert natural-reload docs 전체(initial + noisy + actual-search)가 이번 라운드로 compact source-path/exact-field로 정렬됐다`는 판단은 current tree 기준으로 과장입니다.
- 다음 슬라이스는 `entity-card crimson-desert natural-reload initial README source-path wording clarification`으로 고정했습니다. current root docs 같은 family 안에서 [README.md](/home/xpdlqj/code/projectH/README.md#L158) 한 줄만 아직 `provenance 포함` phrasing이 남아 있으므로, same-family current-risk reduction으로는 이 1줄 정렬이 가장 작고 truthful합니다.

## 검증
- `sed -n '1,260p' AGENTS.md`
- `sed -n '1,220p' work/README.md`
- `sed -n '1,220p' verify/README.md`
- `sed -n '1,220p' .pipeline/README.md`
- `sed -n '1,220p' .agents/skills/round-handoff/SKILL.md`
- `sed -n '1,240p' work/4/8/2026-04-08-entity-card-crimson-desert-natural-reload-initial-acceptance-source-path-wording-clarification.md`
- `sed -n '1,320p' verify/4/8/2026-04-08-entity-card-crimson-desert-actual-search-natural-reload-follow-up-second-follow-up-docs-exact-field-wording-clarification-verification.md`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '1366,1368p'`
- `nl -ba README.md | sed -n '158p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '4314,4318p'`
- `rg -n 'plurality|provenance 포함|context box에 .*provenance 포함|source path\\(` README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md | sed -n '1,200p'`
- `nl -ba docs/NEXT_STEPS.md | sed -n '1,220p'`
- `sed -n '1,320p' .pipeline/claude_handoff.md`
- `git diff -- docs/ACCEPTANCE_CRITERIA.md`
- `git diff --check -- docs/ACCEPTANCE_CRITERIA.md`
- `git status --short`
- Playwright rerun, `python3 -m unittest -v`, `make e2e-test`는 이번 docs-only verification 범위를 넘어가므로 재실행하지 않았습니다.

## 남은 리스크
- acceptance line [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1367)은 이번 라운드로 닫혔지만, same crimson-desert natural-reload initial README line [README.md](/home/xpdlqj/code/projectH/README.md#L158)은 아직 `provenance 포함` phrasing이 남아 있습니다.
- 이번 verification은 docs-only 범위였으므로 browser rerun이나 broader end-to-end health는 다시 판정하지 않았습니다.
