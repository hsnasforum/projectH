# docs: TASK_BACKLOG remaining reviewed-memory precondition heading shipped-truth bundle verification

## 변경 파일
- `verify/4/9/2026-04-09-docs-task-backlog-precondition-heading-shipped-truth-sync-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work`의 docs-only truth-sync가 실제 `docs/TASK_BACKLOG.md` 상태와 adjacent planning/root docs truth에 맞는지 다시 확인해야 했습니다.
- 같은 reviewed-memory precondition planning family 안에서 다음 Claude 슬라이스를 다시 one exact bundle로 좁혀야 했습니다.

## 핵심 변경
- 최신 `/work`의 직접 수정 4곳은 truthful합니다.
  - `docs/TASK_BACKLOG.md:332`
  - `docs/TASK_BACKLOG.md:409`
  - `docs/TASK_BACKLOG.md:436`
  - `docs/TASK_BACKLOG.md:475`
  는 모두 `Fix ...` future-style heading 대신 shipped/current framing으로 정리되어 있습니다.
- 최신 `/work`의 stale heading 제거 주장도 맞습니다.
  - `rg -n 'Fix `reviewed_memory_boundary_defined`|Fix `conflict_visible_reviewed_memory_scope`|Fix `operator_auditable_reviewed_memory_transition`|Fix first same-session unblock semantics as binary and all-required' docs/TASK_BACKLOG.md` 결과 0건
- 다만 closeout의 `남은 리스크 없음`은 과합니다.
  - 같은 precondition block 안에 current shipped apply/unblock truth를 아직 과도하게 축소하는 residual이 남아 있습니다.
  - `docs/TASK_BACKLOG.md:329`
  - `docs/TASK_BACKLOG.md:476`
- 이 residual은 adjacent planning/root docs와 어긋납니다.
  - `docs/MILESTONES.md:199`
  - `docs/MILESTONES.md:200`
  - `docs/MILESTONES.md:275`
  - `docs/MILESTONES.md:276`
  - `docs/NEXT_STEPS.md:122`
  - `docs/NEXT_STEPS.md:145`
  - `docs/NEXT_STEPS.md:206`
  - `docs/PRODUCT_SPEC.md:1080`
  - `docs/PRODUCT_SPEC.md:1501`
  - `docs/ARCHITECTURE.md:816`
  - `docs/ARCHITECTURE.md:1140`
  - `docs/ACCEPTANCE_CRITERIA.md:845`
  - `docs/ACCEPTANCE_CRITERIA.md:978`
- 다음 슬라이스는 `TASK_BACKLOG` 같은 block 안의 `precondition_status` / `unblock semantics` residual wording bundle로 고정했습니다.

## 검증
- `sed -n '1,220p' work/4/9/2026-04-09-docs-task-backlog-precondition-heading-shipped-truth-sync.md`
- `sed -n '1,220p' verify/4/9/2026-04-09-docs-milestones-task-backlog-reviewed-memory-precondition-summary-shipped-truth-sync-verification.md`
- `sed -n '1,260p' .pipeline/claude_handoff.md`
- `ls -1t work/4/9/*.md | head -n 12`
- `ls -1t verify/4/9/*.md | head -n 12`
- `git status --short`
- `git diff --check`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '326,520p'`
- `nl -ba docs/MILESTONES.md | sed -n '190,210p'`
- `nl -ba docs/NEXT_STEPS.md | sed -n '118,156p'`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '1080,1092p'`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '1498,1506p'`
- `nl -ba docs/ARCHITECTURE.md | sed -n '816,823p'`
- `nl -ba docs/ARCHITECTURE.md | sed -n '1138,1143p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '838,846p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '976,982p'`
- `rg -n 'Fix `reviewed_memory_boundary_defined`|Fix `conflict_visible_reviewed_memory_scope`|Fix `operator_auditable_reviewed_memory_transition`|Fix first same-session unblock semantics as binary and all-required' docs/TASK_BACKLOG.md`
- `rg -n 'no reviewed-memory apply|through later machinery|blocked_all_required|unblocked_all_required' docs/TASK_BACKLOG.md docs/MILESTONES.md docs/NEXT_STEPS.md docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md`
- Python unit test와 Playwright는 이번 검증 라운드에서 재실행하지 않았습니다. 최신 `/work`가 docs-only이고 code/test/runtime 변경을 주장하지 않았기 때문입니다.

## 남은 리스크
- `docs/TASK_BACKLOG.md:329`와 `docs/TASK_BACKLOG.md:476`은 current shipped apply/unblock truth를 아직 완전히 따라가지 못합니다.
- 따라서 최신 `/work`의 direct heading sync는 truthful하지만, `남은 리스크 없음`까지 완전히 truthful하다고 보기는 어렵습니다.
