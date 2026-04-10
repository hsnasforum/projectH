# browser folder picker mixed scanned-PDF count-only partial-failure search-only selected-path/copy + transcript-body-hidden assertion tightening verification

날짜: 2026-04-08

## 변경 파일
- `verify/4/8/2026-04-08-browser-folder-picker-mixed-scanned-pdf-count-only-partial-failure-search-only-selected-path-copy-transcript-body-hidden-assertion-tightening-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest `/work`는 mixed-folder `search-only` count-only partial-failure scenario에 selected path retention, `selected-copy` click/notice/clipboard path, transcript body hidden assertions를 추가해 same scenario의 primary-surface contract를 더 완전히 닫았다고 보고했습니다. 이번 라운드에서는 그 tightening이 current tree와 isolated rerun 기준으로 truthful한지 다시 확인해야 했습니다.
- same-day latest `/verify`와 current `.pipeline/claude_handoff.md`는 직전 preview exact-field tightening 기준에 머물러 있었으므로, newer `/work` 기준으로 persistent truth와 다음 한 개의 exact next slice를 다시 고정할 필요가 있었습니다.

## 핵심 변경
- latest `/work`는 truthful했습니다. current [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6613), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6616), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6618), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6619), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6621), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6624)에 `/work`가 주장한 selected-path/copy와 transcript body hidden assertions가 실제로 들어가 있습니다.
- claimed isolated rerun도 재현됐습니다. `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "count-only partial-failure notice" --reporter=line`은 `1 passed (7.5s)`였습니다.
- latest `/work`가 말한 `docs/runtime 무변경`도 current tree와 맞습니다. `git diff --check -- e2e/tests/web-smoke.spec.mjs README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md`는 clean이었고, change surface는 same scenario tightening에 머물렀습니다.
- 다음 슬라이스는 `browser folder picker mixed scanned-PDF count-only partial-failure search-only docs exact-field wording clarification`으로 고정했습니다.
- 근거는 current smoke scenario [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6574)부터 [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6624)까지가 이제 notice만이 아니라 readable file preview exact fields, selected path retention, `selected-copy`, transcript body hidden까지 직접 고정하는 반면, current scenario-level docs [README.md](/home/xpdlqj/code/projectH/README.md#L189), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1398), [docs/MILESTONES.md](/home/xpdlqj/code/projectH/docs/MILESTONES.md#L101), [docs/TASK_BACKLOG.md](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L96)는 아직 `count-only partial-failure notice` 표시만 적고 있어 current smoke truth를 덜 반영하기 때문입니다.

## 검증
- `sed -n '1,220p' AGENTS.md`
- `sed -n '1,220p' work/README.md`
- `sed -n '1,220p' verify/README.md`
- `sed -n '1,220p' .pipeline/README.md`
- `sed -n '1,260p' work/4/8/2026-04-08-browser-folder-picker-mixed-scanned-pdf-count-only-partial-failure-search-only-selected-path-copy-transcript-body-hidden-assertion-tightening.md`
- `sed -n '1,260p' verify/4/8/2026-04-08-browser-folder-picker-mixed-scanned-pdf-count-only-partial-failure-search-only-preview-exact-field-primary-surface-assertion-tightening-verification.md`
- `sed -n '1,260p' .pipeline/claude_handoff.md`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '6574,6622p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '6621,6628p'`
- `nl -ba README.md | sed -n '186,192p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '1396,1401p'`
- `nl -ba docs/MILESTONES.md | sed -n '99,104p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '94,99p'`
- `rg -n "selected-copy|선택 경로를 복사했습니다|search-only hides|transcript body|pre\\)\\.toHaveCount\\(0\\)|mixed-search-folder/notes.txt|count-only partial-failure notice" e2e/tests/web-smoke.spec.mjs README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "count-only partial-failure notice" --reporter=line`
- `git diff --check -- e2e/tests/web-smoke.spec.mjs README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md`
- `git status --short -- .pipeline/claude_handoff.md pipeline_gui/app.py pipeline_gui/view.py tests/test_pipeline_gui_app.py windows-launchers/README.md`
- `python3 -m unittest -v`, `make e2e-test`는 이번 focused browser-smoke verification 범위를 넘어가므로 재실행하지 않았습니다.

## 남은 리스크
- current mixed-folder count-only search-only scenario-level docs는 actual smoke가 고정한 preview exact fields, selected path/copy, transcript hidden 범위를 아직 직접 반영하지 않습니다.
- 이번 verification은 latest `/work` truth와 isolated browser rerun, 그리고 다음 slice selection까지만 다뤘으므로 full browser suite health 전체는 다시 판정하지 않았습니다.
