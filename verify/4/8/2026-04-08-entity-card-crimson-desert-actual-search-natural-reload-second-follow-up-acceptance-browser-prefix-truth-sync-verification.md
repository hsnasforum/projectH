# entity-card crimson-desert actual-search natural-reload second-follow-up acceptance browser-prefix truth-sync verification

날짜: 2026-04-08

## 변경 파일
- `verify/4/8/2026-04-08-entity-card-crimson-desert-actual-search-natural-reload-second-follow-up-acceptance-browser-prefix-truth-sync-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest `/work`는 `docs/ACCEPTANCE_CRITERIA.md:1376` 한 줄의 browser-prefix truth-sync가 current tree 기준으로 실제 반영됐다고 보고했습니다. 이번 라운드에서는 그 docs-only change가 truthful한지 다시 확인해야 했습니다.
- same natural-reload docs family에서 crimson-desert set이 닫힌 만큼, 다음 Claude 라운드는 남아 있는 latest-update natural-reload docs browser-prefix gap을 한 coherent docs slice로만 넘겨야 했습니다.

## 핵심 변경
- latest `/work`의 observable end state는 truthful하셨습니다. [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1376)는 `/work`가 주장한 `entity-card 붉은사막 actual-search browser 자연어 reload 후 두 번째 follow-up` framing으로 실제 반영돼 있었고, sibling docs [README.md](/home/xpdlqj/code/projectH/README.md#L165)와 current test truth [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L5047)와 정렬됩니다.
- docs-only claimed check도 truthful했습니다. `git diff -- docs/ACCEPTANCE_CRITERIA.md`는 empty였고, `git diff --check -- docs/ACCEPTANCE_CRITERIA.md`는 clean이었습니다.
- next slice는 `latest-update natural-reload docs browser-prefix wording clarification`으로 고정했습니다. current docs [README.md](/home/xpdlqj/code/projectH/README.md#L171), [README.md](/home/xpdlqj/code/projectH/README.md#L172), [README.md](/home/xpdlqj/code/projectH/README.md#L173), [README.md](/home/xpdlqj/code/projectH/README.md#L174), [README.md](/home/xpdlqj/code/projectH/README.md#L175), [README.md](/home/xpdlqj/code/projectH/README.md#L176), [README.md](/home/xpdlqj/code/projectH/README.md#L177), [README.md](/home/xpdlqj/code/projectH/README.md#L178), [README.md](/home/xpdlqj/code/projectH/README.md#L179), [README.md](/home/xpdlqj/code/projectH/README.md#L180), [README.md](/home/xpdlqj/code/projectH/README.md#L181), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1380), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1381), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1382), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1383), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1384), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1385), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1386), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1387), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1388), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1389), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1390)는 mixed-source/single-source/news-only/noisy-community natural-reload truth를 적고 있지만 `browser 자연어 reload` framing을 direct prefix로는 충분히 드러내지 않습니다. 반면 sibling docs [docs/MILESTONES.md](/home/xpdlqj/code/projectH/docs/MILESTONES.md#L89), [docs/MILESTONES.md](/home/xpdlqj/code/projectH/docs/MILESTONES.md#L90), [docs/MILESTONES.md](/home/xpdlqj/code/projectH/docs/MILESTONES.md#L91), [docs/MILESTONES.md](/home/xpdlqj/code/projectH/docs/MILESTONES.md#L92), [docs/MILESTONES.md](/home/xpdlqj/code/projectH/docs/MILESTONES.md#L93), [docs/MILESTONES.md](/home/xpdlqj/code/projectH/docs/MILESTONES.md#L94), [docs/MILESTONES.md](/home/xpdlqj/code/projectH/docs/MILESTONES.md#L95), [docs/TASK_BACKLOG.md](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L78), [docs/TASK_BACKLOG.md](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L79), [docs/TASK_BACKLOG.md](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L80), [docs/TASK_BACKLOG.md](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L81), [docs/TASK_BACKLOG.md](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L82), [docs/TASK_BACKLOG.md](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L83), [docs/TASK_BACKLOG.md](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L84), [docs/TASK_BACKLOG.md](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L85), [docs/TASK_BACKLOG.md](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L86), [docs/TASK_BACKLOG.md](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L87), [docs/TASK_BACKLOG.md](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L88)와 current browser smoke titles [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L5395), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L5456), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L5513), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L5573), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L5638), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L5707), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L5768), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L5833), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L5897), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L5965), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6034)가 같은 natural-reload family를 직접 고정하므로, README/acceptance wording만 그 축에 맞추는 편이 가장 작은 same-family current-risk reduction입니다.

## 검증
- `sed -n '1,220p' AGENTS.md`
- `sed -n '1,220p' work/README.md`
- `sed -n '1,220p' verify/README.md`
- `sed -n '1,220p' .pipeline/README.md`
- `sed -n '1,220p' .agents/skills/round-handoff/SKILL.md`
- `sed -n '1,260p' work/4/8/2026-04-08-entity-card-crimson-desert-actual-search-natural-reload-second-follow-up-acceptance-browser-prefix-truth-sync.md`
- `sed -n '1,260p' verify/4/8/2026-04-08-entity-card-dual-probe-natural-reload-docs-browser-prefix-wording-clarification-verification.md`
- `sed -n '1,240p' docs/NEXT_STEPS.md`
- `git status --short`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '1376,1394p'`
- `nl -ba README.md | sed -n '165,185p'`
- `nl -ba docs/MILESTONES.md | sed -n '84,97p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '73,92p'`
- `rg -n "latest-update .*자연어 reload|latest-update noisy community source.*자연어 reload" README.md docs/ACCEPTANCE_CRITERIA.md`
- `rg -n "latest-update .*자연어 reload|noisy community source.*자연어 reload|noisy single-source claim.*자연어 reload" e2e/tests/web-smoke.spec.mjs`
- `git diff -- docs/ACCEPTANCE_CRITERIA.md`
- `git diff --check -- docs/ACCEPTANCE_CRITERIA.md`
- `python3 -m unittest -v`, `make e2e-test`, Playwright rerun은 이번 docs-only verification 범위를 넘어가므로 재실행하지 않았습니다.

## 남은 리스크
- crimson-desert natural-reload acceptance truth-sync는 이번 라운드로 닫혔지만, latest-update natural-reload docs는 README/acceptance에서 아직 `browser 자연어 reload` framing이 mixed-source/single-source/news-only/noisy-community 전 구간에 걸쳐 sibling docs만큼 직접적이지 않습니다.
- entity-card noisy single-source claim natural-reload docs와 other family wording gap은 이번 verification 범위 밖이라 재판정하지 않았습니다.
