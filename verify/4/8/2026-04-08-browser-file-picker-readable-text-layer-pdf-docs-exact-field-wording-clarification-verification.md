# browser file picker readable text-layer PDF docs exact-field wording clarification verification

날짜: 2026-04-08

## 변경 파일
- `verify/4/8/2026-04-08-browser-file-picker-readable-text-layer-pdf-docs-exact-field-wording-clarification-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest `/work`는 readable text-layer PDF scenario-level docs 4곳을 actual smoke truth에 맞게 exact-field wording으로 정렬했다고 보고했습니다. 이번 라운드에서는 그 docs-only closeout이 current tree와 current smoke 기준으로 truthful한지 다시 확인해야 했습니다.
- same-day latest `/verify`와 current `.pipeline/claude_handoff.md`는 직전 mixed-folder `search-plus-summary` docs wording clarification 기준에 머물러 있었으므로, newer `/work` 기준으로 persistent truth와 다음 한 개의 exact next slice를 다시 고정할 필요가 있었습니다.

## 핵심 변경
- latest `/work`는 truthful했습니다. current [README.md](/home/xpdlqj/code/projectH/README.md#L190), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1399), [docs/MILESTONES.md](/home/xpdlqj/code/projectH/docs/MILESTONES.md#L102), [docs/TASK_BACKLOG.md](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L97)은 `/work` 주장대로 readable PDF smoke의 visible summary body with extracted text, OCR guidance 미노출, `readable-text-layer.pdf`, quick-meta `문서 요약` 범위를 반영하는 문구로 정렬돼 있었습니다.
- 이 wording은 current smoke truth와 맞습니다. readable PDF smoke [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6669), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6671), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6673), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6674), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6675), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6676)는 각각 OCR guidance 미노출, extracted text 포함 visible summary body, context box/quick meta filename, quick-meta `문서 요약` label을 직접 고정하고 있습니다.
- `git diff -- README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md`는 empty였고, `git diff --check -- README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md`도 clean이었습니다.
- 다음 슬라이스는 `browser file picker scanned-image-only PDF docs exact-field wording clarification`으로 고정했습니다.
- 근거는 current scanned/image-only PDF smoke [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6566), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6568), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6569), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6570), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6571)는 visible OCR-not-supported guidance response와 exact strings `요약할 수 없습니다`, `OCR`, `이미지형 PDF`, `다음 단계:`를 직접 고정하는 반면, current scenario-level docs [README.md](/home/xpdlqj/code/projectH/README.md#L188), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1397), [docs/MILESTONES.md](/home/xpdlqj/code/projectH/docs/MILESTONES.md#L100), [docs/TASK_BACKLOG.md](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L95)는 아직 exact-field truth를 일부만 반영하거나 generic wording에 머무르기 때문입니다.

## 검증
- `sed -n '1,260p' work/4/8/2026-04-08-browser-file-picker-readable-text-layer-pdf-docs-exact-field-wording-clarification.md`
- `sed -n '1,260p' verify/4/8/2026-04-08-browser-folder-picker-mixed-scanned-pdf-search-plus-summary-docs-exact-field-wording-clarification-verification.md`
- `sed -n '1,260p' .pipeline/claude_handoff.md`
- `nl -ba README.md | sed -n '188,191p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '1397,1400p'`
- `nl -ba docs/MILESTONES.md | sed -n '100,103p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '95,98p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '6659,6677p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '6559,6572p'`
- `git diff -- README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md`
- `git diff --check -- README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md`
- `git status --short -- .pipeline/claude_handoff.md pipeline_gui/app.py pipeline_gui/view.py tests/test_pipeline_gui_app.py windows-launchers/README.md`
- docs-only 검수 범위라 Playwright, `python3 -m unittest -v`, `make e2e-test`는 재실행하지 않았습니다.

## 남은 리스크
- current scanned/image-only PDF scenario-level docs는 actual smoke가 고정한 visible response guidance와 exact token 세트를 아직 fully 직접 반영하지 않습니다.
- 이번 verification은 latest `/work` truth와 docs/current smoke 대조, 그리고 다음 slice selection까지만 다뤘으므로 full browser suite health 전체는 다시 판정하지 않았습니다.
