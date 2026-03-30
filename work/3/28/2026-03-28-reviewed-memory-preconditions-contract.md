## 변경 파일
- `docs/PRODUCT_SPEC.md`
- `docs/ARCHITECTURE.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`
- `docs/NEXT_STEPS.md`
- `plandoc/2026-03-28-reviewed-memory-preconditions-contract.md`
- `work/3/28/2026-03-28-reviewed-memory-preconditions-contract.md`

## 사용 skill
- `mvp-scope`
- `approval-flow-audit`
- `doc-sync`
- `release-check`
- `work-log-closeout`

## 변경 이유
- 직전 closeout에서 same-session aggregate 위의 blocked marker는 shipped 되었지만, 그 marker가 어떤 exact preconditions가 충족돼야만 later reviewed-memory boundary로 넘어갈 수 있는지 문서 계약이 없었습니다.
- 이 경계가 없으면 repeated-signal promotion, reviewed-memory apply, broader durable promotion, cross-session counting을 과장해서 여는 위험이 남아 있었습니다.

## 핵심 변경
- current same-session aggregate unblock preconditions를 exact five-precondition family로 고정했습니다:
  - `reviewed_memory_boundary_defined`
  - `rollback_ready_reviewed_memory_effect`
  - `disable_ready_reviewed_memory_effect`
  - `conflict_visible_reviewed_memory_scope`
  - `operator_auditable_reviewed_memory_transition`
- 각 precondition이 무엇을 의미하고 무엇을 의미하지 않는지 분리했습니다:
  - rollback은 later reviewed-memory effect reversal이지 source-message correction history rollback이 아님
  - disable은 later stop-apply이지 candidate deletion이 아님
  - conflict visibility는 aggregate-level reviewed-signal conflict visibility이지 same-source edit mismatch만 뜻하지 않음
  - operator-audit은 explicit local transition trace이지 `task_log`를 canonical store로 승격시키는 것이 아님
- current source-message candidate / durable projection / review trace / recurrence key / same-session aggregate / blocked marker / future reviewed-memory layer 경계를 다시 좁게 고정했습니다.
- current blocked marker를 넘는 future smallest surface는 still read-only인 aggregate-level `reviewed_memory_precondition_status` object only로 추천했고, reviewed-memory store/apply와 cross-session counting은 계속 later로 유지했습니다.

## 검증
- 실행:
  - `git diff --check`
  - `rg -n "blocked_pending_reviewed_memory_boundary|aggregate_promotion_marker|reviewed-memory|rollback|disable|conflict|operator-audit|cross-session" docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md README.md plandoc/2026-03-28-reviewed-memory-preconditions-contract.md`
- 미실행:
  - `python3 -m py_compile ...`
  - `python3 -m unittest ...`
  - `make e2e-test`
- 사유:
  - 이번 라운드는 문서 작업만 수행했고 제품 코드는 변경하지 않았습니다.

## 남은 리스크
- 이전 closeout에서 이어받은 리스크:
  - blocked marker는 shipped 되었지만 unblock preconditions가 정확히 고정되지 않아 later promotion/apply 경계가 흐릴 수 있었습니다.
- 이번 라운드에서 해소한 리스크:
  - exact precondition family와 각 의미를 분리해 same-session aggregate unblock boundary를 정직하게 고정했습니다.
  - same-session unblock과 cross-session counting을 별도 레이어로 다시 분리했습니다.
- 여전히 남은 리스크:
  - read-only precondition-status surface가 아직 구현되지 않았습니다.
  - reviewed-memory store, reviewed-memory apply, rollback / disable controls, cross-session stale-resolution은 여전히 미구현입니다.
