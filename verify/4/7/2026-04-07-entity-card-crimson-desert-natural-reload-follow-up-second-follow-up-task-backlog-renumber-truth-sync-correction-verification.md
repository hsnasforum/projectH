# entity-card crimson-desert natural-reload follow-up/second-follow-up task-backlog renumber truth-sync correction verification

날짜: 2026-04-07

## 변경 파일
- `verify/4/7/2026-04-07-entity-card-crimson-desert-natural-reload-follow-up-second-follow-up-task-backlog-renumber-truth-sync-correction-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest `/work`는 `docs/TASK_BACKLOG.md`의 crimson natural-reload follow-up/second-follow-up block에서 빠졌던 `55`, `56` 번호를 복구해 numbering truth를 닫았다고 주장하므로, 해당 줄의 actual numbering과 docs-only 검증 범위를 다시 확인할 필요가 있었습니다.
- rerun 결과 [docs/TASK_BACKLOG.md:64](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md:64)부터 [docs/TASK_BACKLOG.md:74](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md:74)까지는 now `51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61`의 단조 증가로 맞춰져 있고, latest `/work`의 correction claim은 current tree와 일치합니다.
- 이 family의 다음 same-family current-risk는 numbering이 아니라 dedicated crimson follow-up/second-follow-up browser/docs가 `blog.example.com` provenance continuity를 직접 적지 않는 점입니다. current crimson-specific browser scenarios인 [e2e/tests/web-smoke.spec.mjs:5177](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs:5177), [e2e/tests/web-smoke.spec.mjs:5258](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs:5258)와 대응 docs인 [README.md:166](/home/xpdlqj/code/projectH/README.md:166), [README.md:167](/home/xpdlqj/code/projectH/README.md:167), [docs/MILESTONES.md:78](/home/xpdlqj/code/projectH/docs/MILESTONES.md:78), [docs/MILESTONES.md:79](/home/xpdlqj/code/projectH/docs/MILESTONES.md:79), [docs/ACCEPTANCE_CRITERIA.md:1369](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md:1369), [docs/ACCEPTANCE_CRITERIA.md:1370](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md:1370), [docs/TASK_BACKLOG.md:67](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md:67), [docs/TASK_BACKLOG.md:68](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md:68)은 `namu.wiki`, `ko.wikipedia.org` continuity까지만 직접 적습니다. 반면 same runtime truth를 가리키는 generic noisy-single-source service/browser anchors인 [tests/test_web_app.py:17327](/home/xpdlqj/code/projectH/tests/test_web_app.py:17327), [tests/test_web_app.py:17386](/home/xpdlqj/code/projectH/tests/test_web_app.py:17386), [e2e/tests/web-smoke.spec.mjs:6305](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs:6305), [e2e/tests/web-smoke.spec.mjs:6381](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs:6381), [README.md:184](/home/xpdlqj/code/projectH/README.md:184), [README.md:185](/home/xpdlqj/code/projectH/README.md:185)은 `blog.example.com` provenance continuity까지 직접 적습니다. 이 마지막 판단은 existing coverage/doc split을 근거로 한 추론입니다.

## 핵심 변경
- latest `/work`가 truthful함을 확인하고, crimson natural-reload follow-up/second-follow-up task-backlog renumber correction이 current docs truth와 맞음을 persistent `/verify` note로 남겼습니다.
- 다음 Claude 슬라이스를 `entity-card crimson-desert natural-reload follow-up-second-follow-up provenance-continuity tightening`으로 고정했습니다.

## 검증
- `sed -n '1,220p' AGENTS.md`
- `sed -n '1,220p' work/README.md`
- `sed -n '1,220p' verify/README.md`
- `sed -n '1,260p' .pipeline/README.md`
- `sed -n '1,220p' .agents/skills/round-handoff/SKILL.md`
- `ls -1t verify/4/7 | head -n 12`
- `sed -n '1,260p' work/4/7/2026-04-07-entity-card-crimson-desert-natural-reload-follow-up-second-follow-up-task-backlog-renumber-truth-sync-correction.md`
- `sed -n '1,260p' verify/4/7/2026-04-07-entity-card-crimson-desert-natural-reload-follow-up-second-follow-up-noisy-exclusion-tightening-verification.md`
- `git status --short docs/TASK_BACKLOG.md .pipeline/claude_handoff.md`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '64,74p'`
- `git diff --check -- docs/TASK_BACKLOG.md`
- `nl -ba README.md | sed -n '160,170p'`
- `nl -ba docs/MILESTONES.md | sed -n '76,86p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '1367,1377p'`
- `nl -ba docs/NEXT_STEPS.md | sed -n '16,16p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '5155,5265p'`
- `nl -ba tests/test_web_app.py | sed -n '17317,17389p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '6299,6385p'`
- `nl -ba README.md | sed -n '184,186p'`
- docs-only verification round이므로 `python3 -m unittest -v`, Playwright, `make e2e-test`는 재실행하지 않았습니다.

## 남은 리스크
- current tree 기준으로 crimson-specific natural-reload follow-up/second-follow-up browser/docs는 negative exclusion과 `namu.wiki`·`ko.wikipedia.org` continuity는 explicit하지만, `blog.example.com` provenance continuity는 generic noisy-single-source family에만 직접 잠겨 있습니다. 이 split은 runtime bug를 즉시 의미하지는 않지만, same query/user-visible path를 읽는 문서와 dedicated browser scenario가 generic family truth보다 약하게 보이게 만듭니다.
- 따라서 다음 라운드는 crimson-specific browser scenarios 2개와 대응 docs만 좁게 건드려 `blog.example.com` provenance continuity를 직접 잠그고, existing generic service/browser truth와 같은 수준으로 맞추는 편이 가장 작고 reviewable합니다.
