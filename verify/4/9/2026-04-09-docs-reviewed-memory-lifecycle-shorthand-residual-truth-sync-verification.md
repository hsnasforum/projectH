# docs: reviewed-memory lifecycle shorthand residual truth sync verification

## 변경 파일
- `verify/4/9/2026-04-09-docs-reviewed-memory-lifecycle-shorthand-residual-truth-sync-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work`가 reviewed-memory lifecycle shorthand residual bundle을 실제로 닫았는지 다시 확인해야 했습니다.
- direct target이 truthful하더라도, 같은 family의 residual이 더 남아 있으면 `남은 리스크 없음`과 family-closure 표현은 그대로 수용하면 안 됐습니다.

## 핵심 변경
- 최신 `/work`의 직접 수정 대상은 truthful합니다.
  - `README.md:3`
  - `README.md:12`
  - `AGENTS.md:5`
  - `CLAUDE.md:5`
  - `PROJECT_CUSTOM_INSTRUCTIONS.md:1`
  - `docs/PRODUCT_SPEC.md:6`
  - `docs/PRODUCT_SPEC.md:18`
  - `docs/PRODUCT_SPEC.md:27`
  - `docs/PRODUCT_SPEC.md:970`
  - `docs/PRODUCT_PROPOSAL.md:6`
  - `docs/PRODUCT_PROPOSAL.md:16`
  - `docs/PRODUCT_PROPOSAL.md:25`
  - `docs/project-brief.md:5`
  - `docs/project-brief.md:14`
  - `docs/MILESTONES.md:6`
  - `docs/NEXT_STEPS.md:19`
  - `docs/ARCHITECTURE.md:5`
  - `docs/ARCHITECTURE.md:10`
  - `docs/TASK_BACKLOG.md:5`
  - `docs/ACCEPTANCE_CRITERIA.md:186`
- 위 구간은 현재 shipped reviewed-memory lifecycle truth와 맞습니다.
  - `app/handlers/aggregate.py:399`
  - `app/handlers/aggregate.py:470`
  - `app/handlers/aggregate.py:532`
  - `app/handlers/aggregate.py:639`
  - `docs/ARCHITECTURE.md:15`
  - `docs/MILESTONES.md:11`
  - `docs/PRODUCT_PROPOSAL.md:95`
  - `docs/project-brief.md:20`
  - `docs/TASK_BACKLOG.md:8`
- 다만 최신 `/work`의 `남은 리스크 없음`과 `전체 repo docs의 reviewed-memory lifecycle shorthand 동기화 완료`는 과합니다.
  - same-family residual이 아직 남아 있습니다.
    - `AGENTS.md:48`
    - `CLAUDE.md:27`
    - `PROJECT_CUSTOM_INSTRUCTIONS.md:25`
    - `docs/project-brief.md:15`
    - `docs/ACCEPTANCE_CRITERIA.md:25`
  - 이 줄들은 여전히 `reviewed-memory active-effect path (apply / stop-apply / reversal / conflict-visibility)` 형태라서, 이번 bundle이 닫으려던 shorthand family를 repo-level로 완전히 닫았다고 보기는 어렵습니다.
- 따라서 latest `/work`는 direct target 기준으로는 truthful하지만, same-family closure claim까지는 아직 수용하기 어렵습니다.

## 검증
- `git diff --check`
- `git diff -- README.md AGENTS.md CLAUDE.md PROJECT_CUSTOM_INSTRUCTIONS.md docs/PRODUCT_SPEC.md docs/PRODUCT_PROPOSAL.md docs/project-brief.md docs/MILESTONES.md docs/NEXT_STEPS.md docs/ARCHITECTURE.md docs/TASK_BACKLOG.md docs/ACCEPTANCE_CRITERIA.md`
- `sed -n '1,260p' work/4/9/2026-04-09-docs-reviewed-memory-lifecycle-shorthand-residual-truth-sync.md`
- `sed -n '1,260p' verify/4/9/2026-04-09-docs-architecture-recurrence-key-practical-next-path-truth-sync-verification.md`
- `rg -n --no-heading 'active-effect path|reviewed-memory active-effect path' README.md AGENTS.md CLAUDE.md PROJECT_CUSTOM_INSTRUCTIONS.md docs`
- `rg -n --no-heading 'reviewed-memory active-effect path \\(apply / stop-apply / reversal / conflict-visibility\\)' AGENTS.md CLAUDE.md PROJECT_CUSTOM_INSTRUCTIONS.md docs/project-brief.md docs/ACCEPTANCE_CRITERIA.md docs`
- `nl -ba README.md | sed -n '1,13p'`
- `nl -ba AGENTS.md | sed -n '1,6p'`
- `nl -ba CLAUDE.md | sed -n '1,6p'`
- `nl -ba PROJECT_CUSTOM_INSTRUCTIONS.md | sed -n '1,3p'`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '1,28p'`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '968,971p'`
- `nl -ba docs/PRODUCT_PROPOSAL.md | sed -n '1,26p'`
- `nl -ba docs/project-brief.md | sed -n '1,15p'`
- `nl -ba docs/MILESTONES.md | sed -n '1,7p'`
- `nl -ba docs/NEXT_STEPS.md | sed -n '17,20p'`
- `nl -ba docs/ARCHITECTURE.md | sed -n '1,11p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '1,6p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '184,187p'`
- `nl -ba docs/project-brief.md | sed -n '13,16p'`
- `nl -ba AGENTS.md | sed -n '44,50p'`
- `nl -ba CLAUDE.md | sed -n '23,29p'`
- `nl -ba PROJECT_CUSTOM_INSTRUCTIONS.md | sed -n '21,26p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '23,27p'`
- `nl -ba app/handlers/aggregate.py | sed -n '388,406p'`
- `nl -ba app/handlers/aggregate.py | sed -n '466,474p'`
- `nl -ba app/handlers/aggregate.py | sed -n '528,536p'`
- `nl -ba app/handlers/aggregate.py | sed -n '636,644p'`
- Python unit test와 Playwright는 재실행하지 않았습니다. 최신 `/work`가 docs-only이고 code/test/runtime 변경을 주장하지 않았기 때문입니다.

## 남은 리스크
- 최신 `/work`의 direct target은 truthful합니다.
- 그러나 same-family feature-list/current-surface residual 5줄이 아직 남아 있어서 reviewed-memory lifecycle shorthand family가 repo-level로 완전히 닫히지는 않았습니다.
- 다음 라운드에서 `AGENTS.md`, `CLAUDE.md`, `PROJECT_CUSTOM_INSTRUCTIONS.md`, `docs/project-brief.md`, `docs/ACCEPTANCE_CRITERIA.md`의 remaining `reviewed-memory active-effect path` wording을 한 번에 맞추면, 이번 family를 더 정직하게 닫을 수 있습니다.
