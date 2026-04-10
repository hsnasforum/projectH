# docs: PRODUCT_PROPOSAL project-brief ACCEPTANCE_CRITERIA panel richness truth sync verification

## 변경 파일
- `verify/4/9/2026-04-09-docs-product-proposal-project-brief-acceptance-panel-richness-truth-sync-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work`가 남아 있던 3개 panel-richness residual을 실제로 richer shipped wording과 맞췄는지 다시 확인해야 했습니다.
- direct target이 truthful하더라도, `/work`가 주장한 `unenriched — 0건`과 same-family closure까지 수용할 수 있는지는 별도로 좁게 재대조해야 했습니다.

## 핵심 변경
- 최신 `/work`의 직접 수정 대상은 truthful합니다.
  - `docs/PRODUCT_PROPOSAL.md:65`
  - `docs/project-brief.md:89`
  - `docs/ACCEPTANCE_CRITERIA.md:32`
- 위 줄들은 richer shipped panel wording과 맞습니다.
  - `README.md:79`
  - `docs/PRODUCT_SPEC.md:338`
  - `docs/PRODUCT_SPEC.md:361`
- 다만 latest `/work`의 `unenriched — 0건`과 `남은 리스크 없음`은 과합니다.
  - same-family rendering/source-of-truth residual이 아직 남아 있습니다.
    - `docs/PRODUCT_SPEC.md:107`
    - `docs/PRODUCT_SPEC.md:361`
    - `README.md:137`
    - `docs/NEXT_STEPS.md:22`
    - `docs/MILESTONES.md:41`
    - `docs/TASK_BACKLOG.md:26`
- 위 줄들은 dedicated plain-language explanation까지는 반영했지만, current richer family wording 대비 `source role with trust level labels` 또는 `fact-strength summary bar` detail을 아직 드러내지 않습니다.
- 따라서 latest `/work`는 direct target 기준으로는 truthful하지만, same-family closure까지는 아직 수용하기 어렵습니다.

## 검증
- `sed -n '1,240p' work/4/9/2026-04-09-docs-product-proposal-project-brief-acceptance-panel-richness-truth-sync.md`
- `sed -n '1,240p' verify/4/9/2026-04-09-docs-remaining-web-investigation-surface-richness-truth-sync-verification.md`
- `git diff --check`
- `nl -ba docs/PRODUCT_PROPOSAL.md | sed -n '63,65p'`
- `nl -ba docs/project-brief.md | sed -n '87,89p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '27,32p'`
- `nl -ba README.md | sed -n '78,79p;136,137p'`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '106,107p;338,339p;360,361p'`
- `nl -ba docs/NEXT_STEPS.md | sed -n '21,22p'`
- `nl -ba docs/MILESTONES.md | sed -n '40,41p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '25,26p'`
- `rg -n --no-heading 'claim coverage panel with status tags, actionable hints, and dedicated plain-language focus-slot reinvestigation explanation|claim-coverage panel with status tags, actionable hints, and dedicated plain-language focus-slot reinvestigation explanation|claim coverage or verification state where applicable' AGENTS.md CLAUDE.md PROJECT_CUSTOM_INSTRUCTIONS.md README.md docs`
- `bash -lc "rg -n --no-heading 'claim coverage panel with status tags, actionable hints, and dedicated plain-language focus-slot reinvestigation explanation|claim-coverage panel with status tags, actionable hints, and dedicated plain-language focus-slot reinvestigation explanation|claim coverage or verification state where applicable' AGENTS.md CLAUDE.md PROJECT_CUSTOM_INSTRUCTIONS.md README.md docs | rg -v 'source role with trust level labels|fact-strength summary bar' || true"`
- Python unit test와 Playwright는 재실행하지 않았습니다. 최신 `/work`가 docs-only이고 code/test/runtime 변경을 주장하지 않았기 때문입니다.

## 남은 리스크
- latest `/work`의 direct target은 truthful합니다.
- 하지만 same-family rendering/source-of-truth residual 6줄이 남아 있어 family closure는 아직 아닙니다.
- 다음 라운드에서는 `docs/PRODUCT_SPEC.md`, `README.md`, `docs/NEXT_STEPS.md`, `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md`의 remaining claim-coverage rendering richness를 한 번에 닫는 bounded bundle이 적절합니다.
