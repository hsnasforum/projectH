# docs: remaining web-investigation surface richness truth sync verification

## 변경 파일
- `verify/4/9/2026-04-09-docs-remaining-web-investigation-surface-richness-truth-sync-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work`가 남아 있던 web-investigation surface-richness residual을 실제로 current shipped wording과 맞췄는지 다시 확인해야 했습니다.
- direct target이 mostly truthful하더라도, `/work`가 주장한 `unenriched — 0건`과 family closure까지 수용할 수 있는지는 별도로 좁게 재대조해야 했습니다.

## 핵심 변경
- 최신 `/work`의 직접 수정 대상 다수는 truthful합니다.
  - `docs/PRODUCT_SPEC.md:154`
  - `AGENTS.md:45`
  - `CLAUDE.md:24`
  - `PROJECT_CUSTOM_INSTRUCTIONS.md:22`
  - `docs/ARCHITECTURE.md:11`
  - `docs/ARCHITECTURE.md:137`
  - `docs/ARCHITECTURE.md:1372`
  - `docs/PRODUCT_PROPOSAL.md:26`
  - `docs/project-brief.md:15`
  - `docs/NEXT_STEPS.md:21`
  - `docs/TASK_BACKLOG.md:24`
- 위 줄들은 richer badge / panel wording anchor와 맞습니다.
  - `README.md:78`
  - `README.md:79`
  - `docs/PRODUCT_SPEC.md:338`
  - `docs/PRODUCT_SPEC.md:339`
  - `docs/PRODUCT_SPEC.md:359`
  - `docs/PRODUCT_SPEC.md:361`
- 다만 latest `/work`의 `enriched lines — 12건, unenriched — 0건`과 `남은 리스크 없음`은 수용하기 어렵습니다.
  - 아직 same-family unenriched panel summary가 남아 있습니다.
    - `docs/PRODUCT_PROPOSAL.md:65`
    - `docs/project-brief.md:89`
  - previous `/verify`가 이미 residual로 짚었던 variant-form acceptance summary도 그대로 남아 있습니다.
    - `docs/ACCEPTANCE_CRITERIA.md:32`
- 따라서 latest `/work`는 direct target 기준으로는 mostly truthful하지만, same-family closure까지는 아직 수용하기 어렵습니다.

## 검증
- `sed -n '1,240p' work/4/9/2026-04-09-docs-remaining-web-investigation-surface-richness-truth-sync.md`
- `sed -n '1,240p' verify/4/9/2026-04-09-docs-web-investigation-badge-panel-richness-truth-sync-verification.md`
- `git diff --check`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '152,155p;338,339p;359,361p'`
- `nl -ba AGENTS.md | sed -n '45,47p'`
- `nl -ba CLAUDE.md | sed -n '24,26p'`
- `nl -ba PROJECT_CUSTOM_INSTRUCTIONS.md | sed -n '22,24p'`
- `nl -ba docs/ARCHITECTURE.md | sed -n '10,11p;135,137p;1370,1372p'`
- `nl -ba docs/PRODUCT_PROPOSAL.md | sed -n '25,26p;63,65p'`
- `nl -ba docs/project-brief.md | sed -n '14,15p;87,89p'`
- `nl -ba docs/NEXT_STEPS.md | sed -n '20,21p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '24,25p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '27,32p;1364,1366p'`
- `rg -n --no-heading 'claim coverage panel with status tags, actionable hints, and dedicated plain-language focus-slot reinvestigation explanation|claim-coverage panel with status tags, actionable hints, and dedicated plain-language focus-slot reinvestigation explanation|claim coverage or verification state where applicable' AGENTS.md CLAUDE.md PROJECT_CUSTOM_INSTRUCTIONS.md README.md docs`
- `bash -lc "rg -n --no-heading 'claim coverage panel with status tags, actionable hints, and dedicated plain-language focus-slot reinvestigation explanation|claim-coverage panel with status tags, actionable hints, and dedicated plain-language focus-slot reinvestigation explanation|claim coverage or verification state where applicable' AGENTS.md CLAUDE.md PROJECT_CUSTOM_INSTRUCTIONS.md README.md docs | rg -v 'source role with trust level labels|fact-strength summary bar' || true"`
- Python unit test와 Playwright는 재실행하지 않았습니다. 최신 `/work`가 docs-only이고 code/test/runtime 변경을 주장하지 않았기 때문입니다.

## 남은 리스크
- latest `/work`의 direct target은 mostly truthful합니다.
- 하지만 lower-level panel summary 2줄과 acceptance variant summary 1줄이 남아 있어 same-family closure는 아직 아닙니다.
- 다음 라운드에서는 `docs/PRODUCT_PROPOSAL.md`, `docs/project-brief.md`, `docs/ACCEPTANCE_CRITERIA.md`의 remaining web-investigation panel richness를 한 번에 닫는 bounded bundle이 적절합니다.
