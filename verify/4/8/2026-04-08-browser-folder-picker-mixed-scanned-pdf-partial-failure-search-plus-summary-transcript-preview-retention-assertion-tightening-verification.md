# browser folder picker mixed scanned-PDF partial-failure search-plus-summary transcript preview retention assertion tightening verification

날짜: 2026-04-08

## 변경 파일
- `verify/4/8/2026-04-08-browser-folder-picker-mixed-scanned-pdf-partial-failure-search-plus-summary-transcript-preview-retention-assertion-tightening-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest `/work`는 기존 mixed-folder `search-plus-summary` partial-failure scenario에 transcript preview retention assertion 4줄만 추가해, response-detail preview뿐 아니라 transcript preview도 same scenario에서 유지되는지를 더 직접적으로 고정했다고 보고했습니다. 이번 라운드에서는 그 tightening이 current tree와 실제 rerun 기준으로 truthful한지 다시 확인해야 했습니다.
- same-day latest `/verify`와 current `.pipeline/claude_handoff.md`는 직전 mixed-folder `search-plus-summary` preview retention smoke coverage handoff에 머물러 있었으므로, newer `/work` 기준으로 persistent truth와 다음 한 개의 exact next slice를 다시 고정할 필요가 있었습니다.

## 핵심 변경
- latest `/work`는 truthful했습니다. current [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6596) scenario에는 `/work`가 주장한 transcript preview retention assertions가 실제로 들어가 있으며, current [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6618), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6619), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6620), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6621), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6622)에 transcript preview panel visibility, item count, `notes.txt`, `budget` snippet retention 검증이 존재합니다.
- `/work`가 말한 no-docs, no-runtime widening도 current tree와 맞습니다. 이번 라운드에서 actual change surface는 [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6618), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6619), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6620), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6621), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6622) 같은 same-scenario tightening 범위로 보였고, `git diff --check -- e2e/tests/web-smoke.spec.mjs`는 clean이었습니다.
- claimed isolated rerun도 재현됐습니다. `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "검색\\+요약하면 partial-failure" --reporter=line`은 `1 passed (6.9s)`였습니다.
- 다음 슬라이스는 `browser folder picker mixed scanned-PDF partial-failure search-plus-summary preview exact-field assertion tightening`으로 고정했습니다.
- 근거는 current shipped contract [README.md](/home/xpdlqj/code/projectH/README.md#L47), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L36)가 preview card의 ordered label, full path tooltip, match badge, snippet까지 직접 약속하고, generic search-plus-summary assertions [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L245), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L248), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L249), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L253), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L254)가 title/match exact-field를 직접 고정하는 반면, current mixed-folder `search-plus-summary` scenario [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6612), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6613), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6614), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6615), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6618), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6619), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6620), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6621), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6622)는 visibility/count/name/snippet까지만 확인하고 title attribute와 match badge는 아직 직접 고정하지 않기 때문입니다.

## 검증
- `sed -n '1,220p' AGENTS.md`
- `sed -n '1,220p' work/README.md`
- `sed -n '1,220p' verify/README.md`
- `sed -n '1,220p' .pipeline/README.md`
- `sed -n '1,220p' .agents/skills/round-handoff/SKILL.md`
- `sed -n '1,260p' work/4/8/2026-04-08-browser-folder-picker-mixed-scanned-pdf-partial-failure-search-plus-summary-transcript-preview-retention-assertion-tightening.md`
- `sed -n '1,260p' verify/4/8/2026-04-08-browser-folder-picker-mixed-scanned-pdf-partial-failure-search-plus-summary-preview-retention-smoke-coverage-verification.md`
- `sed -n '1,260p' .pipeline/claude_handoff.md`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '6596,6630p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '243,256p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '301,312p'`
- `rg -n "search-preview-match|HaveAttribute\\(\\\"title\\\"|full path tooltip|ordered label|내용 일치|파일명 일치" e2e/tests/web-smoke.spec.mjs README.md docs/ACCEPTANCE_CRITERIA.md`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "검색\\+요약하면 partial-failure" --reporter=line`
- `git diff --check -- e2e/tests/web-smoke.spec.mjs`
- `git status --short -- .pipeline/claude_handoff.md pipeline_gui/app.py pipeline_gui/view.py tests/test_pipeline_gui_app.py windows-launchers/README.md`
- `git status --short -- .pipeline/claude_handoff.md verify/4/8/2026-04-08-browser-folder-picker-mixed-scanned-pdf-partial-failure-search-plus-summary-transcript-preview-retention-assertion-tightening-verification.md`
- `git diff --check -- .pipeline/claude_handoff.md`
- `git diff --no-index --check /dev/null verify/4/8/2026-04-08-browser-folder-picker-mixed-scanned-pdf-partial-failure-search-plus-summary-transcript-preview-retention-assertion-tightening-verification.md`
- `python3 -m unittest -v`, `make e2e-test`는 이번 focused browser-smoke verification 범위를 넘어가므로 재실행하지 않았습니다.

## 남은 리스크
- current mixed-folder `search-plus-summary` browser smoke는 response-detail/transcript preview retention은 직접 고정하지만, preview card의 full-path tooltip과 match badge exact-field는 아직 직접 고정하지 않습니다.
- 이번 verification은 latest `/work` truth, isolated browser rerun, 다음 slice selection까지만 다뤘으므로 full browser suite health 전체는 다시 판정하지 않았습니다.
