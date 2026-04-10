# browser folder picker mixed scanned-PDF partial-failure search-plus-summary preview exact-field assertion tightening verification

날짜: 2026-04-08

## 변경 파일
- `verify/4/8/2026-04-08-browser-folder-picker-mixed-scanned-pdf-partial-failure-search-plus-summary-preview-exact-field-assertion-tightening-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest `/work`는 mixed-folder `search-plus-summary` partial-failure scenario에서 response-detail과 transcript preview 모두에 ordered label exact text, `title` attribute, match badge를 직접 고정했다고 보고했습니다. 이번 라운드에서는 그 tightening이 current tree와 isolated rerun 기준으로 truthful한지 다시 확인해야 했습니다.
- same-day latest `/verify`와 current `.pipeline/claude_handoff.md`는 직전 transcript preview retention tightening 기준에 머물러 있었으므로, newer `/work` 기준으로 persistent truth와 다음 한 개의 exact next slice를 다시 고정할 필요가 있었습니다.

## 핵심 변경
- latest `/work`는 truthful했습니다. current [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6614), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6615), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6616), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6624), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6625), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6626)에 `/work`가 주장한 exact-field assertions가 실제로 들어가 있습니다.
- claimed isolated rerun도 재현됐습니다. `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "검색\\+요약하면 partial-failure" --reporter=line`은 `1 passed (7.2s)`였습니다.
- no-docs, no-runtime widening도 current tree와 맞습니다. `git diff --check -- e2e/tests/web-smoke.spec.mjs`는 clean이었고, 이번 라운드에서 docs surface mismatch는 보이지 않았습니다.
- 다음 슬라이스는 `browser folder picker mixed scanned-PDF count-only partial-failure search-only preview exact-field primary-surface assertion tightening`으로 고정했습니다.
- 근거는 current shipped contract [README.md](/home/xpdlqj/code/projectH/README.md#L47), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L36)가 search-only 응답에서도 preview ordered label, full path tooltip, match badge, snippet, hidden body를 직접 약속하고, generic search-only scenario [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L274), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L277), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L278), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L279), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L299), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L303), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L304), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L305), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L314)가 exact-field와 hidden-body contract를 이미 직접 고정하는 반면, current mixed-folder count-only scenario [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6584), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6591), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6592), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6593)는 아직 response preview name/snippet containment만 보고 transcript preview와 hidden-body contract는 직접 고정하지 않기 때문입니다.

## 검증
- `sed -n '1,260p' work/4/8/2026-04-08-browser-folder-picker-mixed-scanned-pdf-partial-failure-search-plus-summary-preview-exact-field-assertion-tightening.md`
- `sed -n '1,260p' verify/4/8/2026-04-08-browser-folder-picker-mixed-scanned-pdf-partial-failure-search-plus-summary-transcript-preview-retention-assertion-tightening-verification.md`
- `sed -n '1,260p' .pipeline/claude_handoff.md`
- `rg -n "mixed scanned|partial-failure|search\\+summary|search-plus-summary|preview exact-field|search-preview-name|search-preview-match|title\\\"" e2e/tests/web-smoke.spec.mjs README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '6574,6634p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '268,316p'`
- `nl -ba README.md | sed -n '44,48p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '34,37p'`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "검색\\+요약하면 partial-failure" --reporter=line`
- `git diff --check -- e2e/tests/web-smoke.spec.mjs`
- `git status --short -- .pipeline/claude_handoff.md pipeline_gui/app.py pipeline_gui/view.py tests/test_pipeline_gui_app.py windows-launchers/README.md`
- `python3 -m unittest -v`, `make e2e-test`는 이번 focused browser-smoke verification 범위를 넘어가므로 재실행하지 않았습니다.

## 남은 리스크
- current mixed-folder count-only partial-failure search-only scenario는 아직 preview ordered label exact text, full-path tooltip, match badge, transcript preview visibility, hidden-body contract를 직접 고정하지 않습니다.
- 이번 verification은 latest `/work` truth와 isolated browser rerun, 그리고 다음 slice selection까지만 다뤘으므로 full browser suite health 전체는 다시 판정하지 않았습니다.
