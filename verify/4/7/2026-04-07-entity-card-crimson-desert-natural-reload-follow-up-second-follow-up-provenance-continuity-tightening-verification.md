# entity-card crimson-desert natural-reload follow-up/second-follow-up provenance-continuity tightening verification

날짜: 2026-04-07

## 변경 파일
- `verify/4/7/2026-04-07-entity-card-crimson-desert-natural-reload-follow-up-second-follow-up-provenance-continuity-tightening-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest `/work`는 crimson natural-reload follow-up/second-follow-up dedicated browser scenarios와 대응 docs에 `blog.example.com` provenance continuity를 직접 추가했다고 주장하므로, focused Playwright rerun과 current docs truth를 다시 맞춰 볼 필요가 있었습니다.
- rerun 결과 [e2e/tests/web-smoke.spec.mjs:5177](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs:5177)과 [e2e/tests/web-smoke.spec.mjs:5259](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs:5259)는 now `namu.wiki`, `ko.wikipedia.org`, `blog.example.com`을 함께 context box에 요구하고, `npx playwright test tests/web-smoke.spec.mjs -g "entity-card 붉은사막 자연어 reload 후.*noisy" --reporter=line`도 `2 passed`였습니다. [README.md:166](/home/xpdlqj/code/projectH/README.md:166), [README.md:167](/home/xpdlqj/code/projectH/README.md:167), [docs/MILESTONES.md:78](/home/xpdlqj/code/projectH/docs/MILESTONES.md:78), [docs/MILESTONES.md:79](/home/xpdlqj/code/projectH/docs/MILESTONES.md:79), [docs/ACCEPTANCE_CRITERIA.md:1369](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md:1369), [docs/ACCEPTANCE_CRITERIA.md:1370](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md:1370), [docs/TASK_BACKLOG.md:67](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md:67), [docs/TASK_BACKLOG.md:68](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md:68), [docs/NEXT_STEPS.md:16](/home/xpdlqj/code/projectH/docs/NEXT_STEPS.md:16)도 same truth와 맞게 정렬되어 있습니다.
- 이 family의 다음 same-family current-risk는 dedicated noisy-exclusion lines가 아니라, parallel general continuity docs가 아직 `namu.wiki`, `ko.wikipedia.org`만 직접 적는 점입니다. [README.md:159](/home/xpdlqj/code/projectH/README.md:159), [README.md:165](/home/xpdlqj/code/projectH/README.md:165), [docs/MILESTONES.md:77](/home/xpdlqj/code/projectH/docs/MILESTONES.md:77), [docs/MILESTONES.md:85](/home/xpdlqj/code/projectH/docs/MILESTONES.md:85), [docs/ACCEPTANCE_CRITERIA.md:1368](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md:1368), [docs/ACCEPTANCE_CRITERIA.md:1376](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md:1376), [docs/TASK_BACKLOG.md:66](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md:66), [docs/TASK_BACKLOG.md:74](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md:74)는 general follow-up/second-follow-up continuity를 약하게 적지만, same shipped truth를 가리키는 [tests/test_web_app.py:17327](/home/xpdlqj/code/projectH/tests/test_web_app.py:17327), [tests/test_web_app.py:17386](/home/xpdlqj/code/projectH/tests/test_web_app.py:17386), [e2e/tests/web-smoke.spec.mjs:5178](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs:5178), [e2e/tests/web-smoke.spec.mjs:5260](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs:5260), [docs/NEXT_STEPS.md:16](/home/xpdlqj/code/projectH/docs/NEXT_STEPS.md:16)은 `blog.example.com` provenance continuity까지 포함하는 현재 truth를 이미 가리킵니다.

## 핵심 변경
- latest `/work`의 crimson provenance-continuity tightening claim이 truthful함을 확인하고, focused browser rerun과 docs re-check 결과를 persistent `/verify` note로 남겼습니다.
- 다음 Claude 슬라이스를 `entity-card crimson-desert natural-reload follow-up-second-follow-up source-path plurality docs truth-sync consolidation`으로 고정했습니다.

## 검증
- `sed -n '1,220p' AGENTS.md`
- `sed -n '1,220p' work/README.md`
- `sed -n '1,220p' verify/README.md`
- `sed -n '1,260p' .pipeline/README.md`
- `sed -n '1,220p' .agents/skills/round-handoff/SKILL.md`
- `ls -1t verify/4/7 | head -n 12`
- `sed -n '1,240p' work/4/7/2026-04-07-entity-card-crimson-desert-natural-reload-follow-up-second-follow-up-provenance-continuity-tightening.md`
- `sed -n '1,240p' verify/4/7/2026-04-07-entity-card-crimson-desert-natural-reload-follow-up-second-follow-up-task-backlog-renumber-truth-sync-correction-verification.md`
- `sed -n '1,240p' .pipeline/claude_handoff.md`
- `git status --short`
- `git diff --check -- e2e/tests/web-smoke.spec.mjs README.md docs/NEXT_STEPS.md docs/MILESTONES.md docs/ACCEPTANCE_CRITERIA.md docs/TASK_BACKLOG.md`
- `npx playwright test tests/web-smoke.spec.mjs -g "entity-card 붉은사막 자연어 reload 후.*noisy" --reporter=line`
- `rg -c '^test\\(' e2e/tests/web-smoke.spec.mjs`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '5107,5268p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '6296,6392p'`
- `nl -ba tests/test_web_app.py | sed -n '17275,17395p'`
- `nl -ba README.md | sed -n '150,190p'`
- `nl -ba docs/MILESTONES.md | sed -n '68,98p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '1358,1398p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '56,92p'`
- `nl -ba docs/NEXT_STEPS.md | sed -n '16,16p'`
- `rg -n "entity-card 붉은사막 자연어 reload 후 follow-up|entity-card 붉은사막 자연어 reload 후 두 번째 follow-up|Entity-card 붉은사막 browser natural-reload follow-up|Entity-card 붉은사막 natural-reload second-follow-up" README.md docs/MILESTONES.md docs/ACCEPTANCE_CRITERIA.md docs/TASK_BACKLOG.md`
- `rg -n "붉은사막.*follow-up|붉은사막.*second follow-up|crimson.*follow|entity-card crimson|entity-noisy-nat|actual-nat" tests/test_web_app.py`
- focused browser/docs verification round이므로 `python3 -m unittest -v`와 `make e2e-test`는 재실행하지 않았습니다.

## 남은 리스크
- crimson natural-reload follow-up/second-follow-up family의 dedicated noisy-exclusion docs는 now `blog.example.com` provenance continuity까지 직접 잠그지만, parallel general continuity docs는 아직 `namu.wiki`, `ko.wikipedia.org`만 적어 same shipped truth보다 약하게 읽힙니다.
- 따라서 다음 라운드는 runtime이나 browser scenario를 더 넓히지 말고, [README.md:159](/home/xpdlqj/code/projectH/README.md:159), [README.md:165](/home/xpdlqj/code/projectH/README.md:165), [docs/MILESTONES.md:77](/home/xpdlqj/code/projectH/docs/MILESTONES.md:77), [docs/MILESTONES.md:85](/home/xpdlqj/code/projectH/docs/MILESTONES.md:85), [docs/ACCEPTANCE_CRITERIA.md:1368](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md:1368), [docs/ACCEPTANCE_CRITERIA.md:1376](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md:1376), [docs/TASK_BACKLOG.md:66](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md:66), [docs/TASK_BACKLOG.md:74](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md:74) 같은 general continuity lines만 current truth 수준으로 정리하는 docs-only truth-sync가 가장 작고 reviewable합니다.
