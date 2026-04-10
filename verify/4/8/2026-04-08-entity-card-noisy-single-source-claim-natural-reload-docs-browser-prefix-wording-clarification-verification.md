# entity-card noisy single-source claim natural-reload docs browser-prefix wording clarification verification

날짜: 2026-04-08

## 변경 파일
- `verify/4/8/2026-04-08-entity-card-noisy-single-source-claim-natural-reload-docs-browser-prefix-wording-clarification-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest `/work`는 `README.md:184-185`, `docs/ACCEPTANCE_CRITERIA.md:1393-1394`의 entity-card noisy single-source claim natural-reload docs wording을 `browser 자연어 reload` framing으로 맞췄다고 보고했습니다. 이번 라운드에서는 그 docs-only change가 current tree 기준으로 실제 반영됐는지 다시 확인해야 했습니다.
- 동시에 previous `/verify`가 지적했던 natural-reload docs family closure mismatch가 이번 라운드로 실제 해소됐는지 확인하고, same-family 기준으로 다음 한 슬라이스를 다시 고정해야 했습니다.

## 핵심 변경
- latest `/work`의 docs change는 truthful하셨습니다. [README.md](/home/xpdlqj/code/projectH/README.md#L184), [README.md](/home/xpdlqj/code/projectH/README.md#L185), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1393), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1394)에 `/work`가 주장한 `browser 자연어 reload 후` framing이 실제로 반영돼 있었습니다.
- `/work`가 주장한 docs-only check도 truthful했습니다. `git diff -- README.md docs/ACCEPTANCE_CRITERIA.md`는 empty였고, `git diff --check -- README.md docs/ACCEPTANCE_CRITERIA.md`는 clean이었습니다.
- `/work` closeout 전체도 이번에는 truthful했습니다. `rg -n "자연어 reload" README.md docs/ACCEPTANCE_CRITERIA.md | rg -v "browser 자연어 reload"`가 no-match였으므로, `/work`의 `natural-reload docs browser-prefix family 전체 closure` 판단은 current docs 기준으로 맞습니다.
- 다음 슬라이스는 `history-card entity-card noisy single-source claim click-reload follow-up + second-follow-up docs exact-field wording clarification`으로 고정했습니다. current docs [README.md](/home/xpdlqj/code/projectH/README.md#L186), [README.md](/home/xpdlqj/code/projectH/README.md#L187), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1395), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1396)는 same noisy single-source claim family의 click-reload follow-up/second-follow-up contract를 적고 있지만, current browser smoke title [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6393), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6462)와 sibling docs [docs/MILESTONES.md](/home/xpdlqj/code/projectH/docs/MILESTONES.md#L97), [docs/TASK_BACKLOG.md](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L93), [docs/TASK_BACKLOG.md](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L94)에 비해 click-reload exact-field framing이 덜 직접적입니다.

## 검증
- `nl -ba AGENTS.md | sed -n '1,260p'`
- `nl -ba work/README.md | sed -n '1,240p'`
- `nl -ba verify/README.md | sed -n '1,240p'`
- `nl -ba .pipeline/README.md | sed -n '1,260p'`
- `nl -ba .agents/skills/round-handoff/SKILL.md | sed -n '1,240p'`
- `nl -ba work/4/8/2026-04-08-entity-card-noisy-single-source-claim-natural-reload-docs-browser-prefix-wording-clarification.md | sed -n '1,220p'`
- `nl -ba verify/4/8/2026-04-08-latest-update-natural-reload-docs-browser-prefix-wording-clarification-verification.md | sed -n '1,240p'`
- `nl -ba docs/NEXT_STEPS.md | sed -n '1,240p'`
- `git status --short`
- `nl -ba README.md | sed -n '184,187p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '1393,1396p'`
- `nl -ba docs/MILESTONES.md | sed -n '97,97p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '91,94p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '6244,6468p'`
- `git diff -- README.md docs/ACCEPTANCE_CRITERIA.md`
- `git diff --check -- README.md docs/ACCEPTANCE_CRITERIA.md`
- `rg -n "자연어 reload" README.md docs/ACCEPTANCE_CRITERIA.md | rg -v "browser 자연어 reload"`
- Playwright rerun, `python3 -m unittest -v`, `make e2e-test`는 이번 docs-only verification 범위를 넘어가므로 재실행하지 않았습니다.

## 남은 리스크
- natural-reload docs browser-prefix family는 이번 라운드로 닫혔지만, same noisy single-source claim family의 click-reload docs [README.md](/home/xpdlqj/code/projectH/README.md#L186), [README.md](/home/xpdlqj/code/projectH/README.md#L187), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1395), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1396)는 아직 별도 wording 정렬 대상입니다.
- 이번 verification은 docs-only 범위였으므로 browser rerun이나 broader end-to-end health는 다시 판정하지 않았습니다.
