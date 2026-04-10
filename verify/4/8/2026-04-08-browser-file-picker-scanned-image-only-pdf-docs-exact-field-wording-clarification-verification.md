# browser file picker scanned-image-only PDF docs exact-field wording clarification verification

날짜: 2026-04-08

## 변경 파일
- `verify/4/8/2026-04-08-browser-file-picker-scanned-image-only-pdf-docs-exact-field-wording-clarification-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest `/work`는 scanned/image-only PDF scenario-level docs를 actual smoke truth에 맞게 exact-field wording으로 정렬했다고 보고했습니다. 이번 라운드에서는 그 docs-only closeout이 current tree와 current smoke 기준으로 truthful한지 다시 확인해야 했습니다.
- same-day latest `/verify`와 current `.pipeline/claude_handoff.md`는 직전 readable text-layer PDF docs wording clarification 기준에 머물러 있었으므로, newer `/work` 기준으로 persistent truth와 다음 한 개의 exact next slice를 다시 고정할 필요가 있었습니다.

## 핵심 변경
- latest `/work`는 truthful했습니다. current [README.md](/home/xpdlqj/code/projectH/README.md#L188), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1397), [docs/MILESTONES.md](/home/xpdlqj/code/projectH/docs/MILESTONES.md#L100), [docs/TASK_BACKLOG.md](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L95)는 `/work` 주장대로 scanned/image-only PDF smoke의 visible OCR guidance와 exact strings `요약할 수 없습니다`, `OCR`, `이미지형 PDF`, `다음 단계:` 범위를 반영하는 문구로 정렬돼 있었습니다.
- 이 wording은 current smoke truth와 맞습니다. scanned/image-only PDF smoke [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6566), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6568), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6569), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6570), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6571)는 visible response guidance와 4개 exact strings를 직접 고정하고 있습니다.
- `git diff -- README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md`는 empty였고, `git diff --check -- README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md`도 clean이었습니다.
- 다음 슬라이스는 `PDF top-level text-layer + OCR-not-supported contract wording clarification`으로 고정했습니다.
- 근거는 current top-level docs [README.md](/home/xpdlqj/code/projectH/README.md#L66), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L33), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L34), [docs/MILESTONES.md](/home/xpdlqj/code/projectH/docs/MILESTONES.md#L98), [docs/MILESTONES.md](/home/xpdlqj/code/projectH/docs/MILESTONES.md#L99), [docs/TASK_BACKLOG.md](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L22)는 아직 generic `PDF text-layer support` / `OCR-not-supported guidance` 수준에 머무는 반면, current scenario-level smoke와 docs는 already readable text-layer success exact fields와 scanned/image-only OCR guidance exact fields를 직접 고정하고 있기 때문입니다. scenario-level truth-sync가 모두 닫힌 지금은 같은 PDF docs family의 top-level contract wording을 한 coherent slice로 맞추는 편이 가장 작고 reviewable합니다.

## 검증
- `sed -n '1,260p' work/4/8/2026-04-08-browser-file-picker-scanned-image-only-pdf-docs-exact-field-wording-clarification.md`
- `sed -n '1,260p' verify/4/8/2026-04-08-browser-file-picker-readable-text-layer-pdf-docs-exact-field-wording-clarification-verification.md`
- `sed -n '1,260p' .pipeline/claude_handoff.md`
- `nl -ba README.md | sed -n '187,190p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '1396,1399p'`
- `nl -ba docs/MILESTONES.md | sed -n '99,102p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '94,97p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '6559,6572p'`
- `nl -ba README.md | sed -n '64,68p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '33,36p'`
- `nl -ba docs/MILESTONES.md | sed -n '96,100p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '20,23p'`
- `git diff -- README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md`
- `git diff --check -- README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md`
- `git status --short -- .pipeline/claude_handoff.md pipeline_gui/app.py pipeline_gui/view.py tests/test_pipeline_gui_app.py windows-launchers/README.md`
- docs-only 검수 범위라 Playwright, `python3 -m unittest -v`, `make e2e-test`는 재실행하지 않았습니다.

## 남은 리스크
- current PDF top-level contract docs는 scenario-level smoke가 고정한 readable text-layer success exact fields와 scanned/image-only OCR guidance exact fields를 아직 generic wording으로만 요약하고 있습니다.
- 이번 verification은 latest `/work` truth와 docs/current smoke 대조, 그리고 다음 slice selection까지만 다뤘으므로 full browser suite health 전체는 다시 판정하지 않았습니다.
