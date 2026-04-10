# browser folder picker mixed scanned-PDF partial-failure successful-result retention assertion tightening verification

날짜: 2026-04-08

## 변경 파일
- `verify/4/8/2026-04-08-browser-folder-picker-mixed-scanned-pdf-partial-failure-successful-result-retention-assertion-tightening-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest `/work`는 기존 mixed-folder scanned-PDF partial-failure browser scenario에 successful-result retention assertion 3줄만 추가해, readable file 결과가 실제로 preview에 남는지를 same scenario에서 더 직접적으로 고정했다고 보고했습니다. 이번 라운드에서는 그 tightening이 current tree와 실제 rerun 기준으로 truthful한지 다시 확인해야 했습니다.
- same-day latest `/verify`와 current `.pipeline/claude_handoff.md`는 직전 readable-PDF file picker tightening handoff에 머물러 있었으므로, newer `/work` 기준으로 persistent truth와 다음 한 개의 exact next slice를 다시 고정할 필요가 있었습니다.

## 핵심 변경
- latest `/work`는 truthful했습니다. current [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6574)는 mixed-folder partial-failure scenario를 유지하고 있고, current [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6591), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6592), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6593)에 `/work`가 주장한 preview retention assertion 3줄이 실제로 들어가 있습니다.
- `/work`가 말한 no-docs, no-runtime widening도 current tree와 맞습니다. 이번 라운드에서 actual change surface는 [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6591), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6592), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6593) 같은 same-scenario tightening 범위로 보였고, `git diff --check -- e2e/tests/web-smoke.spec.mjs`는 clean이었습니다.
- claimed isolated rerun도 재현됐습니다. `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "count-only partial-failure notice" --reporter=line`은 `1 passed (6.8s)`였습니다.
- 다음 슬라이스는 `browser folder picker mixed scanned-PDF partial-failure search-plus-summary preview retention smoke coverage`로 고정했습니다.
- 근거는 current shipped contract [README.md](/home/xpdlqj/code/projectH/README.md#L47), [README.md](/home/xpdlqj/code/projectH/README.md#L67), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L35), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L36)가 partial-failure notice와 함께 both `search-only` and `search-plus-summary` preview retention을 약속하는 반면, current mixed-folder scenario [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6580)는 아직 `#search-only`를 체크한 variant에만 묶여 있기 때문입니다. existing generic search-plus-summary preview assertions [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L229), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L241)를 mixed-folder fixture에 재사용하는 편이 가장 작은 same-family current-risk reduction입니다.

## 검증
- `sed -n '1,220p' AGENTS.md`
- `sed -n '1,220p' work/README.md`
- `sed -n '1,220p' verify/README.md`
- `sed -n '1,220p' .pipeline/README.md`
- `sed -n '1,220p' .agents/skills/round-handoff/SKILL.md`
- `sed -n '1,260p' work/4/8/2026-04-08-browser-folder-picker-mixed-scanned-pdf-partial-failure-successful-result-retention-assertion-tightening.md`
- `sed -n '1,260p' verify/4/8/2026-04-08-browser-file-picker-readable-text-layer-pdf-extracted-text-summary-assertion-tightening-verification.md`
- `sed -n '1,260p' .pipeline/claude_handoff.md`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '6574,6594p'`
- `rg -n "count-only partial-failure notice|search-only|성공적으로 읽은|successfully read files|partial-failure" README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md e2e/tests/web-smoke.spec.mjs tests/test_smoke.py tests/test_web_app.py`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "count-only partial-failure notice" --reporter=line`
- `git diff --check -- e2e/tests/web-smoke.spec.mjs`
- `nl -ba README.md | sed -n '45,68p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '33,36p'`
- `git status --short -- .pipeline/claude_handoff.md pipeline_gui/app.py pipeline_gui/view.py tests/test_pipeline_gui_app.py windows-launchers/README.md`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '224,242p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '272,288p'`
- `test -f verify/4/8/2026-04-08-browser-folder-picker-mixed-scanned-pdf-partial-failure-successful-result-retention-assertion-tightening-verification.md && echo EXISTS || echo MISSING`
- `git status --short -- .pipeline/claude_handoff.md verify/4/8/2026-04-08-browser-folder-picker-mixed-scanned-pdf-partial-failure-successful-result-retention-assertion-tightening-verification.md`
- `git diff --check -- .pipeline/claude_handoff.md`
- `git diff --no-index --check /dev/null verify/4/8/2026-04-08-browser-folder-picker-mixed-scanned-pdf-partial-failure-successful-result-retention-assertion-tightening-verification.md`
- `python3 -m unittest -v`, `make e2e-test`는 이번 focused browser-smoke verification 범위를 넘어가므로 재실행하지 않았습니다.

## 남은 리스크
- current mixed-folder partial-failure browser smoke는 `search-only` variant에서는 result retention을 직접 고정하지만, same contract family의 `search-plus-summary` variant는 아직 직접 Playwright로 고정되지 않았습니다.
- 이번 verification은 latest `/work` truth, isolated browser rerun, 다음 slice selection까지만 다뤘으므로 full browser suite health 전체는 다시 판정하지 않았습니다.
