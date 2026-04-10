# docs: ARCHITECTURE reviewed-memory recurrence-key practical-next-path truth sync verification

## 변경 파일
- `verify/4/9/2026-04-09-docs-architecture-recurrence-key-practical-next-path-truth-sync-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work`가 `docs/ARCHITECTURE.md:703`의 recurrence-key practical-next-path wording을 현재 shipped reviewed-memory truth와 맞게 고쳤는지 다시 확인해야 했습니다.
- direct target이 truthful하면, 같은 날 docs-only truth-sync를 또 한 줄짜리 micro-slice로 늘리기보다 같은 family의 남은 summary residual을 한 번에 닫는 bounded bundle로 넘기는 편이 더 적절했습니다.

## 핵심 변경
- 최신 `/work`의 직접 수정 대상은 truthful합니다.
  - `docs/ARCHITECTURE.md:703`
- 현재 문구는 shipped reviewed-memory lifecycle truth와 맞습니다.
  - `app/handlers/aggregate.py:399`
  - `app/handlers/aggregate.py:470`
  - `app/handlers/aggregate.py:639`
  - `docs/ARCHITECTURE.md:15`
  - `docs/NEXT_STEPS.md:542`
- 따라서 직전 `/verify`가 남겨 둔 `docs/ARCHITECTURE.md:703` residual은 이번 라운드로 닫혔습니다.
- 다만 최신 `/work`의 `남은 리스크 없음`은 repo-level reviewed-memory docs family 기준으로는 과합니다.
  - 아직 여러 current-summary / current-contract 구간이 shipped first slice를 `active-effect path` shorthand로만 축약하고 있습니다.
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
    - `docs/project-brief.md:15`
    - `docs/MILESTONES.md:6`
    - `docs/ARCHITECTURE.md:5`
    - `docs/ARCHITECTURE.md:10`
    - `docs/TASK_BACKLOG.md:5`
    - `docs/NEXT_STEPS.md:19`
    - `docs/ACCEPTANCE_CRITERIA.md:186`
  - 반면 repo 안의 다른 root docs는 이미 full shipped summary를 더 명시적으로 적고 있습니다.
    - `docs/ARCHITECTURE.md:15`
    - `docs/MILESTONES.md:11`
    - `docs/PRODUCT_PROPOSAL.md:95`
    - `docs/project-brief.md:20`
    - `docs/TASK_BACKLOG.md:8`
    - `docs/ACCEPTANCE_CRITERIA.md:25`
- 다음 슬라이스는 남아 있는 `active-effect path` shorthand residual을 한 번에 정리하는 reviewed-memory lifecycle summary bundle이 적절합니다.

## 검증
- `git diff --check`
- `git diff -- docs/ARCHITECTURE.md`
- `sed -n '1,220p' work/4/9/2026-04-09-docs-architecture-recurrence-key-practical-next-path-truth-sync.md`
- `sed -n '1,240p' verify/4/9/2026-04-09-docs-product-spec-acceptance-reviewed-memory-entry-slice-historical-truth-sync-verification.md`
- `nl -ba docs/ARCHITECTURE.md | sed -n '694,706p'`
- `nl -ba app/handlers/aggregate.py | sed -n '398,408p'`
- `nl -ba app/handlers/aggregate.py | sed -n '468,476p'`
- `nl -ba app/handlers/aggregate.py | sed -n '636,644p'`
- `nl -ba docs/ARCHITECTURE.md | sed -n '1166,1172p'`
- `nl -ba docs/NEXT_STEPS.md | sed -n '540,543p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '180,188p'`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '964,972p'`
- `rg -n --no-heading 'without opening any apply / rollback|read-only review queue|reviewed-memory active-effect path|active-effect path' README.md AGENTS.md CLAUDE.md PROJECT_CUSTOM_INSTRUCTIONS.md docs`
- Python unit test와 Playwright는 재실행하지 않았습니다. 최신 `/work`가 docs-only이고 code/test/runtime 변경을 주장하지 않았기 때문입니다.

## 남은 리스크
- 최신 `/work`의 direct target은 truthful합니다.
- recurrence-key practical-next-path residual은 닫혔지만, repo-level reviewed-memory docs family에는 `active-effect path` shorthand summary residual이 아직 남아 있습니다.
- 다음 라운드에서 remaining shorthand를 한 번에 `emitted/apply/result/active-effect path, stop-apply, reversal, and conflict-visibility` 수준으로 맞추면, 같은 family를 더 정직하게 닫을 수 있습니다.
