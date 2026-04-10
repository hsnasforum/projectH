## 변경 파일
- `verify/4/8/2026-04-08-docs-next-steps-playwright-smoke-count-claim-coverage-inventory-truth-sync-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest `/work` `work/4/8/2026-04-08-docs-next-steps-playwright-smoke-count-claim-coverage-inventory-truth-sync.md`가 실제 tree와 맞는지 다시 확인하고, 같은 family에서 남은 가장 정확한 다음 슬라이스를 한 개로 고정해야 했습니다.
- same-day latest `/verify`와 기존 `.pipeline/claude_handoff.md`는 직전 `focus-slot transition copy particle normalization` 라운드 기준이어서, 이번 docs truth-sync 라운드를 반영한 persistent verification과 다음 handoff가 필요했습니다.

## 핵심 변경
- latest `/work`는 truthful하다고 확인했습니다.
  - `docs/NEXT_STEPS.md:16`이 이제 `Playwright smoke currently covers 82 browser scenarios`로 갱신되어 있습니다.
  - 같은 줄의 inventory 문구도 claim-coverage focus-slot reinvestigation explanation을 `improved`, `regressed`, `unchanged`, particle normalization까지 포함하는 현재 상태와 맞게 정리되어 있습니다.
  - `rg -c '^test\(' e2e/tests/web-smoke.spec.mjs` 결과도 실제로 `82`였습니다.
- `/work`가 적은 verification claim도 그대로 맞았습니다.
  - `git diff -- docs/NEXT_STEPS.md`는 clean이었고, `git diff --check`도 clean이었습니다.
- 다음 exact slice는 `Docs ACCEPTANCE_CRITERIA Playwright core-scenario count and claim-coverage gate inventory truth sync`로 고정했습니다.
  - `docs/ACCEPTANCE_CRITERIA.md:1322`는 아직 `Playwright smoke covers 17 core browser scenarios:`라고 적고 있습니다.
  - 하지만 현재 `### Current Gates` 아래 실제 bullet 수는 `79`개였습니다.
  - 같은 구간의 claim-coverage bullet은 leading status tags와 actionable hints까지만 적고 있어, 최신 `focus-slot reinvestigation explanation` detail까지는 current-gate inventory에 아직 반영되지 않았습니다.
  - 따라서 남은 가장 선명한 same-family current-risk는 `docs/ACCEPTANCE_CRITERIA.md`의 misleading docs drift라고 판단했습니다.
- `.pipeline/claude_handoff.md`도 위 판단에 맞춰 stale 상태에서 새 next slice 기준으로 갱신했습니다.

## 검증
- `sed -n '1,220p' work/4/8/2026-04-08-docs-next-steps-playwright-smoke-count-claim-coverage-inventory-truth-sync.md`
- `sed -n '1,220p' verify/4/8/2026-04-08-web-investigation-focus-slot-transition-copy-particle-normalization-verification.md`
- `sed -n '1,220p' .pipeline/claude_handoff.md`
- `nl -ba docs/NEXT_STEPS.md | sed -n '15,16p'`
- `rg -c '^test\(' e2e/tests/web-smoke.spec.mjs`
- `git diff -- docs/NEXT_STEPS.md`
- `git diff --check`
- `rg -n "claim-coverage.*focus-slot|improved/regressed/unchanged|Playwright smoke currently covers|82 browser scenarios|80\. claim-coverage|81\. claim-coverage|82\. claim-coverage" docs/NEXT_STEPS.md README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md -S`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '1318,1326p'`
- `nl -ba docs/MILESTONES.md | sed -n '107,115p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '100,106p'`
- `rg -n "claim-coverage panel rendering contract|focus-slot reinvestigation explanation|leading status tags|actionable hints|17 core browser scenarios" docs/ACCEPTANCE_CRITERIA.md -S`
- `sed -n '1322,1365p' docs/ACCEPTANCE_CRITERIA.md`
- `rg -n "Current Gates|Playwright smoke covers 17 core browser scenarios" docs/ACCEPTANCE_CRITERIA.md README.md docs/NEXT_STEPS.md -S`
- `awk 'BEGIN{flag=0;count=0} /### Current Gates/{flag=1;next} /### In Progress/{flag=0} flag && /^  - /{count++} END{print count}' docs/ACCEPTANCE_CRITERIA.md`

## 남은 리스크
- `docs/ACCEPTANCE_CRITERIA.md`의 `17 core browser scenarios` wording과 실제 `Current Gates` inventory 사이 truth drift가 남아 있습니다.
- 현재 `Current Gates`가 정말로 전체 gate inventory를 뜻하는지, 아니면 의도적으로 축약된 `core scenarios`를 뜻하는지 wording 해석 여지가 있으므로, 다음 라운드에서는 숫자만 바꾸지 말고 구간 설명 자체를 truthfully 정리해야 합니다.
- unrelated dirty worktree(`.gitignore`, `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `PROJECT_CUSTOM_INSTRUCTIONS.md`, `pipeline_gui/*`, `watcher_core.py`, 관련 tests, `work/README.md`, `verify/README.md`, `report/gemini/README.md`, 기타 unrelated `work/` / `verify/` note)는 이번 검증 범위 밖이라 손대지 않았습니다.
