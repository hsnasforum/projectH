# PDF top-level text-layer + OCR-not-supported contract wording clarification verification

날짜: 2026-04-08

## 변경 파일
- `verify/4/8/2026-04-08-pdf-top-level-text-layer-ocr-not-supported-contract-wording-clarification-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest `/work`는 PDF top-level contract docs를 readable text-layer success와 scanned/image-only OCR guidance의 current behavior에 맞게 정렬했다고 보고했습니다. 이번 라운드에서는 그 docs-only closeout이 current tree와 current smoke 기준으로 truthful한지 다시 확인해야 했습니다.
- same-day latest `/verify`와 current `.pipeline/claude_handoff.md`는 직전 scanned/image-only PDF docs wording clarification 기준에 머물러 있었으므로, newer `/work` 기준으로 persistent truth와 다음 한 개의 exact next slice를 다시 고정할 필요가 있었습니다.

## 핵심 변경
- latest `/work`는 truthful했습니다. current [README.md](/home/xpdlqj/code/projectH/README.md#L66), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L33), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L34), [docs/MILESTONES.md](/home/xpdlqj/code/projectH/docs/MILESTONES.md#L98), [docs/MILESTONES.md](/home/xpdlqj/code/projectH/docs/MILESTONES.md#L99), [docs/TASK_BACKLOG.md](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L22)는 `/work` 주장대로 readable text-layer success exact fields와 scanned/image-only OCR guidance exact fields를 반영하는 top-level wording으로 정렬돼 있었습니다.
- 이 wording은 current smoke truth와 맞습니다. readable PDF smoke [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6669), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6673), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6674), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6675), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6676)와 scanned/image-only smoke [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6566), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6568), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6569), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6570), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6571)가 각각 문서의 exact behavior를 뒷받침합니다.
- `git diff -- README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md`는 empty였고, `git diff --check -- README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md`도 clean이었습니다.
- 다음 슬라이스는 `browser file picker readable text-layer PDF transcript-meta exact-field smoke tightening`으로 고정했습니다.
- 근거는 current readable PDF smoke [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6662)부터 [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6677)까지가 quick meta와 context box만 직접 고정하고 transcript meta는 아직 직접 고정하지 않는 반면, broader smoke contract [README.md](/home/xpdlqj/code/projectH/README.md#L114), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1323)와 generic file-picker summary smoke [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L199), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L200), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L201), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L202)는 browser file picker summary flow의 quick-meta + transcript-meta `문서 요약` contract를 이미 약속하고 있기 때문입니다. PDF parsing path에서 같은 사용자-visible meta contract를 직접 고정하는 것이 같은 family의 가장 작은 current-risk reduction입니다.

## 검증
- `sed -n '1,260p' work/4/8/2026-04-08-pdf-top-level-text-layer-ocr-not-supported-contract-wording-clarification.md`
- `sed -n '1,260p' verify/4/8/2026-04-08-browser-file-picker-scanned-image-only-pdf-docs-exact-field-wording-clarification-verification.md`
- `sed -n '1,260p' .pipeline/claude_handoff.md`
- `nl -ba README.md | sed -n '64,68p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '33,36p'`
- `nl -ba docs/MILESTONES.md | sed -n '98,100p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '21,23p'`
- `nl -ba README.md | sed -n '112,116p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '1322,1324p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '189,205p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '6559,6572p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '6662,6677p'`
- `git diff -- README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md`
- `git diff --check -- README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md`
- docs-only 검수 범위라 Playwright, `python3 -m unittest -v`, `make e2e-test`는 재실행하지 않았습니다.

## 남은 리스크
- current readable text-layer PDF dedicated smoke는 transcript meta의 source filename / `문서 요약` label을 아직 직접 고정하지 않습니다.
- 이번 verification은 latest `/work` truth와 docs/current smoke 대조, 그리고 다음 slice selection까지만 다뤘으므로 full browser suite health 전체는 다시 판정하지 않았습니다.
