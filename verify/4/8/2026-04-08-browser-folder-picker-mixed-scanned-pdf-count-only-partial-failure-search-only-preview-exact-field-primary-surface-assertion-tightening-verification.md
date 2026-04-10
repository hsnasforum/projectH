# browser folder picker mixed scanned-PDF count-only partial-failure search-only preview exact-field primary-surface assertion tightening verification

날짜: 2026-04-08

## 변경 파일
- `verify/4/8/2026-04-08-browser-folder-picker-mixed-scanned-pdf-count-only-partial-failure-search-only-preview-exact-field-primary-surface-assertion-tightening-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest `/work`는 mixed-folder `search-only` count-only partial-failure scenario에서 response-detail preview exact fields, hidden response body/copy button, transcript preview exact fields를 직접 고정했다고 보고했습니다. 이번 라운드에서는 그 tightening이 current tree와 isolated rerun 기준으로 truthful한지 다시 확인해야 했습니다.
- same-day latest `/verify`와 current `.pipeline/claude_handoff.md`는 직전 `search-plus-summary` preview exact-field tightening 기준에 머물러 있었으므로, newer `/work` 기준으로 persistent truth와 다음 한 개의 exact next slice를 다시 고정할 필요가 있었습니다.

## 핵심 변경
- latest `/work`는 truthful했습니다. current [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6591), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6592), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6593), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6594), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6599), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6600), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6604), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6606), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6607), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6608)에 `/work`가 주장한 response-detail/transcript preview exact-field와 hidden response body assertions가 실제로 들어가 있습니다.
- claimed isolated rerun도 재현됐습니다. `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "count-only partial-failure notice" --reporter=line`은 `1 passed (7.2s)`였습니다.
- no-docs, no-runtime widening도 current tree와 맞습니다. `git diff --check -- e2e/tests/web-smoke.spec.mjs`는 clean이었고, 이번 라운드에서 docs surface mismatch는 보이지 않았습니다.
- 다음 슬라이스는 `browser folder picker mixed scanned-PDF count-only partial-failure search-only selected-path/copy + transcript-body-hidden assertion tightening`으로 고정했습니다.
- 근거는 current shipped contract [README.md](/home/xpdlqj/code/projectH/README.md#L47)가 search-only 응답에서 response detail과 transcript의 redundant body hidden을 직접 약속하고, current smoke coverage 설명 [README.md](/home/xpdlqj/code/projectH/README.md#L116), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1325)가 `selected-copy` visibility/click/clipboard verification까지 포함한 search-only primary-surface flow를 이미 고정하는 반면, generic search-only scenario [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L289), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L292), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L294), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L295), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L297), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L314)에서는 selected-path/copy와 transcript body hidden을 직접 고정하지만, current mixed-folder count-only scenario [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6584), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6599), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6600), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6602)부터 [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6610)까지는 아직 selected-path/copy retention과 transcript `pre` hidden 여부를 직접 고정하지 않기 때문입니다.

## 검증
- `sed -n '1,260p' AGENTS.md`
- `sed -n '1,260p' work/README.md`
- `sed -n '1,260p' verify/README.md`
- `sed -n '1,260p' .pipeline/README.md`
- `sed -n '1,260p' work/4/8/2026-04-08-browser-folder-picker-mixed-scanned-pdf-count-only-partial-failure-search-only-preview-exact-field-primary-surface-assertion-tightening.md`
- `sed -n '1,260p' verify/4/8/2026-04-08-browser-folder-picker-mixed-scanned-pdf-partial-failure-search-plus-summary-preview-exact-field-assertion-tightening-verification.md`
- `sed -n '1,260p' .pipeline/claude_handoff.md`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '6574,6610p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '6602,6616p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '271,297p'`
- `nl -ba README.md | sed -n '112,117p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '1323,1326p'`
- `rg -n "count-only partial-failure|mixed scanned-PDF|notes.txt|budget|search-only response|response-text|response-copy-text|search-preview-match|search-preview-name" e2e/tests/web-smoke.spec.mjs README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "count-only partial-failure notice" --reporter=line`
- `git diff --check -- e2e/tests/web-smoke.spec.mjs`
- `git status --short -- .pipeline/claude_handoff.md pipeline_gui/app.py pipeline_gui/view.py tests/test_pipeline_gui_app.py windows-launchers/README.md`
- `python3 -m unittest -v`, `make e2e-test`는 이번 focused browser-smoke verification 범위를 넘어가므로 재실행하지 않았습니다.

## 남은 리스크
- current mixed-folder count-only `search-only` scenario는 아직 selected path list retention, `selected-copy` click/notice/clipboard path, transcript body hidden을 직접 고정하지 않습니다.
- 이번 verification은 latest `/work` truth와 isolated browser rerun, 그리고 다음 slice selection까지만 다뤘으므로 full browser suite health 전체는 다시 판정하지 않았습니다.
