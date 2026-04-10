# history-card latest-update noisy-community click-reload initial docs exact-field wording clarification verification

날짜: 2026-04-08

## 변경 파일
- `verify/4/8/2026-04-08-history-card-latest-update-noisy-community-click-reload-initial-docs-exact-field-wording-clarification-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest `/work`는 history-card latest-update noisy-community click-reload initial root docs 4곳을 exact-field exclusion + positive-retention wording으로 정렬했다고 보고했습니다. 이번 라운드에서는 그 docs-only change가 current tree 기준으로 실제 반영됐는지 다시 확인해야 했습니다.
- 동시에 same-day latest `/verify`와 `.pipeline/claude_handoff.md`는 방금 닫힌 docs slice를 아직 next slice로 가리키고 있었으므로, newer `/work`에 맞춰 current truth와 다음 한 슬라이스를 다시 고정할 필요가 있었습니다.

## 핵심 변경
- latest `/work`는 truthful했습니다. current [README.md](/home/xpdlqj/code/projectH/README.md#L133), [docs/MILESTONES.md](/home/xpdlqj/code/projectH/docs/MILESTONES.md#L51), [docs/TASK_BACKLOG.md](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L40), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1342)는 모두 `보조 커뮤니티` / `brunch` 미노출뿐 아니라 `기사 교차 확인`, `보조 기사`, `hankyung.com`, `mk.co.kr` positive retention까지 직접 드러내는 wording으로 반영돼 있었습니다.
- `/work`가 주장한 docs-only verification도 재현됐습니다. `git diff -- README.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/ACCEPTANCE_CRITERIA.md`는 empty였고, `git diff --check -- README.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/ACCEPTANCE_CRITERIA.md`는 clean이었습니다.
- 다음 슬라이스는 `history-card latest-update mixed-source click-reload initial milestone/backlog source-path + response-origin exact-field wording clarification`으로 고정했습니다. current planning docs [docs/MILESTONES.md](/home/xpdlqj/code/projectH/docs/MILESTONES.md#L54)와 [docs/TASK_BACKLOG.md](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L43)는 아직 generic `source-path + response-origin continuity` framing으로 남아 있습니다.
- 반면 current shipped root docs [README.md](/home/xpdlqj/code/projectH/README.md#L136), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1345)와 current smoke titles [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L1222), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L2086)는 `store.steampowered.com`, `yna.co.kr`, `WEB`, `최신 확인`, `공식+기사 교차 확인`, `보조 기사`, `공식 기반`을 더 직접적으로 고정합니다. same latest-update click-reload family 안에서 남아 있는 가장 작은 planning-doc current-risk reduction으로는 initial mixed-source line pair를 exact-field wording으로 정렬하는 편이 가장 작고 truthful합니다.

## 검증
- `sed -n '1,220p' AGENTS.md`
- `sed -n '1,220p' work/README.md`
- `sed -n '1,240p' verify/README.md`
- `sed -n '1,220p' .pipeline/README.md`
- `sed -n '1,220p' .agents/skills/round-handoff/SKILL.md`
- `sed -n '1,220p' docs/NEXT_STEPS.md`
- `sed -n '1,240p' work/4/8/2026-04-08-history-card-latest-update-noisy-community-click-reload-initial-docs-exact-field-wording-clarification.md`
- `sed -n '1,260p' verify/4/8/2026-04-08-history-card-latest-update-noisy-community-click-reload-initial-exclusion-exact-field-smoke-clarification-verification.md`
- `sed -n '1,240p' .pipeline/claude_handoff.md`
- `nl -ba README.md | sed -n '130,187p'`
- `nl -ba docs/MILESTONES.md | sed -n '48,97p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '37,95p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '1339,1396p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '1218,1230p;2082,2092p'`
- `ls work/4/8 | rg 'mixed-source.*(milestone|backlog)|dual-probe.*(milestone|backlog)|single-source.*(milestone|backlog)|news-only.*(milestone|backlog)'`
- `ls verify/4/8 | rg 'mixed-source.*(milestone|backlog)|dual-probe.*(milestone|backlog)|single-source.*(milestone|backlog)|news-only.*(milestone|backlog)'`
- `git diff -- README.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/ACCEPTANCE_CRITERIA.md`
- `git diff --check -- README.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/ACCEPTANCE_CRITERIA.md`
- `git status --short -- .pipeline/claude_handoff.md README.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/ACCEPTANCE_CRITERIA.md e2e/tests/web-smoke.spec.mjs pipeline_gui/app.py pipeline_gui/view.py tests/test_pipeline_gui_app.py windows-launchers/README.md`
- Playwright rerun, `python3 -m unittest -v`, `make e2e-test`는 이번 docs-only verification 범위를 넘어가므로 재실행하지 않았습니다.

## 남은 리스크
- latest-update noisy-community click-reload initial root docs 4곳은 이번 라운드로 닫혔지만, same latest-update click-reload family의 initial mixed-source planning lines [docs/MILESTONES.md](/home/xpdlqj/code/projectH/docs/MILESTONES.md#L54), [docs/TASK_BACKLOG.md](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L43)는 아직 generic continuity wording으로 남아 있습니다.
- 이번 verification은 latest docs-only `/work` truth와 next slice selection까지만 다뤘으므로, browser/runtime health 자체는 다시 판정하지 않았습니다.
