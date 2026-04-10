# browser file picker PDF text-layer readable success smoke coverage verification

날짜: 2026-04-08

## 변경 파일
- `verify/4/8/2026-04-08-browser-file-picker-pdf-text-layer-readable-success-smoke-coverage-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest `/work`는 browser file picker의 readable text-layer PDF positive path를 Playwright smoke로 추가하고, 관련 README/acceptance/milestone/backlog wording을 함께 정렬했다고 보고했습니다. 이번 라운드에서는 그 closeout이 current tree와 실제 rerun 기준으로 truthful한지 다시 확인해야 했습니다.
- same-day latest `/verify`와 current `.pipeline/claude_handoff.md`는 직전 scanned-PDF / partial-failure PDF family에 머물러 있었으므로, newer `/work` 기준으로 persistent truth와 다음 한 개의 exact next slice를 다시 고정할 필요가 있었습니다.

## 핵심 변경
- latest `/work`는 truthful했습니다. current [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L14), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L111), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6591)에 `/work`가 주장한 readable PDF fixture path, fixture 생성, browser file picker scenario가 실제로 존재합니다.
- docs truth-sync도 current tree와 일치합니다. current [README.md](/home/xpdlqj/code/projectH/README.md#L190), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1399), [docs/MILESTONES.md](/home/xpdlqj/code/projectH/docs/MILESTONES.md#L102), [docs/TASK_BACKLOG.md](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L97)은 `/work` 주장대로 browser file picker readable PDF success smoke coverage를 직접 고정하고 있습니다.
- claimed isolated rerun도 재현됐습니다. `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "readable text-layer PDF" --reporter=line`은 `1 passed (6.9s)`였습니다.
- 다음 슬라이스는 `browser file picker readable text-layer PDF extracted-text summary assertion tightening`으로 고정했습니다.
- 근거는 current shipped contract [README.md](/home/xpdlqj/code/projectH/README.md#L66), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L33)가 readable PDF를 실제로 `읽을 수 있어야` 한다고 약속하는 반면, current readable PDF scenario [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6591) 는 OCR 안내 미노출과 filename metadata만 검증하고, fixture comment [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L111)에 직접 적힌 고유 text-layer 문구가 response body나 visible success surface에 나타나는지는 아직 고정하지 않기 때문입니다.

## 검증
- `sed -n '1,220p' AGENTS.md`
- `sed -n '1,220p' work/README.md`
- `sed -n '1,220p' verify/README.md`
- `sed -n '1,220p' .pipeline/README.md`
- `sed -n '1,220p' .agents/skills/round-handoff/SKILL.md`
- `sed -n '1,260p' work/4/8/2026-04-08-browser-file-picker-pdf-text-layer-readable-success-smoke-coverage.md`
- `sed -n '1,260p' verify/4/8/2026-04-08-browser-file-folder-picker-scanned-pdf-ocr-not-supported-guidance-skipped-pdf-partial-failure-smoke-coverage-verification.md`
- `sed -n '1,260p' .pipeline/claude_handoff.md`
- `rg -n "readable text-layer PDF|readable-pdf|text-layer test|scanned-stub|browser file picker|browser folder picker|PDF text-layer" e2e/tests/web-smoke.spec.mjs README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md work/4/8 verify/4/8`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '1,170p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '6580,6645p'`
- `git diff --check -- e2e/tests/web-smoke.spec.mjs README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "readable text-layer PDF" --reporter=line`
- `nl -ba README.md | sed -n '186,194p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '1395,1402p'`
- `nl -ba docs/MILESTONES.md | sed -n '99,103p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '95,98p'`
- `rg -n "readable PDF|text-layer PDF|PDF text-layer|folder picker.*PDF|search.*PDF|pdf.*search|scan\\.pdf|readable-text-layer\\.pdf" e2e/tests/web-smoke.spec.mjs README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md tests/test_smoke.py tests/test_web_app.py work/4/8 verify/4/8`
- `rg -n "browser-folder-input|search-only|response-search-preview|picked-search-folder|선택 결과 요약" e2e/tests/web-smoke.spec.mjs`
- `rg -n "search.*pdf|pdf.*search|text-layer.*search|readable.*pdf|scan\\.pdf|스캔본 또는 이미지형 PDF|건너뛰었습니다" tests/test_smoke.py tests/test_web_app.py`
- `nl -ba tests/test_smoke.py | sed -n '7510,7605p'`
- `nl -ba tests/test_web_app.py | sed -n '6048,6095p'`
- `rg -n "PDF text-layer test: local-first approval-based document assistant|local-first approval-based document assistant" e2e/tests/web-smoke.spec.mjs tests/test_smoke.py tests/test_web_app.py README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md`
- `git status --short -- .pipeline/claude_handoff.md pipeline_gui/app.py pipeline_gui/view.py tests/test_pipeline_gui_app.py windows-launchers/README.md`
- `test -f verify/4/8/2026-04-08-browser-file-picker-pdf-text-layer-readable-success-smoke-coverage-verification.md && echo EXISTS || echo MISSING`
- `git status --short -- .pipeline/claude_handoff.md verify/4/8/2026-04-08-browser-file-picker-pdf-text-layer-readable-success-smoke-coverage-verification.md`
- `git diff --check -- .pipeline/claude_handoff.md`
- `git diff --no-index --check /dev/null verify/4/8/2026-04-08-browser-file-picker-pdf-text-layer-readable-success-smoke-coverage-verification.md`
- `python3 -m unittest -v`, `make e2e-test`는 이번 focused browser-smoke verification 범위를 넘어가므로 재실행하지 않았습니다.

## 남은 리스크
- current readable PDF browser smoke는 success metadata와 OCR 미노출은 고정하지만, fixture의 actual text-layer content가 current visible success surface에 나타나는지는 아직 직접 고정하지 않습니다.
- 이번 verification은 latest `/work` truth, isolated browser rerun, 다음 slice selection까지만 다뤘으므로 full browser suite health 전체는 다시 판정하지 않았습니다.
