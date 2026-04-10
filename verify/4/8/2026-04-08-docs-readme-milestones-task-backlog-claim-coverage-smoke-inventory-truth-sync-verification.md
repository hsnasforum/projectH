## 변경 파일
- `verify/4/8/2026-04-08-docs-readme-milestones-task-backlog-claim-coverage-smoke-inventory-truth-sync-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest `/work` `work/4/8/2026-04-08-docs-readme-milestones-task-backlog-claim-coverage-smoke-inventory-truth-sync.md`가 실제 문서 상태와 맞는지 다시 확인하고, same-family 문서 drift 중 다음 한 개 슬라이스를 정해야 했습니다.
- same-day latest `/verify`와 기존 `.pipeline/claude_handoff.md`는 `docs/ACCEPTANCE_CRITERIA.md` truth-sync 라운드 기준이었으므로, 이번 `README.md` / `docs/MILESTONES.md` / `docs/TASK_BACKLOG.md` 반영 결과에 맞춰 persistent verification과 next handoff를 갱신할 필요가 있었습니다.

## 핵심 변경
- latest `/work`는 truthful하다고 확인했습니다.
  - `README.md:127`에 claim-coverage smoke inventory가 `focus-slot reinvestigation explanation (improved/regressed/unchanged with natural Korean particle normalization)`까지 포함하도록 갱신되어 있습니다.
  - `docs/MILESTONES.md:37`과 `docs/TASK_BACKLOG.md:25`도 같은 detail을 포함하도록 실제로 갱신되어 있습니다.
  - `rg -n "focus-slot reinvestigation explanation" README.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/ACCEPTANCE_CRITERIA.md docs/NEXT_STEPS.md docs/PRODUCT_SPEC.md -S` 결과 기준으로 해당 wording은 현재 5개 synced docs에 반영되어 있습니다.
- `/work`가 적은 verification claim도 그대로 맞았습니다.
  - `git diff -- README.md docs/MILESTONES.md docs/TASK_BACKLOG.md`는 clean이었고, `git diff --check`도 clean이었습니다.
- 다음 exact slice는 `Docs README PRODUCT_SPEC claim-coverage current-behavior explanation sync`로 고정했습니다.
  - `README.md:69`은 현재 shipped claim-coverage panel을 status tags, actionable hints, source-role trust labels, fact-strength summary bar까지만 적고 있고, plain-language focus-slot explanation line은 빠져 있습니다.
  - `docs/PRODUCT_SPEC.md:106`, `docs/PRODUCT_SPEC.md:154`, `docs/PRODUCT_SPEC.md:310`도 claim coverage panel을 status tags / actionable hints / fact-strength summary bar 또는 `slot reinvestigation scaffolding` 수준으로만 설명합니다.
  - 반면 `docs/ACCEPTANCE_CRITERIA.md:41`, `docs/ACCEPTANCE_CRITERIA.md:1337`, `docs/NEXT_STEPS.md:16`, `README.md:127`은 이미 focus-slot explanation을 현재 shipped behavior 또는 current smoke contract로 적고 있어, high-level current-behavior docs와 lower-level contract docs 사이 설명 층위 drift가 남아 있습니다.
  - 따라서 남은 가장 선명한 same-family current-risk는 `README.md` / `docs/PRODUCT_SPEC.md`의 current-behavior wording drift라고 판단했습니다.
- `.pipeline/claude_handoff.md`도 위 판단에 맞춰 새 next slice 기준으로 갱신했습니다.

## 검증
- `sed -n '1,240p' work/4/8/2026-04-08-docs-readme-milestones-task-backlog-claim-coverage-smoke-inventory-truth-sync.md`
- `sed -n '1,240p' verify/4/8/2026-04-08-docs-acceptance-criteria-playwright-count-claim-coverage-gate-inventory-truth-sync-verification.md`
- `sed -n '1,260p' .pipeline/claude_handoff.md`
- `nl -ba README.md | sed -n '124,129p'`
- `nl -ba docs/MILESTONES.md | sed -n '35,38p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '23,26p'`
- `rg -n "focus-slot reinvestigation explanation" README.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/ACCEPTANCE_CRITERIA.md docs/NEXT_STEPS.md docs/PRODUCT_SPEC.md -S`
- `git diff -- README.md docs/MILESTONES.md docs/TASK_BACKLOG.md`
- `git diff --check`
- `rg -n "slot reinvestigation scaffolding|leading status tags, actionable hints|leading status tags and actionable hints|focus-slot reinvestigation explanation|claim coverage panel" docs README.md -S`
- `nl -ba README.md | sed -n '64,71p'`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '100,108p'`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '150,156p'`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '306,313p'`

## 남은 리스크
- `README.md:69`와 `docs/PRODUCT_SPEC.md:106`, `docs/PRODUCT_SPEC.md:154`, `docs/PRODUCT_SPEC.md:310`은 아직 claim-coverage panel의 plain-language focus-slot explanation line을 current behavior로 직접 적지 않고 있습니다.
- `docs/project-brief.md:81`와 `docs/PRODUCT_PROPOSAL.md:61`에도 더 오래된 high-level wording이 남아 있지만, 이번 tie-break에서는 current shipped contract에 더 직접 연결된 `README.md` / `docs/PRODUCT_SPEC.md`를 먼저 좁히는 편이 맞다고 판단했습니다.
- unrelated dirty worktree(`.gitignore`, `.pipeline/README.md`, `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `PROJECT_CUSTOM_INSTRUCTIONS.md`, `pipeline_gui/*`, `watcher_core.py`, 관련 tests, `work/README.md`, `verify/README.md`, `report/gemini/README.md`, 기타 unrelated `work/` / `verify/` note)는 이번 검증 범위 밖이라 손대지 않았습니다.
