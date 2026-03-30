## 변경 파일
- docs/PRODUCT_SPEC.md
- docs/ARCHITECTURE.md
- docs/ACCEPTANCE_CRITERIA.md
- docs/MILESTONES.md
- docs/TASK_BACKLOG.md
- docs/NEXT_STEPS.md
- plandoc/2026-03-28-reviewed-memory-rollback-contract.md

## 사용 skill
- mvp-scope
- approval-flow-audit
- doc-sync
- release-check
- work-log-closeout

## 변경 이유
- 직전 closeout에서 `reviewed_memory_boundary_draft`는 shipped 되었지만 `rollback_ready_reviewed_memory_effect`가 정확히 무엇을 뜻하는지, 무엇을 rollback target으로 삼아야 하는지가 아직 문서로 닫히지 않았습니다.
- 이 경계가 없으면 later reviewed-memory apply나 repeated-signal promotion이 “무엇을 되돌릴 수 있어야 하는가”를 과장해서 해석할 위험이 남습니다.

## 핵심 변경
- `rollback_ready_reviewed_memory_effect`를 one later applied reviewed-memory effect reversal로 고정했습니다.
- rollback target은 `same_session_exact_recurrence_aggregate_only` scope 안의 future applied effect only로 정리했고, current `reviewed_memory_boundary_draft`는 scope draft/basis ref로 남기되 rollback target으로 쓰지 않도록 고정했습니다.
- rollback 이후에도 aggregate identity, supporting refs, boundary draft, operator-visible audit trace는 남고 later applied effect only가 비활성화될 수 있다고 문서화했습니다.
- rollback을 disable, conflict visibility, operator audit와 separate later machinery로 분리했고, `task_log`는 audit mirror일 뿐 canonical rollback store가 아니라고 다시 못 박았습니다.
- next implementation slice는 one read-only `reviewed_memory_rollback_contract` only로 추천했습니다.

## 검증
- 실행: `git diff --check`
- 실행: `rg -n "rollback_ready_reviewed_memory_effect|reviewed_memory_boundary_draft|reviewed_memory_precondition_status|aggregate_promotion_marker|same_session_exact_recurrence_aggregate_only|cross-session" docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md README.md plandoc/2026-03-28-reviewed-memory-rollback-contract.md`
- 미실행: `python3 -m py_compile ...`
- 미실행: `python3 -m unittest ...`
- 미실행: `make e2e-test`

## 남은 리스크
- 이전 closeout에서 이어받은 리스크:
  - boundary draft는 생겼지만 later reviewed-memory effect를 무엇을 대상으로 어떻게 rollback해야 하는지 exact contract가 없었습니다.
- 이번 라운드에서 해소한 리스크:
  - rollback target이 current evidence traces나 boundary draft deletion이 아니라 one later applied reviewed-memory effect only라는 점을 문서로 고정했습니다.
  - rollback 이후에도 무엇이 남아야 하는지와 `task_log`가 canonical rollback store가 아니라는 점을 분리했습니다.
- 여전히 남은 리스크:
  - disable-ready, conflict-visible, operator-auditable precondition은 아직 separate exact contract가 더 필요합니다.
  - `reviewed_memory_rollback_contract`를 실제 payload에 어떤 최소 shape로 materialize할지 구현은 아직 남아 있습니다.
