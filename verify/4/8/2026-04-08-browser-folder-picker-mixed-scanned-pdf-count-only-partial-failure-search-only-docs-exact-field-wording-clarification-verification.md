# browser folder picker mixed scanned-PDF count-only partial-failure search-only docs exact-field wording clarification verification

날짜: 2026-04-08

## 변경 파일
- `verify/4/8/2026-04-08-browser-folder-picker-mixed-scanned-pdf-count-only-partial-failure-search-only-docs-exact-field-wording-clarification-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest `/work`는 mixed-folder `search-only` count-only partial-failure scenario-level docs 4곳을 actual smoke truth에 맞게 exact-field wording으로 정렬했다고 보고했습니다. 이번 라운드에서는 그 docs-only closeout이 current tree와 current smoke 기준으로 truthful한지 다시 확인해야 했습니다.
- same-day latest `/verify`와 current `.pipeline/claude_handoff.md`는 직전 selected-path/copy + transcript-hidden tightening 기준에 머물러 있었으므로, newer `/work` 기준으로 persistent truth와 다음 한 개의 exact next slice를 다시 고정할 필요가 있었습니다.

## 핵심 변경
- latest `/work`는 truthful했습니다. current [README.md](/home/xpdlqj/code/projectH/README.md#L189), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1398), [docs/MILESTONES.md](/home/xpdlqj/code/projectH/docs/MILESTONES.md#L101), [docs/TASK_BACKLOG.md](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L96)는 `/work` 주장대로 notice-only wording이 아니라 preview exact fields, selected path/copy, transcript hidden까지 반영하는 문구로 정렬돼 있었습니다.
- 이 wording은 current smoke truth와 맞습니다. mixed-folder count-only `search-only` scenario [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6591), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6593), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6594), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6613), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6616), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6624)는 각각 `1. notes.txt`, full-path tooltip, `내용 일치`, selected path/copy, transcript hidden을 직접 고정하고 있습니다.
- `git diff -- README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md`는 empty였고, `git diff --check -- README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md`도 clean이었습니다.
- 다음 슬라이스는 `browser folder picker mixed scanned-PDF search-plus-summary docs exact-field wording clarification`으로 고정했습니다.
- 근거는 current mixed-folder `search-plus-summary` smoke [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6643), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6645), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6646), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6647), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6653), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6655), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6656), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6657), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6659)는 이미 response-detail/transcript preview exact fields를 직접 고정하는 반면, current scenario-level docs [README.md](/home/xpdlqj/code/projectH/README.md#L191), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1400), [docs/MILESTONES.md](/home/xpdlqj/code/projectH/docs/MILESTONES.md#L103), [docs/TASK_BACKLOG.md](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L98)는 아직 `notes.txt` preview + `budget` snippet 유지` 수준으로만 적고 있어 exact-field truth를 덜 반영하기 때문입니다.

## 검증
- `sed -n '1,260p' work/4/8/2026-04-08-browser-folder-picker-mixed-scanned-pdf-count-only-partial-failure-search-only-docs-exact-field-wording-clarification.md`
- `sed -n '1,260p' verify/4/8/2026-04-08-browser-folder-picker-mixed-scanned-pdf-count-only-partial-failure-search-only-selected-path-copy-transcript-body-hidden-assertion-tightening-verification.md`
- `sed -n '1,260p' .pipeline/claude_handoff.md`
- `nl -ba README.md | sed -n '186,192p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '1397,1401p'`
- `nl -ba docs/MILESTONES.md | sed -n '100,104p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '95,99p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '6574,6622p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '6627,6660p'`
- `git diff -- README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md`
- `git diff --check -- README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md`
- `git status --short -- .pipeline/claude_handoff.md pipeline_gui/app.py pipeline_gui/view.py tests/test_pipeline_gui_app.py windows-launchers/README.md`
- docs-only 검수 범위라 Playwright, `python3 -m unittest -v`, `make e2e-test`는 재실행하지 않았습니다.

## 남은 리스크
- current mixed-folder `search-plus-summary` scenario-level docs는 actual smoke가 고정한 response-detail/transcript preview exact fields 범위를 아직 직접 반영하지 않습니다.
- 이번 verification은 latest `/work` truth와 docs/current smoke 대조, 그리고 다음 slice selection까지만 다뤘으므로 full browser suite health 전체는 다시 판정하지 않았습니다.
