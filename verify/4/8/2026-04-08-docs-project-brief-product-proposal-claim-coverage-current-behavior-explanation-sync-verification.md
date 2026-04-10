## 변경 파일
- `verify/4/8/2026-04-08-docs-project-brief-product-proposal-claim-coverage-current-behavior-explanation-sync-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest `/work` `work/4/8/2026-04-08-docs-project-brief-product-proposal-claim-coverage-current-behavior-explanation-sync.md`가 실제 문서 상태와 맞는지 다시 확인하고, same-family 문서 drift가 정말로 모두 닫혔는지 검증해야 했습니다.
- same-day latest `/verify`와 기존 `.pipeline/claude_handoff.md`는 `README.md` / `docs/PRODUCT_SPEC.md` current-behavior sync 라운드 기준이었으므로, 이번 `docs/project-brief.md` / `docs/PRODUCT_PROPOSAL.md` 반영 결과에 맞춰 persistent verification과 next handoff를 갱신할 필요가 있었습니다.

## 핵심 변경
- latest `/work`는 구현과 rerun 자체는 맞았지만, 완전히 truthful하지는 않았습니다.
  - `docs/project-brief.md:81`와 `docs/PRODUCT_PROPOSAL.md:61`은 실제로 `claim coverage panel with status tags, actionable hints, and dedicated plain-language focus-slot reinvestigation explanation (improved/regressed/unchanged)`로 갱신되어 있습니다.
  - `/work`가 적은 검증 claim도 그대로 맞았습니다.
    - `rg -n "status tags and actionable hints" docs/project-brief.md docs/PRODUCT_PROPOSAL.md`는 0건이었고,
    - `rg -n "focus-slot reinvestigation explanation" docs/project-brief.md docs/PRODUCT_PROPOSAL.md README.md docs/PRODUCT_SPEC.md` 기준으로 관련 synced docs에 새 wording이 들어가 있으며,
    - `git diff --check`도 clean이었습니다.
- 다만 `/work`의 `남은 리스크`에 적힌 “claim-coverage 관련 문서 동기화는 이번 슬라이스로 전체 문서 계층에서 완료됨”은 사실과 다릅니다.
  - `docs/NEXT_STEPS.md:15`는 아직 `claim-coverage panel with status tags and actionable hints` 수준으로만 적고 있습니다.
  - `docs/TASK_BACKLOG.md:24`도 아직 `Claim coverage panel with status tags and actionable hints, and slot reinvestigation scaffolding`라고 적고 있습니다.
  - 같은 파일들의 바로 인접한 smoke/backlog 항목(`docs/NEXT_STEPS.md:16`, `docs/TASK_BACKLOG.md:25`)은 이미 `focus-slot reinvestigation explanation` detail을 적고 있어, high-level summary bullet만 뒤처진 상태입니다.
- 다음 exact slice는 `Docs NEXT_STEPS TASK_BACKLOG claim-coverage current-behavior summary sync`로 고정했습니다.
  - 이는 같은 family의 남은 misleading-docs current-risk reduction입니다.
  - `docs/NEXT_STEPS.md`와 `docs/TASK_BACKLOG.md` 안에서조차 high-level summary와 smoke/detail inventory가 서로 어긋나 있기 때문에, 새 quality axis를 여는 것보다 먼저 닫는 편이 맞다고 판단했습니다.
- `.pipeline/claude_handoff.md`도 위 판단에 맞춰 새 next slice 기준으로 갱신했습니다.

## 검증
- `sed -n '1,240p' work/4/8/2026-04-08-docs-project-brief-product-proposal-claim-coverage-current-behavior-explanation-sync.md`
- `sed -n '1,240p' verify/4/8/2026-04-08-docs-readme-product-spec-claim-coverage-current-behavior-explanation-sync-verification.md`
- `sed -n '1,260p' .pipeline/claude_handoff.md`
- `nl -ba docs/project-brief.md | sed -n '78,82p'`
- `nl -ba docs/PRODUCT_PROPOSAL.md | sed -n '58,62p'`
- `rg -n "status tags and actionable hints|focus-slot reinvestigation explanation|claim coverage panel" docs/project-brief.md docs/PRODUCT_PROPOSAL.md README.md docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md docs/NEXT_STEPS.md docs/MILESTONES.md docs/TASK_BACKLOG.md -S`
- `git diff -- docs/project-brief.md docs/PRODUCT_PROPOSAL.md`
- `git diff --check`
- `git status --short`
- `nl -ba docs/NEXT_STEPS.md | sed -n '14,16p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '22,25p'`
- `rg -n "slot reinvestigation scaffolding|claim coverage panel with status tags and actionable hints|claim-coverage panel with status tags and actionable hints|focus-slot reinvestigation explanation" docs README.md -S`

## 남은 리스크
- `docs/NEXT_STEPS.md:15`와 `docs/TASK_BACKLOG.md:24`의 claim-coverage high-level summary bullet은 아직 current shipped wording을 다 반영하지 못하고 있습니다.
- 같은 family 문서 정리는 거의 닫혔지만, `/work` closeout의 “전체 문서 계층 완료” 같은 표현은 실제 residual drift 검색 후에만 쓰는 편이 안전합니다.
- unrelated dirty worktree(`.gitignore`, `.pipeline/README.md`, `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `PROJECT_CUSTOM_INSTRUCTIONS.md`, `pipeline_gui/*`, `watcher_core.py`, 관련 tests, `work/README.md`, `verify/README.md`, `report/gemini/README.md`, 기타 unrelated `work/` / `verify/` note)는 이번 검증 범위 밖이라 손대지 않았습니다.
