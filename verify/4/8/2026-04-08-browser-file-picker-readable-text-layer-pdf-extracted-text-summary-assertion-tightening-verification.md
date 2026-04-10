# browser file picker readable text-layer PDF extracted-text summary assertion tightening verification

날짜: 2026-04-08

## 변경 파일
- `verify/4/8/2026-04-08-browser-file-picker-readable-text-layer-pdf-extracted-text-summary-assertion-tightening-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest `/work`는 기존 readable PDF browser file picker scenario에 extracted-text assertion 1줄만 추가해, 실제 text-layer가 읽혀 응답에 반영되는지를 더 직접적으로 고정했다고 보고했습니다. 이번 라운드에서는 그 same-scenario tightening이 current tree와 실제 rerun 기준으로 truthful한지 다시 확인해야 했습니다.
- same-day latest `/verify`와 current `.pipeline/claude_handoff.md`는 직전 readable PDF success smoke coverage handoff에 머물러 있었으므로, newer `/work` 기준으로 persistent truth와 다음 한 개의 exact next slice를 다시 고정할 필요가 있었습니다.

## 핵심 변경
- latest `/work`는 truthful했습니다. current [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6591) scenario에는 `/work`가 주장한 extracted-text assertion이 실제로 들어가 있으며, current [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6602)는 `local-first approval-based document assistant`가 response body에 포함되는지를 직접 검증합니다.
- `/work`가 말한 no-docs, no-runtime widening도 current tree와 맞습니다. 이번 라운드에서 실제 code delta는 [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6602) 한 줄 tightening 범위로 보였고, `git diff --check -- e2e/tests/web-smoke.spec.mjs`는 clean이었습니다.
- claimed isolated rerun도 재현됐습니다. `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "readable text-layer PDF" --reporter=line`은 `1 passed (6.6s)`였습니다.
- 다음 슬라이스는 `browser folder picker mixed scanned-PDF partial-failure successful-result retention assertion tightening`으로 고정했습니다.
- 근거는 current shipped contract [README.md](/home/xpdlqj/code/projectH/README.md#L67), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L35)가 partial-failure notice와 함께 “successfully read files의 결과는 계속 반환된다”는 점까지 약속하는 반면, current mixed-folder browser scenario [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6574) 는 [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6587), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6588)의 partial-failure notice만 검증하고, readable file result가 preview에 남아 있는지까지는 아직 직접 고정하지 않기 때문입니다.

## 검증
- `sed -n '1,220p' AGENTS.md`
- `sed -n '1,220p' work/README.md`
- `sed -n '1,220p' verify/README.md`
- `sed -n '1,220p' .pipeline/README.md`
- `sed -n '1,220p' .agents/skills/round-handoff/SKILL.md`
- `sed -n '1,260p' work/4/8/2026-04-08-browser-file-picker-readable-text-layer-pdf-extracted-text-summary-assertion-tightening.md`
- `sed -n '1,260p' verify/4/8/2026-04-08-browser-file-picker-pdf-text-layer-readable-success-smoke-coverage-verification.md`
- `sed -n '1,260p' .pipeline/claude_handoff.md`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '6590,6608p'`
- `rg -n "local-first approval-based document assistant|readable-text-layer.pdf|PDF text-layer reading|text-layer reading|partial-failure notice|OCR-not-supported guidance" README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md e2e/tests/web-smoke.spec.mjs work/4/8 verify/4/8`
- `git status --short -- .pipeline/claude_handoff.md pipeline_gui/app.py pipeline_gui/view.py tests/test_pipeline_gui_app.py windows-launchers/README.md`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '6570,6592p'`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "readable text-layer PDF" --reporter=line`
- `git diff --check -- e2e/tests/web-smoke.spec.mjs`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '224,242p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '272,288p'`
- `test -f verify/4/8/2026-04-08-browser-file-picker-readable-text-layer-pdf-extracted-text-summary-assertion-tightening-verification.md && echo EXISTS || echo MISSING`
- `git status --short -- .pipeline/claude_handoff.md verify/4/8/2026-04-08-browser-file-picker-readable-text-layer-pdf-extracted-text-summary-assertion-tightening-verification.md`
- `git diff --check -- .pipeline/claude_handoff.md`
- `git diff --no-index --check /dev/null verify/4/8/2026-04-08-browser-file-picker-readable-text-layer-pdf-extracted-text-summary-assertion-tightening-verification.md`
- `python3 -m unittest -v`, `make e2e-test`는 이번 focused browser-smoke verification 범위를 넘어가므로 재실행하지 않았습니다.

## 남은 리스크
- current mixed-folder PDF search smoke는 partial-failure notice는 고정하지만, readable file result retention 자체는 아직 직접 고정하지 않습니다.
- 이번 verification은 latest `/work` truth, isolated browser rerun, 다음 slice selection까지만 다뤘으므로 full browser suite health 전체는 다시 판정하지 않았습니다.
