## 변경 파일
- `verify/4/8/2026-04-08-docs-acceptance-criteria-playwright-count-claim-coverage-gate-inventory-truth-sync-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest `/work` `work/4/8/2026-04-08-docs-acceptance-criteria-playwright-count-claim-coverage-gate-inventory-truth-sync.md`가 실제 문서 상태와 맞는지 다시 확인하고, 같은 문서 family에서 남은 다음 한 개 슬라이스를 정해야 했습니다.
- same-day latest `/verify`와 기존 `.pipeline/claude_handoff.md`는 `docs/NEXT_STEPS.md` truth-sync 라운드 기준이었으므로, 이번 `docs/ACCEPTANCE_CRITERIA.md` 반영 결과에 맞춰 persistent verification과 next handoff를 갱신할 필요가 있었습니다.

## 핵심 변경
- latest `/work`는 truthful하다고 확인했습니다.
  - `docs/ACCEPTANCE_CRITERIA.md:1322`가 실제로 `Playwright smoke covers 79 core browser scenarios:`로 갱신되어 있습니다.
  - `docs/ACCEPTANCE_CRITERIA.md:1337`에는 claim-coverage panel gate inventory가 `focus-slot reinvestigation explanation (improved/regressed/unchanged with natural Korean particle normalization)`까지 포함하도록 반영되어 있습니다.
  - `awk 'BEGIN{flag=0;count=0} /### Current Gates/{flag=1;next} /### In Progress/{flag=0} flag && /^  - /{count++} END{print count}' docs/ACCEPTANCE_CRITERIA.md` 결과도 실제로 `79`였습니다.
- `/work`가 적은 verification claim도 그대로 맞았습니다.
  - `git diff -- docs/ACCEPTANCE_CRITERIA.md`는 clean이었고, `git diff --check`도 clean이었습니다.
- 다음 exact slice는 `Docs README MILESTONES TASK_BACKLOG claim-coverage smoke inventory truth sync`로 고정했습니다.
  - `README.md:127`은 아직 claim-coverage smoke를 `[교차 확인]`, `[단일 출처]`, `[미확인]` leading status tags와 actionable hints 수준으로만 적고 있습니다.
  - `docs/MILESTONES.md:37`과 `docs/TASK_BACKLOG.md:25`도 dedicated claim-coverage scenario를 같은 옛 wording으로만 설명합니다.
  - 반면 `docs/NEXT_STEPS.md:16`과 `docs/ACCEPTANCE_CRITERIA.md:1337`은 이미 focus-slot reinvestigation explanation detail까지 truth-synced 되어 있어, 같은 family 문서끼리 설명 층위가 어긋나 있습니다.
  - 따라서 남은 가장 선명한 same-family current-risk는 위 세 문서의 smoke inventory wording drift라고 판단했습니다.
- `.pipeline/claude_handoff.md`도 위 판단에 맞춰 새 next slice 기준으로 갱신했습니다.

## 검증
- `sed -n '1,240p' work/4/8/2026-04-08-docs-acceptance-criteria-playwright-count-claim-coverage-gate-inventory-truth-sync.md`
- `sed -n '1,240p' verify/4/8/2026-04-08-docs-next-steps-playwright-smoke-count-claim-coverage-inventory-truth-sync-verification.md`
- `sed -n '1,240p' .pipeline/claude_handoff.md`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '1318,1344p'`
- `awk 'BEGIN{flag=0;count=0} /### Current Gates/{flag=1;next} /### In Progress/{flag=0} flag && /^  - /{count++} END{print count}' docs/ACCEPTANCE_CRITERIA.md`
- `rg -n "focus-slot reinvestigation explanation|79 core browser scenarios|claim-coverage panel rendering contract|17 core browser scenarios" docs/ACCEPTANCE_CRITERIA.md README.md docs/NEXT_STEPS.md docs/MILESTONES.md docs/TASK_BACKLOG.md -S`
- `nl -ba README.md | sed -n '120,131p'`
- `nl -ba docs/MILESTONES.md | sed -n '33,40p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '21,28p'`
- `git diff -- docs/ACCEPTANCE_CRITERIA.md`
- `git diff --check`

## 남은 리스크
- `README.md`, `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md`의 claim-coverage smoke inventory wording은 아직 focus-slot reinvestigation explanation detail을 반영하지 못하고 있습니다.
- `docs/PRODUCT_SPEC.md:310`은 더 상위 구현 서술로 `slot reinvestigation scaffolding` 수준에 머물러 있지만, 이번 tie-break에서는 smoke inventory를 직접 나열하는 세 문서의 drift가 더 직접적인 후속 작업이라고 판단했습니다.
- unrelated dirty worktree(`.gitignore`, `.pipeline/README.md`, `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `PROJECT_CUSTOM_INSTRUCTIONS.md`, `pipeline_gui/*`, `watcher_core.py`, 관련 tests, `work/README.md`, `verify/README.md`, `report/gemini/README.md`, 기타 unrelated `work/` / `verify/` note)는 이번 검증 범위 밖이라 손대지 않았습니다.
