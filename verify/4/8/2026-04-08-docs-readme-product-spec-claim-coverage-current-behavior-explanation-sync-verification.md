## 변경 파일
- `verify/4/8/2026-04-08-docs-readme-product-spec-claim-coverage-current-behavior-explanation-sync-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest `/work` `work/4/8/2026-04-08-docs-readme-product-spec-claim-coverage-current-behavior-explanation-sync.md`가 실제 문서 상태와 맞는지 다시 확인하고, 같은 claim-coverage 문서 family에서 남은 다음 한 개 슬라이스를 정해야 했습니다.
- same-day latest `/verify`와 기존 `.pipeline/claude_handoff.md`는 `README.md` / `docs/MILESTONES.md` / `docs/TASK_BACKLOG.md` smoke inventory sync 라운드 기준이었으므로, 이번 `README.md` / `docs/PRODUCT_SPEC.md` current-behavior sync 결과에 맞춰 persistent verification과 next handoff를 갱신할 필요가 있었습니다.

## 핵심 변경
- latest `/work`는 truthful하다고 확인했습니다.
  - `README.md:69`는 실제로 claim-coverage panel을 status tags, actionable hints, source-role trust labels, fact-strength summary bar, 그리고 `dedicated plain-language focus-slot reinvestigation explanation (improved/regressed/unchanged)`까지 포함해 설명합니다.
  - `docs/PRODUCT_SPEC.md:106`, `docs/PRODUCT_SPEC.md:154`, `docs/PRODUCT_SPEC.md:310`도 focus-slot reinvestigation explanation을 current behavior로 반영하고 있습니다.
  - `rg -n "claim coverage panel|focus-slot reinvestigation explanation|slot reinvestigation scaffolding" README.md docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md docs/NEXT_STEPS.md docs/project-brief.md docs/PRODUCT_PROPOSAL.md -S` 결과 기준으로 `README.md`와 `docs/PRODUCT_SPEC.md`에는 더 이상 `slot reinvestigation scaffolding`가 남아 있지 않았습니다.
- `/work`가 적은 verification claim도 그대로 맞았습니다.
  - `git diff -- README.md docs/PRODUCT_SPEC.md`는 clean이었고, `git diff --check`도 clean이었습니다.
- 다음 exact slice는 `Docs project-brief PRODUCT_PROPOSAL claim-coverage current-behavior explanation sync`로 고정했습니다.
  - `docs/project-brief.md:81`는 아직 `claim coverage panel with status tags and actionable hints`까지만 적고 있습니다.
  - `docs/PRODUCT_PROPOSAL.md:61`도 같은 old wording에 머물러 있습니다.
  - 반면 `README.md:69`, `docs/PRODUCT_SPEC.md:106`, `docs/ACCEPTANCE_CRITERIA.md:41`, `docs/ACCEPTANCE_CRITERIA.md:1337`, `docs/NEXT_STEPS.md:16`은 이미 focus-slot explanation을 shipped/current behavior로 적고 있어, root `docs/` 안에서도 high-level brief/proposal 계층이 뒤처져 있습니다.
  - 따라서 남은 가장 선명한 same-family current-risk는 `docs/project-brief.md` / `docs/PRODUCT_PROPOSAL.md`의 claim-coverage current-behavior wording drift라고 판단했습니다.
- `.pipeline/claude_handoff.md`도 위 판단에 맞춰 새 next slice 기준으로 갱신했습니다.

## 검증
- `sed -n '1,240p' work/4/8/2026-04-08-docs-readme-product-spec-claim-coverage-current-behavior-explanation-sync.md`
- `sed -n '1,240p' verify/4/8/2026-04-08-docs-readme-milestones-task-backlog-claim-coverage-smoke-inventory-truth-sync-verification.md`
- `sed -n '1,260p' .pipeline/claude_handoff.md`
- `nl -ba README.md | sed -n '66,70p'`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '104,107p'`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '152,155p'`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '308,312p'`
- `rg -n "claim coverage panel|focus-slot reinvestigation explanation|slot reinvestigation scaffolding" README.md docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md docs/NEXT_STEPS.md docs/project-brief.md docs/PRODUCT_PROPOSAL.md -S`
- `git diff -- README.md docs/PRODUCT_SPEC.md`
- `git diff --check`
- `sed -n '1,120p' docs/project-brief.md`
- `sed -n '1,120p' docs/PRODUCT_PROPOSAL.md`

## 남은 리스크
- `docs/project-brief.md:81`와 `docs/PRODUCT_PROPOSAL.md:61`는 아직 claim-coverage panel을 status tags와 actionable hints 수준으로만 적고 있습니다.
- 이 두 문서는 `README.md`에서 root `docs/` current product docs로 직접 연결되고 있어, lower-level contract docs보다 늦게 남아 있는 wording drift가 이후에도 혼선을 줄 수 있습니다.
- unrelated dirty worktree(`.gitignore`, `.pipeline/README.md`, `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `PROJECT_CUSTOM_INSTRUCTIONS.md`, `pipeline_gui/*`, `watcher_core.py`, 관련 tests, `work/README.md`, `verify/README.md`, `report/gemini/README.md`, 기타 unrelated `work/` / `verify/` note)는 이번 검증 범위 밖이라 손대지 않았습니다.
