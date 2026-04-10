# history-card latest-update news-only click-reload initial milestone/backlog verification-label/source-path exact-field wording clarification verification

날짜: 2026-04-08

## 변경 파일
- `verify/4/8/2026-04-08-history-card-latest-update-news-only-click-reload-initial-milestone-backlog-verification-label-source-path-exact-field-wording-clarification-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest `/work`는 history-card latest-update news-only click-reload initial planning-doc 4줄을 `verification-label/source-path exact-field drift-prevention` wording으로 정렬했다고 보고했습니다. 이번 라운드에서는 그 docs-only closeout이 current tree 기준으로 실제 반영됐는지 다시 확인해야 했습니다.
- 동시에 same-day latest `/verify`는 직전 single-source initial verification에 머물러 있었고, `.pipeline/claude_handoff.md`는 news-only initial slice를 next slice로 가리키고 있었으므로, newer `/work` 기준으로 persistent truth와 다음 한 슬라이스를 다시 고정할 필요가 있었습니다.

## 핵심 변경
- latest `/work`는 truthful했습니다. current [docs/MILESTONES.md](/home/xpdlqj/code/projectH/docs/MILESTONES.md#L56), [docs/MILESTONES.md](/home/xpdlqj/code/projectH/docs/MILESTONES.md#L57), [docs/TASK_BACKLOG.md](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L45), [docs/TASK_BACKLOG.md](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L46)은 모두 `/work` 주장대로 exact-field drift-prevention wording으로 반영돼 있습니다.
- `/work`가 주장한 docs-only verification도 재현됐습니다. `git diff -- docs/MILESTONES.md docs/TASK_BACKLOG.md`는 empty였고, `git diff --check -- docs/MILESTONES.md docs/TASK_BACKLOG.md`는 clean이었습니다. 추가로 `git diff -- README.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/ACCEPTANCE_CRITERIA.md`도 empty였고, 같은 범위의 `git diff --check`도 clean이었습니다.
- 다음 슬라이스는 `history-card latest-update mixed-source click-reload follow-up milestone/backlog source-path + response-origin exact-field wording clarification`으로 고정했습니다. current planning docs [docs/MILESTONES.md](/home/xpdlqj/code/projectH/docs/MILESTONES.md#L62), [docs/TASK_BACKLOG.md](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L51)은 아직 generic `source-path + response-origin continuity` framing으로 남아 있습니다.
- 반면 current shipped root docs [README.md](/home/xpdlqj/code/projectH/README.md#L144), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1353)와 current smoke title [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L3281)는 `store.steampowered.com`, `yna.co.kr`, `WEB`, `최신 확인`, `공식+기사 교차 확인`, `보조 기사`, `공식 기반`을 이미 직접 고정합니다. same latest-update click-reload follow-up family 안에서 mixed-source planning pair는 2줄만 정렬하면 되는 가장 작은 current-risk reduction이고, single-source/news-only follow-up은 각각 4줄 세트라 더 큽니다.

## 검증
- `sed -n '1,140p' AGENTS.md`
- `sed -n '1,180p' work/README.md`
- `sed -n '1,200p' verify/README.md`
- `sed -n '1,180p' .pipeline/README.md`
- `sed -n '1,220p' work/4/8/2026-04-08-history-card-latest-update-news-only-click-reload-initial-milestone-backlog-verification-label-source-path-exact-field-wording-clarification.md`
- `sed -n '1,240p' verify/4/8/2026-04-08-history-card-latest-update-single-source-click-reload-initial-milestone-backlog-verification-label-source-path-exact-field-wording-clarification-verification.md`
- `sed -n '1,260p' .pipeline/claude_handoff.md`
- `nl -ba docs/MILESTONES.md | sed -n '48,100p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '37,100p'`
- `nl -ba README.md | sed -n '133,181p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '1342,1392p'`
- `ls work/4/8 | sort`
- `ls verify/4/8 | sort`
- `sed -n '1,220p' work/4/8/2026-04-08-history-card-latest-update-click-reload-mixed-source-response-origin-exact-field-wording-clarification.md`
- `sed -n '1,220p' work/4/8/2026-04-08-history-card-latest-update-click-reload-single-source-browser-anchor-source-path-exact-field-wording-clarification.md`
- `sed -n '1,220p' work/4/8/2026-04-08-history-card-latest-update-click-reload-news-only-browser-anchor-source-path-exact-field-wording-clarification.md`
- `nl -ba docs/MILESTONES.md | sed -n '56,64p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '45,53p'`
- `nl -ba README.md | sed -n '138,146p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '1347,1355p'`
- `rg -n "history-card latest-update (single-source|news-only|mixed-source).*follow-up" e2e/tests/web-smoke.spec.mjs`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '3281,3296p;2599,2614p;2712,2727p;3470,3486p;3574,3590p'`
- `git diff -- README.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/ACCEPTANCE_CRITERIA.md`
- `git diff --check -- README.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/ACCEPTANCE_CRITERIA.md`
- `git diff -- docs/MILESTONES.md docs/TASK_BACKLOG.md`
- `git diff --check -- docs/MILESTONES.md docs/TASK_BACKLOG.md`
- `git status --short -- .pipeline/claude_handoff.md README.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/ACCEPTANCE_CRITERIA.md e2e/tests/web-smoke.spec.mjs pipeline_gui/app.py pipeline_gui/view.py tests/test_pipeline_gui_app.py windows-launchers/README.md verify/4/8/2026-04-08-history-card-latest-update-single-source-click-reload-initial-milestone-backlog-verification-label-source-path-exact-field-wording-clarification-verification.md`
- `test -f verify/4/8/2026-04-08-history-card-latest-update-news-only-click-reload-initial-milestone-backlog-verification-label-source-path-exact-field-wording-clarification-verification.md && echo exists || echo missing`
- `git status --short -- .pipeline/claude_handoff.md verify/4/8/2026-04-08-history-card-latest-update-news-only-click-reload-initial-milestone-backlog-verification-label-source-path-exact-field-wording-clarification-verification.md`
- `git diff --check -- .pipeline/claude_handoff.md`
- `git diff --no-index --check /dev/null verify/4/8/2026-04-08-history-card-latest-update-news-only-click-reload-initial-milestone-backlog-verification-label-source-path-exact-field-wording-clarification-verification.md`
- Playwright rerun, `python3 -m unittest -v`, `make e2e-test`는 이번 docs-only verification 범위를 넘어가므로 재실행하지 않았습니다.

## 남은 리스크
- latest-update news-only click-reload initial planning-doc 4줄은 이번 라운드로 닫혔지만, same latest-update click-reload follow-up family의 mixed-source planning pair [docs/MILESTONES.md](/home/xpdlqj/code/projectH/docs/MILESTONES.md#L62), [docs/TASK_BACKLOG.md](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L51)는 아직 generic continuity wording으로 남아 있습니다.
- 이번 verification은 latest docs-only `/work` truth와 next slice selection까지만 다뤘으므로, browser/runtime health 자체는 다시 판정하지 않았습니다.
