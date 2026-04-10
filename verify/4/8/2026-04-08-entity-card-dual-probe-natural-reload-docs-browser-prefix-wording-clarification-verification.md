# entity-card dual-probe natural-reload docs browser-prefix wording clarification verification

날짜: 2026-04-08

## 변경 파일
- `verify/4/8/2026-04-08-entity-card-dual-probe-natural-reload-docs-browser-prefix-wording-clarification-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest `/work`는 dual-probe natural-reload docs 10곳의 browser-prefix wording이 current tree 기준으로 실제 반영됐다고 보고했습니다. 이번 라운드에서는 그 docs-only change가 truthful한지 다시 확인해야 했습니다.
- 동시에 latest `/work`의 `남은 리스크`가 이전 crimson-desert natural-reload docs family까지 모두 닫혔다고 적은 부분이 current tree와 완전히 맞는지도 다시 대조해야 했습니다.

## 핵심 변경
- latest `/work`의 직접 수정 대상은 truthful하셨습니다. [README.md](/home/xpdlqj/code/projectH/README.md#L153), [README.md](/home/xpdlqj/code/projectH/README.md#L154), [README.md](/home/xpdlqj/code/projectH/README.md#L155), [README.md](/home/xpdlqj/code/projectH/README.md#L156), [README.md](/home/xpdlqj/code/projectH/README.md#L164), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1362), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1363), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1364), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1365), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1375)에는 `/work`가 주장한 `browser 자연어 reload` framing이 실제로 반영돼 있었고, sibling docs/test가 말하는 dual-probe browser natural-reload contract와 정렬됩니다.
- docs-only claimed check도 truthful했습니다. `git diff -- README.md docs/ACCEPTANCE_CRITERIA.md`는 empty였고, `git diff --check -- README.md docs/ACCEPTANCE_CRITERIA.md`는 clean이었습니다.
- 다만 latest `/work` closeout 전체는 fully truthful하지는 않았습니다. `남은 리스크`는 "붉은사막/zero-strong-slot natural-reload docs도 이전 라운드에서 모두 닫혔다"고 적었지만, current docs [README.md](/home/xpdlqj/code/projectH/README.md#L165)는 이미 `browser 자연어 reload 후 두 번째 follow-up`으로 정렬된 반면 [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1376)는 아직 `entity-card 붉은사막 actual-search 자연어 reload 후 두 번째 follow-up`으로 남아 있어 crimson-desert actual-search second-follow-up acceptance line 1곳이 아직 generic wording입니다.
- next slice는 `entity-card crimson-desert actual-search natural-reload second-follow-up acceptance browser-prefix truth-sync clarification`으로 고정했습니다. current test/body [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L5047), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L5085), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L5088), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L5091)와 sibling docs [README.md](/home/xpdlqj/code/projectH/README.md#L165)는 이미 browser natural-reload second-follow-up contract를 직접 고정하므로, `docs/ACCEPTANCE_CRITERIA.md:1376` 한 줄만 그 축에 맞춰 truth-sync하는 편이 가장 작은 same-family current-risk reduction입니다.

## 검증
- `sed -n '1,220p' AGENTS.md`
- `sed -n '1,220p' work/README.md`
- `sed -n '1,220p' verify/README.md`
- `sed -n '1,220p' .pipeline/README.md`
- `sed -n '1,220p' .agents/skills/round-handoff/SKILL.md`
- `sed -n '1,260p' work/4/8/2026-04-08-entity-card-dual-probe-natural-reload-docs-browser-prefix-wording-clarification.md`
- `sed -n '1,260p' verify/4/8/2026-04-08-entity-card-crimson-desert-natural-reload-second-follow-up-docs-browser-prefix-wording-clarification-verification.md`
- `git status --short`
- `nl -ba README.md | sed -n '152,165p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '1361,1376p'`
- `rg -n "자연어 reload" README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md`
- `rg -n "붉은사막 actual-search .*자연어 reload 후 두 번째 follow-up|붉은사막 .*browser 자연어 reload 후 두 번째 follow-up|붉은사막 browser natural-reload second-follow-up|붉은사막 actual-search browser natural-reload second-follow-up" README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md e2e/tests/web-smoke.spec.mjs`
- `nl -ba docs/MILESTONES.md | sed -n '79,84p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '68,73p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '5047,5093p'`
- `git diff -- README.md docs/ACCEPTANCE_CRITERIA.md`
- `git diff --check -- README.md docs/ACCEPTANCE_CRITERIA.md`
- `python3 -m unittest -v`, `make e2e-test`, Playwright rerun은 이번 docs-only verification 범위를 넘어가므로 재실행하지 않았습니다.

## 남은 리스크
- dual-probe natural-reload docs browser-prefix는 이번 라운드로 닫혔지만, crimson-desert actual-search natural-reload second-follow-up acceptance line 1곳은 아직 generic wording이라 latest `/work`의 family-closure 서술과 current tree 사이에 작은 truth-sync gap이 남아 있습니다.
- latest-update natural-reload docs와 other family wording gap은 이번 verification 범위 밖이라 재판정하지 않았습니다.
