# docs: PRODUCT_SPEC ACCEPTANCE_CRITERIA reviewed-memory entry-slice historical truth sync verification

## 변경 파일
- `verify/4/9/2026-04-09-docs-product-spec-acceptance-reviewed-memory-entry-slice-historical-truth-sync-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work`가 `docs/PRODUCT_SPEC.md`와 `docs/ACCEPTANCE_CRITERIA.md`의 reviewed-memory entry-slice historical wording을 현재 shipped truth와 맞췄다고 주장하므로, direct target truth부터 다시 확인해야 했습니다.
- same-day docs-only truth-sync가 길게 이어진 상태라, direct target이 truthful하더라도 같은 reviewed-memory docs family residual이 남으면 그 잔여를 한 번에 닫는 bounded slice로 넘겨야 했습니다.

## 핵심 변경
- 최신 `/work`의 직접 수정 대상은 truthful합니다.
  - `docs/PRODUCT_SPEC.md:415`
  - `docs/PRODUCT_SPEC.md:970`
  - `docs/ACCEPTANCE_CRITERIA.md:186`
- 위 문구는 현재 shipped reviewed-memory truth와 맞습니다.
  - `docs/PRODUCT_SPEC.md:58`
  - `docs/PRODUCT_SPEC.md:60`
  - `docs/ARCHITECTURE.md:15`
  - `docs/ARCHITECTURE.md:1170`
  - `app/handlers/aggregate.py:399`
  - `app/handlers/aggregate.py:470`
  - `app/handlers/aggregate.py:639`
- 다만 최신 `/work`의 `남은 리스크 없음`은 repo-level reviewed-memory docs family 기준으로는 약간 과합니다.
  - 같은 family residual이 아직 남아 있습니다.
    - `docs/ARCHITECTURE.md:703`
  - 이 줄은 `read-only review queue`가 아직 `apply / rollback` layer를 열지 않았다고 적지만, 현재 shipped truth는 `docs/ARCHITECTURE.md:1170`, `docs/NEXT_STEPS.md:542`, 그리고 `app/handlers/aggregate.py` stop-apply / reversal / conflict-visibility 구현과 이미 맞물려 있습니다.
- 따라서 latest `/work` 자체는 truthful하지만, repo-level family closure 주장까지는 그대로 받기 어렵습니다.
- 다음 슬라이스는 `docs/ARCHITECTURE.md` 한 파일의 recurrence-key / practical-next-path wording을 현재 shipped apply / rollback truth에 맞추는 bounded slice가 적절합니다.

## 검증
- `sed -n '1,220p' work/4/9/2026-04-09-docs-product-spec-acceptance-reviewed-memory-entry-slice-historical-truth-sync.md`
- `sed -n '1,240p' verify/4/9/2026-04-09-docs-agents-architecture-mission-purpose-reviewed-memory-truth-sync-verification.md`
- `git diff --check`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '411,417p'`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '967,972p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '184,187p'`
- `rg -n --no-heading 'no review queue|reviewed memory and user-level memory still remain closed|first implementation slice is \`artifact_id\` linkage, not review queue|review queue.*later slices above this entry slice|reviewed-memory first slice is now shipped; user-level memory still remains later|review queue, aggregate apply trigger, and active-effect path are now shipped in later slices' docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md`
- `rg -n --no-heading 'review queue|검토 후보|aggregate apply trigger|active-effect path|reviewed-memory first slice' docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md docs/ARCHITECTURE.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/project-brief.md docs/PRODUCT_PROPOSAL.md app/templates/index.html tests/test_web_app.py`
- `rg -n --no-heading 'without opening any apply / rollback|read-only review queue remains separate from review actions|no review queue semantics beyond|reviewed memory and user-level memory|review queue or user-level memory|apply / rollback|apply/rollback|review actions and user-level memory' docs/ARCHITECTURE.md docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md docs/NEXT_STEPS.md docs/TASK_BACKLOG.md docs/MILESTONES.md`
- `nl -ba docs/ARCHITECTURE.md | sed -n '698,706p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '812,820p'`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '506,512p'`
- `nl -ba app/handlers/aggregate.py | sed -n '398,408p'`
- `nl -ba app/handlers/aggregate.py | sed -n '468,476p'`
- `nl -ba app/handlers/aggregate.py | sed -n '636,644p'`
- `nl -ba docs/ARCHITECTURE.md | sed -n '1166,1172p'`
- `nl -ba docs/NEXT_STEPS.md | sed -n '540,543p'`
- Python unit test와 Playwright는 재실행하지 않았습니다. 최신 `/work`가 docs-only이고 code/test/runtime 변경을 주장하지 않았기 때문입니다.

## 남은 리스크
- 최신 `/work`의 직접 수정 대상은 truthful합니다.
- 다만 repo-level reviewed-memory docs truth-sync는 `docs/ARCHITECTURE.md:703` practical-next-path wording까지는 아직 완전히 닫히지 않았습니다.
