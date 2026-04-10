# entity-card crimson-desert natural-reload initial milestone/backlog source-path wording clarification verification

날짜: 2026-04-08

## 변경 파일
- `verify/4/8/2026-04-08-entity-card-crimson-desert-natural-reload-initial-milestone-backlog-source-path-wording-clarification-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest `/work`는 [docs/MILESTONES.md](/home/xpdlqj/code/projectH/docs/MILESTONES.md#L76)과 [docs/TASK_BACKLOG.md](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L65)의 entity-card crimson-desert natural-reload initial planning-doc source-path wording을 current README/acceptance/test title에 더 가깝게 맞췄다고 보고했습니다. 이번 라운드에서는 그 docs-only change가 current tree 기준으로 실제 반영됐는지 다시 확인해야 했습니다.
- 동시에 latest `/work` closeout 전체가 truthful한지 판정하고, same crimson-desert actual-search natural-reload family 안에서 다음 한 슬라이스를 다시 좁혀야 했습니다.

## 핵심 변경
- latest `/work`의 planning-doc change 자체는 truthful했습니다. [docs/MILESTONES.md](/home/xpdlqj/code/projectH/docs/MILESTONES.md#L76)과 [docs/TASK_BACKLOG.md](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L65)에 `/work`가 주장한 compact source-path wording이 실제로 반영돼 있었습니다.
- `/work`가 주장한 docs-only check도 truthful했습니다. `git diff -- docs/MILESTONES.md docs/TASK_BACKLOG.md`는 empty였고, `git diff --check -- docs/MILESTONES.md docs/TASK_BACKLOG.md`는 clean이었습니다.
- 이번 라운드에서 latest `/work` closeout 전체도 current tree 기준으로 truthful하다고 확인했습니다. `/work`가 적은 대로 crimson-desert natural-reload initial docs는 [README.md](/home/xpdlqj/code/projectH/README.md#L158), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1367), [docs/MILESTONES.md](/home/xpdlqj/code/projectH/docs/MILESTONES.md#L76), [docs/TASK_BACKLOG.md](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L65)에서 모두 compact source-path pattern으로 정렬돼 있습니다.
- 다음 슬라이스는 `entity-card crimson-desert actual-search natural-reload follow-up + second-follow-up milestone/backlog source-path wording clarification`으로 고정했습니다. same family planning docs인 [docs/MILESTONES.md](/home/xpdlqj/code/projectH/docs/MILESTONES.md#L77), [docs/MILESTONES.md](/home/xpdlqj/code/projectH/docs/MILESTONES.md#L85), [docs/TASK_BACKLOG.md](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L66), [docs/TASK_BACKLOG.md](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L74)는 아직 `source-path plurality` 또는 comma-separated source-path phrasing으로 남아 있어, current root docs/test title의 compact `source path(\`namu.wiki\`/\`ko.wikipedia.org\`)` pattern과 완전히 맞지는 않습니다.

## 검증
- `sed -n '1,220p' AGENTS.md`
- `sed -n '1,220p' work/README.md`
- `sed -n '1,220p' verify/README.md`
- `sed -n '1,220p' .pipeline/README.md`
- `sed -n '1,220p' .agents/skills/round-handoff/SKILL.md`
- `sed -n '1,240p' work/4/8/2026-04-08-entity-card-crimson-desert-natural-reload-initial-milestone-backlog-source-path-wording-clarification.md`
- `sed -n '1,260p' verify/4/8/2026-04-08-entity-card-crimson-desert-natural-reload-initial-readme-source-path-wording-clarification-verification.md`
- `sed -n '1,260p' .pipeline/claude_handoff.md`
- `nl -ba docs/MILESTONES.md | sed -n '70,79p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '59,68p'`
- `nl -ba README.md | sed -n '152,167p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '1361,1370p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '4314,4320p;4870,4876p;4990,4996p;5045,5051p;5107,5113p;5186,5192p'`
- `rg -n 'plurality|, \`ko.wikipedia.org\`|provenance 포함|actual-search browser natural-reload follow-up|actual-search natural-reload second-follow-up|붉은사막.*source-path|붉은사막.*source path' README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md | sed -n '1,240p'`
- `git diff -- docs/MILESTONES.md docs/TASK_BACKLOG.md`
- `git diff --check -- docs/MILESTONES.md docs/TASK_BACKLOG.md`
- `git status --short docs/MILESTONES.md docs/TASK_BACKLOG.md work/4/8/2026-04-08-entity-card-crimson-desert-natural-reload-initial-milestone-backlog-source-path-wording-clarification.md .pipeline/claude_handoff.md`
- `nl -ba docs/NEXT_STEPS.md | sed -n '1,120p'`
- `nl -ba docs/MILESTONES.md | sed -n '75,86p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '64,75p'`
- `git status --short | sed -n '1,120p'`
- Playwright rerun, `python3 -m unittest -v`, `make e2e-test`는 이번 docs-only verification 범위를 넘어가므로 재실행하지 않았습니다.

## 남은 리스크
- current shipped contract docs인 [README.md](/home/xpdlqj/code/projectH/README.md#L157), [README.md](/home/xpdlqj/code/projectH/README.md#L159), [README.md](/home/xpdlqj/code/projectH/README.md#L165), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1366), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1368), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1376)와 current browser smoke title [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L4872), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L5047)는 already compact source-path contract를 드러내지만, same family planning docs [docs/MILESTONES.md](/home/xpdlqj/code/projectH/docs/MILESTONES.md#L77), [docs/MILESTONES.md](/home/xpdlqj/code/projectH/docs/MILESTONES.md#L85), [docs/TASK_BACKLOG.md](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L66), [docs/TASK_BACKLOG.md](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L74)는 아직 comma/plurality wording으로 남아 있습니다.
- 이번 verification은 docs-only 범위였으므로 browser rerun이나 broader end-to-end health는 다시 판정하지 않았습니다.
