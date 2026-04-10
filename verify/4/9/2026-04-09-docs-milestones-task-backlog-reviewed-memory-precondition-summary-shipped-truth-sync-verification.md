# docs: MILESTONES TASK_BACKLOG reviewed-memory precondition summary shipped-vs-later truth sync verification

## 변경 파일
- `verify/4/9/2026-04-09-docs-milestones-task-backlog-reviewed-memory-precondition-summary-shipped-truth-sync-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work`의 docs-only truth-sync가 실제 planning docs와 root authority docs, 구현 스니펫 기준으로 맞는지 다시 확인해야 했습니다.
- 같은 reviewed-memory precondition planning family 안에서 다음 Claude 슬라이스를 one exact bundle로 다시 좁혀야 했습니다.

## 핵심 변경
- 최신 `/work`의 직접 수정 7곳은 truthful합니다.
  - `docs/MILESTONES.md:199`
  - `docs/MILESTONES.md:203`
  - `docs/TASK_BACKLOG.md:115`
  - `docs/TASK_BACKLOG.md:306`
  - `docs/TASK_BACKLOG.md:350`
  - `docs/TASK_BACKLOG.md:365`
  - `docs/TASK_BACKLOG.md:380`
  는 모두 현재 shipped apply path, shipped read-only contract surface, later state-machine widening 구분과 맞습니다.
- 최신 `/work`의 잔여 stale phrase 제거 주장도 맞습니다.
  - `rg -n 'before actual reviewed-memory apply result machinery exists|rollback, disable, and operator-audit rules remain later|future rollback target only|future stop-apply target only|disable = later stop-apply machinery|one later reviewed-memory boundary draft|not reviewed-memory apply or cross-session counting' docs/MILESTONES.md docs/TASK_BACKLOG.md` 결과 0건
- 다만 closeout의 `남은 리스크 없음`은 과합니다.
  - 같은 precondition summary family 안에 remaining future-style headings가 남아 있습니다.
  - `docs/TASK_BACKLOG.md:332`
  - `docs/TASK_BACKLOG.md:409`
  - `docs/TASK_BACKLOG.md:436`
  - `docs/TASK_BACKLOG.md:475`
  는 여전히 `Fix ...` framing을 유지하지만, 같은 family의 authority/planning docs는 이미 current shipped wording으로 정리돼 있습니다.
- 이 residual은 current shipped truth와 어긋납니다.
  - `docs/MILESTONES.md:201`
  - `docs/MILESTONES.md:236`
  - `docs/MILESTONES.md:249`
  - `docs/MILESTONES.md:271`
  - `docs/NEXT_STEPS.md:142`
  - `docs/NEXT_STEPS.md:145`
  - `docs/NEXT_STEPS.md:206`
  - `docs/PRODUCT_SPEC.md:1149`
  - `docs/PRODUCT_SPEC.md:1158`
  - `docs/ARCHITECTURE.md:876`
  - `docs/ARCHITECTURE.md:888`
  - `docs/ACCEPTANCE_CRITERIA.md:658`
  - `docs/ACCEPTANCE_CRITERIA.md:665`
- 다음 슬라이스는 또 하나의 한 줄 수정이 아니라, `TASK_BACKLOG` 같은 블록에 남은 `boundary_defined` / `conflict_visible` / `operator_auditable` / `unblock semantics` heading drift bundle로 고정했습니다.

## 검증
- `sed -n '1,220p' work/4/9/2026-04-09-docs-milestones-task-backlog-reviewed-memory-precondition-summary-shipped-truth-sync.md`
- `sed -n '1,220p' verify/4/9/2026-04-09-docs-milestones-task-backlog-rollback-disable-target-influence-truth-sync-verification.md`
- `sed -n '1,260p' .pipeline/claude_handoff.md`
- `ls -1t work/4/9/*.md | head -n 12`
- `ls -1t verify/4/9/*.md | head -n 12`
- `git status --short`
- `git diff --check`
- `nl -ba docs/MILESTONES.md | sed -n '190,206p'`
- `nl -ba docs/MILESTONES.md | sed -n '201,250p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '113,382p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '326,406p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '332,446p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '470,520p'`
- `nl -ba docs/NEXT_STEPS.md | sed -n '142,145p'`
- `nl -ba docs/NEXT_STEPS.md | sed -n '177,214p'`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '1149,1160p'`
- `nl -ba docs/ARCHITECTURE.md | sed -n '876,889p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '658,665p'`
- `rg -n 'before actual reviewed-memory apply result machinery exists|rollback, disable, and operator-audit rules remain later|future rollback target only|future stop-apply target only|disable = later stop-apply machinery|one later reviewed-memory boundary draft|not reviewed-memory apply or cross-session counting' docs/MILESTONES.md docs/TASK_BACKLOG.md`
- `rg -n 'conflict_visible_reviewed_memory_scope|operator_auditable_reviewed_memory_transition|reviewed_memory_conflict_contract|reviewed_memory_transition_audit_contract' docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md docs/NEXT_STEPS.md docs/MILESTONES.md docs/TASK_BACKLOG.md`
- Python unit test와 Playwright는 이번 검증 라운드에서 재실행하지 않았습니다. 최신 `/work`가 docs-only이고 code/test/runtime 변경을 주장하지 않았기 때문입니다.

## 남은 리스크
- `docs/TASK_BACKLOG.md`의 reviewed-memory precondition summary block에는 current shipped semantics를 아직 future task heading처럼 적는 residual이 남아 있습니다.
- 따라서 최신 `/work`의 직접 수정은 맞지만, `남은 리스크 없음`까지 완전히 truthful하다고 보기는 어렵습니다.
