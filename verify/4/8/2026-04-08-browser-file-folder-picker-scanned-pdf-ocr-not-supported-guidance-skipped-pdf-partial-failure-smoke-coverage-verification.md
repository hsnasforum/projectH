# browser file/folder picker scanned-PDF OCR-not-supported guidance + skipped-PDF partial-failure smoke coverage verification

날짜: 2026-04-08

## 변경 파일
- `verify/4/8/2026-04-08-browser-file-folder-picker-scanned-pdf-ocr-not-supported-guidance-skipped-pdf-partial-failure-smoke-coverage-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest `/work`는 browser file/folder picker에서 scanned/image-only PDF OCR 미지원 안내와 skipped-PDF partial-failure notice를 Playwright smoke로 추가하고, 관련 README/acceptance/milestone/backlog wording을 함께 정렬했다고 보고했습니다. 이번 라운드에서는 그 closeout이 current tree와 실제 rerun 기준으로 truthful한지 다시 확인해야 했습니다.
- same-day latest `/verify`와 current `.pipeline/claude_handoff.md`는 직전 acceptance-wording family에 머물러 있었으므로, newer `/work` 기준으로 persistent truth와 다음 한 개의 exact next slice를 다시 고정할 필요가 있었습니다.

## 핵심 변경
- latest `/work`는 truthful했습니다. current [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6552), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6567)에 `/work`가 주장한 두 browser smoke scenario가 실제로 존재합니다.
- docs truth-sync도 current tree와 일치합니다. current [README.md](/home/xpdlqj/code/projectH/README.md#L188), [README.md](/home/xpdlqj/code/projectH/README.md#L189), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1397), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1398), [docs/MILESTONES.md](/home/xpdlqj/code/projectH/docs/MILESTONES.md#L100), [docs/MILESTONES.md](/home/xpdlqj/code/projectH/docs/MILESTONES.md#L101), [docs/TASK_BACKLOG.md](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L95), [docs/TASK_BACKLOG.md](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L96)은 `/work` 주장대로 browser-level scanned-PDF OCR guidance 및 mixed-folder partial-failure smoke coverage를 직접 고정하고 있습니다.
- claimed isolated rerun도 재현됐습니다. `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "scanned/image-only PDF" --reporter=line`은 `1 passed (6.8s)`, `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "count-only partial-failure notice" --reporter=line`은 `1 passed (6.5s)`였습니다.
- 다음 슬라이스는 `browser file picker PDF text-layer readable success smoke coverage`로 고정했습니다.
- 근거는 current shipped contract [README.md](/home/xpdlqj/code/projectH/README.md#L66), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L33)가 positive PDF text-layer reading을 이미 약속하는 반면, current browser picker success coverage는 [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L184), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L185)의 markdown file case와 이번 라운드로 닫힌 scanned/partial-failure negative paths뿐이고, repo-wide search 기준 readable text-layer PDF를 browser file picker로 성공시키는 Playwright smoke는 아직 없습니다.

## 검증
- `sed -n '1,260p' work/4/8/2026-04-08-browser-file-folder-picker-scanned-pdf-ocr-not-supported-guidance-skipped-pdf-partial-failure-smoke-coverage.md`
- `sed -n '1,260p' verify/4/8/2026-04-08-latest-update-news-only-natural-reload-follow-up-second-follow-up-acceptance-exact-field-wording-clarification-verification.md`
- `sed -n '1,220p' .pipeline/claude_handoff.md`
- `git status --short -- .pipeline/claude_handoff.md pipeline_gui/app.py pipeline_gui/view.py tests/test_pipeline_gui_app.py windows-launchers/README.md`
- `rg -n "scanned/image-only PDF|count-only partial-failure notice|ensureLongFixture|scan\\.pdf|browser-file-input|browser-folder-input" e2e/tests/web-smoke.spec.mjs`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '1,240p'`
- `nl -ba README.md | sed -n '186,200p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '1393,1405p'`
- `nl -ba docs/MILESTONES.md | sed -n '97,103p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '91,99p'`
- `git diff --check -- e2e/tests/web-smoke.spec.mjs README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "scanned/image-only PDF" --reporter=line`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "count-only partial-failure notice" --reporter=line`
- `rg -n "PDF text-layer|text layer|OCR|scanned/image-only PDF|partial-failure notice|pdf" e2e/tests/web-smoke.spec.mjs README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md work/4/8 verify/4/8`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '1,140p'`
- `rg -n "fixtureDir|pdf|PDF|picked-file-name|pickBrowserFile|ensureLongFixture|summary-mode" e2e/tests/web-smoke.spec.mjs`
- `rg -n "text layer|text-layer|PDF files with a text layer|pdf.*can be read|pdf.*요약|PDF" tests/test_smoke.py tests/test_web_app.py`
- `rg --files -g '*.pdf'`
- `rg -n "browser-file-input|picked-file-name|scanned/image-only PDF|count-only partial-failure notice" e2e/tests/web-smoke.spec.mjs`
- `git status --short -- .pipeline/claude_handoff.md verify/4/8/2026-04-08-browser-file-folder-picker-scanned-pdf-ocr-not-supported-guidance-skipped-pdf-partial-failure-smoke-coverage-verification.md`
- `git diff --check -- .pipeline/claude_handoff.md`
- `git diff --no-index --check /dev/null verify/4/8/2026-04-08-browser-file-folder-picker-scanned-pdf-ocr-not-supported-guidance-skipped-pdf-partial-failure-smoke-coverage-verification.md`
- `python3 -m unittest -v`, `make e2e-test`는 이번 focused browser-smoke verification 범위를 넘어가므로 재실행하지 않았습니다.

## 남은 리스크
- current shipped contract의 positive path인 readable text-layer PDF browser file picker success는 아직 Playwright smoke로 직접 고정되지 않았습니다.
- 이번 verification은 latest `/work` truth, 두 개의 isolated browser rerun, 다음 slice selection까지만 다뤘으므로 full browser suite health 전체는 다시 판정하지 않았습니다.
