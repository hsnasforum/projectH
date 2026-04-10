# uploaded-folder count-only partial-failure retained-result top-level contract wording clarification verification

날짜: 2026-04-08

## 변경 파일
- `verify/4/8/2026-04-08-uploaded-folder-count-only-partial-failure-retained-result-top-level-contract-wording-clarification-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest `/work`는 uploaded-folder count-only partial-failure의 top-level contract wording 2곳을 retained-result preview truth에 맞게 정리했다고 보고했습니다. 이번 라운드에서는 그 docs-only closeout이 current tree와 current smoke truth 기준으로 truthful한지 다시 확인해야 했습니다.
- same-day latest `/verify`는 직전 PDF top-level transcript-meta wording clarification 기준에 머물러 있었으므로, newer `/work` 기준으로 persistent verification truth와 다음 한 개의 exact next slice를 다시 고정할 필요가 있었습니다.

## 핵심 변경
- latest `/work`는 truthful했습니다. current [README.md](/home/xpdlqj/code/projectH/README.md#L67), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L35)는 `/work` 주장대로 uploaded-folder count-only partial-failure의 top-level contract를 generic `results returned` wording이 아니라 readable-file result preview retention truth로 반영하고 있었습니다.
- 이 wording은 current scenario-level docs와 current smoke truth와 맞습니다. [README.md](/home/xpdlqj/code/projectH/README.md#L189), [README.md](/home/xpdlqj/code/projectH/README.md#L191), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1398), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1400)은 search-only/search-plus-summary 양쪽의 retained-result preview truth를 직접 적고 있고, [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6591), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6603), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6643), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6653)는 preview exact-field retention을 직접 고정합니다.
- `git diff -- README.md docs/ACCEPTANCE_CRITERIA.md`는 empty였고, `git diff --check -- README.md docs/ACCEPTANCE_CRITERIA.md`도 clean이었습니다.
- 다음 슬라이스는 `search-only selected-copy top-level contract wording clarification`으로 고정했습니다.
- 근거는 current top-level search contract [README.md](/home/xpdlqj/code/projectH/README.md#L47), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L36)가 preview cards와 hidden body까지만 적고 `selected-copy` visibility/click/notice/clipboard truth를 직접 반영하지 않는 반면, smoke coverage docs [README.md](/home/xpdlqj/code/projectH/README.md#L116), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1325), pure search-only smoke [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L287), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L289), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L292), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L295), mixed partial-failure search-only smoke [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6599), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6613), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6616), [e2e/tests/web-smoke.spec.mjs](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L6619)는 이미 그 user-visible truth를 직접 고정하고 있기 때문입니다.

## 검증
- `sed -n '1,220p' work/4/8/2026-04-08-uploaded-folder-count-only-partial-failure-retained-result-top-level-contract-wording-clarification.md`
- `sed -n '1,260p' verify/4/8/2026-04-08-pdf-top-level-readable-text-layer-transcript-meta-contract-wording-clarification-verification.md`
- `sed -n '1,220p' work/README.md`
- `sed -n '1,220p' verify/README.md`
- `sed -n '1,220p' .pipeline/README.md`
- `sed -n '1,220p' .agents/skills/round-handoff/SKILL.md`
- `sed -n '1,260p' .pipeline/claude_handoff.md`
- `nl -ba README.md | sed -n '66,68p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '34,36p'`
- `nl -ba README.md | sed -n '189,191p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '1398,1400p'`
- `nl -ba docs/MILESTONES.md | sed -n '100,101p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '95,96p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '6584,6659p'`
- `nl -ba README.md | sed -n '46,47p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '35,36p'`
- `nl -ba README.md | sed -n '115,116p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '1324,1325p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '284,295p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '6598,6621p'`
- `rg -n "uploaded folder search|count-only partial-failure|retained-result|preview" docs/NEXT_STEPS.md README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md -S`
- `git diff -- README.md docs/ACCEPTANCE_CRITERIA.md`
- `git diff --check -- README.md docs/ACCEPTANCE_CRITERIA.md`
- docs-only 검수 범위라 Playwright, `python3 -m unittest -v`, `make e2e-test`는 재실행하지 않았습니다.

## 남은 리스크
- uploaded-folder partial-failure top-level contract는 now retained-result preview truth와 맞지만, top-level search-only contract는 아직 `selected-copy` visibility/click/notice/clipboard truth를 fully 드러내지 않습니다.
- 이번 verification은 latest `/work` truth와 docs/current smoke 대조, 다음 slice selection까지만 다뤘으므로 full browser suite health 전체는 다시 판정하지 않았습니다.
