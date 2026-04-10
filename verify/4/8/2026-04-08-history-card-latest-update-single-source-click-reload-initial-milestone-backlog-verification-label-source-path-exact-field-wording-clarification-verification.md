# history-card latest-update single-source click-reload initial milestone/backlog verification-label/source-path exact-field wording clarification verification

날짜: 2026-04-08

## 변경 파일
- `verify/4/8/2026-04-08-history-card-latest-update-single-source-click-reload-initial-milestone-backlog-verification-label-source-path-exact-field-wording-clarification-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest `/work`는 history-card latest-update single-source click-reload initial planning-doc 4줄을 `verification-label/source-path exact-field drift-prevention` wording으로 정렬했다고 보고했습니다. 이번 라운드에서는 그 docs-only closeout이 current tree 기준으로 실제 반영됐는지 다시 확인해야 했습니다.
- 동시에 same-day latest `/verify`는 직전 mixed-source initial verification에 머물러 있었고, `.pipeline/claude_handoff.md`는 single-source initial slice를 next slice로 가리키고 있었으므로, newer `/work` 기준으로 persistent truth와 다음 한 슬라이스를 다시 고정할 필요가 있었습니다.

## 핵심 변경
- latest `/work`는 truthful했습니다. current [docs/MILESTONES.md](/home/xpdlqj/code/projectH/docs/MILESTONES.md#L55), [docs/MILESTONES.md](/home/xpdlqj/code/projectH/docs/MILESTONES.md#L58), [docs/TASK_BACKLOG.md](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L44), [docs/TASK_BACKLOG.md](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L47)는 모두 `/work` 주장대로 exact-field drift-prevention wording으로 반영돼 있습니다.
- `/work`가 주장한 docs-only verification도 재현됐습니다. `git diff -- docs/MILESTONES.md docs/TASK_BACKLOG.md`는 empty였고, `git diff --check -- docs/MILESTONES.md docs/TASK_BACKLOG.md`는 clean이었습니다. 추가로 `git diff -- README.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/ACCEPTANCE_CRITERIA.md`도 empty였고, 같은 범위의 `git diff --check`도 clean이었습니다.
- 다음 슬라이스는 `history-card latest-update news-only click-reload initial milestone/backlog verification-label/source-path exact-field wording clarification`으로 고정했습니다. current planning docs [docs/MILESTONES.md](/home/xpdlqj/code/projectH/docs/MILESTONES.md#L56), [docs/MILESTONES.md](/home/xpdlqj/code/projectH/docs/MILESTONES.md#L57), [docs/TASK_BACKLOG.md](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L45), [docs/TASK_BACKLOG.md](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L46)은 아직 generic `verification-label continuity` / `source-path continuity` framing으로 남아 있습니다.
- 반면 current shipped root docs [README.md](/home/xpdlqj/code/projectH/README.md#L138), [README.md](/home/xpdlqj/code/projectH/README.md#L139), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1347), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1348)와 current smoke titles [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L2296), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L2404)는 `기사 교차 확인`, `보조 기사`, `hankyung.com`, `mk.co.kr`를 더 직접적으로 고정합니다. same latest-update click-reload family 안에서 남아 있는 가장 작은 planning-doc current-risk reduction으로는 initial news-only line set을 exact-field wording으로 정렬하는 편이 가장 작고 truthful합니다.

## 검증
- `sed -n '1,120p' AGENTS.md`
- `sed -n '1,160p' work/README.md`
- `sed -n '1,180p' verify/README.md`
- `sed -n '1,160p' .pipeline/README.md`
- `sed -n '1,220p' work/4/8/2026-04-08-history-card-latest-update-single-source-click-reload-initial-milestone-backlog-verification-label-source-path-exact-field-wording-clarification.md`
- `sed -n '1,220p' verify/4/8/2026-04-08-history-card-latest-update-mixed-source-click-reload-initial-milestone-backlog-source-path-response-origin-exact-field-wording-clarification-verification.md`
- `sed -n '1,260p' .pipeline/claude_handoff.md`
- `nl -ba docs/MILESTONES.md | sed -n '55,57p'`
- `nl -ba docs/MILESTONES.md | sed -n '58,58p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '44,46p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '47,47p'`
- `nl -ba README.md | sed -n '137,139p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '1346,1348p'`
- `rg -n "history-card latest-update (single-source|news-only) 다시 불러오기" e2e/tests/web-smoke.spec.mjs`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '2296,2314p;2404,2422p'`
- `git diff -- README.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/ACCEPTANCE_CRITERIA.md`
- `git diff --check -- README.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/ACCEPTANCE_CRITERIA.md`
- `git diff -- docs/MILESTONES.md docs/TASK_BACKLOG.md`
- `git diff --check -- docs/MILESTONES.md docs/TASK_BACKLOG.md`
- `git status --short -- .pipeline/claude_handoff.md README.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/ACCEPTANCE_CRITERIA.md e2e/tests/web-smoke.spec.mjs pipeline_gui/app.py pipeline_gui/view.py tests/test_pipeline_gui_app.py windows-launchers/README.md`
- `git status --short -- .pipeline/claude_handoff.md verify/4/8/2026-04-08-history-card-latest-update-single-source-click-reload-initial-milestone-backlog-verification-label-source-path-exact-field-wording-clarification-verification.md`
- `git diff --check -- .pipeline/claude_handoff.md`
- `git diff --no-index --check /dev/null verify/4/8/2026-04-08-history-card-latest-update-single-source-click-reload-initial-milestone-backlog-verification-label-source-path-exact-field-wording-clarification-verification.md`
- Playwright rerun, `python3 -m unittest -v`, `make e2e-test`는 이번 docs-only verification 범위를 넘어가므로 재실행하지 않았습니다.

## 남은 리스크
- latest-update single-source click-reload initial planning-doc 4줄은 이번 라운드로 닫혔지만, same latest-update click-reload family의 initial news-only planning lines [docs/MILESTONES.md](/home/xpdlqj/code/projectH/docs/MILESTONES.md#L56), [docs/MILESTONES.md](/home/xpdlqj/code/projectH/docs/MILESTONES.md#L57), [docs/TASK_BACKLOG.md](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L45), [docs/TASK_BACKLOG.md](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L46)는 아직 generic continuity wording으로 남아 있습니다.
- 이번 verification은 latest docs-only `/work` truth와 next slice selection까지만 다뤘으므로, browser/runtime health 자체는 다시 판정하지 않았습니다.
