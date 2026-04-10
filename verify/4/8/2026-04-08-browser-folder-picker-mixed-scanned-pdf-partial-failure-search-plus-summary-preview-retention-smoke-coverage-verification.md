# browser folder picker mixed scanned-PDF partial-failure search-plus-summary preview retention smoke coverage verification

날짜: 2026-04-08

## 변경 파일
- `verify/4/8/2026-04-08-browser-folder-picker-mixed-scanned-pdf-partial-failure-search-plus-summary-preview-retention-smoke-coverage-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest `/work`는 mixed scanned-PDF folder partial-failure contract의 `search-plus-summary` variant browser smoke 1개를 추가하고, 관련 README/acceptance/milestone/backlog wording을 함께 정렬했다고 보고했습니다. 이번 라운드에서는 그 closeout이 current tree와 실제 rerun 기준으로 truthful한지 다시 확인해야 했습니다.
- same-day latest `/verify`와 current `.pipeline/claude_handoff.md`는 직전 mixed-folder `search-only` tightening handoff에 머물러 있었으므로, newer `/work` 기준으로 persistent truth와 다음 한 개의 exact next slice를 다시 고정할 필요가 있었습니다.

## 핵심 변경
- latest `/work`는 truthful했습니다. current [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6596)에는 `/work`가 주장한 `search-plus-summary` mixed-folder scenario가 실제로 존재하고, current [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6608), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6609), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6613), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6614), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6615)에 `/work`가 말한 partial-failure notice, visible response body, `notes.txt` preview, `budget` snippet retention assertion이 들어가 있습니다.
- docs truth-sync도 current tree와 일치합니다. current [README.md](/home/xpdlqj/code/projectH/README.md#L191), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1400), [docs/MILESTONES.md](/home/xpdlqj/code/projectH/docs/MILESTONES.md#L103), [docs/TASK_BACKLOG.md](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L98)은 `/work` 주장대로 `search-plus-summary` mixed-folder partial-failure + preview retention smoke coverage를 직접 고정하고 있습니다.
- claimed isolated rerun도 재현됐습니다. `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "검색\\+요약하면 partial-failure" --reporter=line`은 `1 passed (7.4s)`였습니다.
- 다음 슬라이스는 `browser folder picker mixed scanned-PDF partial-failure search-plus-summary transcript preview retention assertion tightening`으로 고정했습니다.
- 근거는 current shipped contract [README.md](/home/xpdlqj/code/projectH/README.md#L47), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L36)가 search result preview panel을 response family 전체에 약속하고, current generic search-plus-summary path [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L243), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L245), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L256)는 transcript preview retention까지 직접 고정하는 반면, current mixed-folder `search-plus-summary` scenario [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6596) 는 response-detail preview만 확인하고 transcript preview retention은 아직 직접 고정하지 않기 때문입니다.

## 검증
- `sed -n '1,220p' AGENTS.md`
- `sed -n '1,220p' work/README.md`
- `sed -n '1,220p' verify/README.md`
- `sed -n '1,220p' .pipeline/README.md`
- `sed -n '1,220p' .agents/skills/round-handoff/SKILL.md`
- `sed -n '1,260p' work/4/8/2026-04-08-browser-folder-picker-mixed-scanned-pdf-partial-failure-search-plus-summary-preview-retention-smoke-coverage.md`
- `sed -n '1,260p' verify/4/8/2026-04-08-browser-folder-picker-mixed-scanned-pdf-partial-failure-successful-result-retention-assertion-tightening-verification.md`
- `sed -n '1,260p' .pipeline/claude_handoff.md`
- `rg -n "검색.*요약하면 partial-failure|search-plus-summary|notes.txt|budget|mixed-folder|count-only partial-failure notice|79\\. 브라우저 폴더 선택|85\\. Browser folder picker" e2e/tests/web-smoke.spec.mjs README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md work/4/8 verify/4/8`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '6590,6635p'`
- `nl -ba README.md | sed -n '188,193p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '1397,1402p'`
- `nl -ba docs/MILESTONES.md | sed -n '100,104p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '95,99p'`
- `git diff --check -- e2e/tests/web-smoke.spec.mjs README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "검색\\+요약하면 partial-failure" --reporter=line`
- `rg -n "transcript preview panel is also visible in search-plus-summary|lastAssistant.*search-preview|search-preview.*transcript|transcript.*search-preview" e2e/tests/web-smoke.spec.mjs README.md docs/ACCEPTANCE_CRITERIA.md`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '240,258p'`
- `git status --short -- .pipeline/claude_handoff.md pipeline_gui/app.py pipeline_gui/view.py tests/test_pipeline_gui_app.py windows-launchers/README.md`
- `git status --short -- .pipeline/claude_handoff.md verify/4/8/2026-04-08-browser-folder-picker-mixed-scanned-pdf-partial-failure-search-plus-summary-preview-retention-smoke-coverage-verification.md`
- `git diff --check -- .pipeline/claude_handoff.md`
- `git diff --no-index --check /dev/null verify/4/8/2026-04-08-browser-folder-picker-mixed-scanned-pdf-partial-failure-search-plus-summary-preview-retention-smoke-coverage-verification.md`
- `python3 -m unittest -v`, `make e2e-test`는 이번 focused browser-smoke verification 범위를 넘어가므로 재실행하지 않았습니다.

## 남은 리스크
- current mixed-folder `search-plus-summary` browser smoke는 response-detail preview retention은 직접 고정하지만, transcript preview retention은 아직 직접 고정하지 않습니다.
- 이번 verification은 latest `/work` truth, isolated browser rerun, 다음 slice selection까지만 다뤘으므로 full browser suite health 전체는 다시 판정하지 않았습니다.
