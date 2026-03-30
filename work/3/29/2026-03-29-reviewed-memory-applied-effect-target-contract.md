# 2026-03-29 Reviewed-Memory Applied-Effect Target Contract

## 변경 파일
- `docs/PRODUCT_SPEC.md`
- `docs/ARCHITECTURE.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`
- `docs/NEXT_STEPS.md`
- `plandoc/2026-03-29-reviewed-memory-applied-effect-target-contract.md`
- `plandoc/2026-03-29-reviewed-memory-rollback-backer-contract.md`
- `plandoc/2026-03-29-reviewed-memory-capability-basis-source-contract.md`
- `plandoc/2026-03-29-reviewed-memory-unblocked-capability-path-contract.md`
- `work/3/29/2026-03-29-reviewed-memory-applied-effect-target-contract.md`

## 사용 skill
- `mvp-scope`
- `approval-flow-audit`
- `doc-sync`
- `release-check`
- `work-log-closeout`

## 변경 이유
- 직전 closeout에서 이어받은 핵심 리스크는 `reviewed_memory_reversible_effect_handle` helper는 이미 구현됐지만, 그 helper가 later truthfully 참조해야 할 local applied reviewed-memory effect target이 아직 정의되지 않았다는 점이었습니다.
- 이 상태를 닫지 않으면 다음 구현이 current rollback contract, support-only traces, 또는 `task_log` replay를 target/backer처럼 잘못 읽을 위험이 남아 있었습니다.
- root docs와 `plandoc`의 next-slice wording 일부도 아직 handle implementation 기준에 머물러 있어, latest implementation truth와 단계 순서가 어긋난 상태였습니다.

## 핵심 변경
- future exact target을 하나의 shared internal `reviewed_memory_applied_effect_target`으로 고정했습니다.
- target은 `same_session_exact_recurrence_aggregate_only` 범위, exact aggregate identity/supporting refs, matching `boundary_source_ref`, `effect_target_kind = applied_reviewed_memory_effect`, `target_capability_boundary = local_effect_presence_only`, `target_stage = effect_present_local_only`, local `applied_effect_id`, local `present_locally_at`를 갖는 later local target으로 정리했습니다.
- rollback-only target과 shared target 사이의 open question은 이번 라운드에서 닫았습니다.
  - first target은 shared target이 더 정직합니다.
  - 이유는 shipped `reviewed_memory_rollback_contract`와 shipped `reviewed_memory_disable_contract`가 모두 `future_applied_reviewed_memory_effect_only`를 가리키기 때문입니다.
  - rollback과 later disable은 shared target 위의 separate handles / separate contract refs로 분리하기로 고정했습니다.
- current layer boundaries도 다시 명시했습니다.
  - current rollback contract: contract-only
  - current unresolved rollback resolver: exact-scope-validated but unresolved
  - current handle helper: exists but unresolved
  - future applied-effect target: later local target only
  - future full source family / basis / unblocked status / emitted record / apply result: 모두 그 위 later layers
- root docs와 `plandoc`의 stale next-slice wording을 모두 current truth 기준으로 다시 맞췄습니다.
  - next slice는 더 이상 handle implementation이 아니라 `one internal applied-effect target scaffold only`입니다.

## 검증
- 실행함: `git diff --check`
- 실행함: `rg -n "reviewed_memory_reversible_effect_handle|applied reviewed-memory effect target|reviewed_memory_capability_basis|unblocked_all_required|blocked_all_required|reviewed_memory_transition_record|rollback_source_ref|disable_source_ref" docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md app/web.py app/templates/index.html plandoc/2026-03-29-reviewed-memory-applied-effect-target-contract.md plandoc/2026-03-29-reviewed-memory-rollback-backer-contract.md plandoc/2026-03-29-reviewed-memory-capability-basis-source-contract.md`
- 실행하지 않음: `python3 -m py_compile ...`, `python3 -m unittest ...`, `make e2e-test`
- 미실행 이유: 이번 라운드는 제품 코드 변경 없는 문서 계약 작업이었기 때문입니다.

## 남은 리스크
- 이전 closeout에서 이어받은 리스크 중 “handle helper 아래의 exact later local target 부재”는 이번 라운드에서 contract 수준으로는 해소했습니다.
- 이번 라운드에서 해소한 리스크는 다음 구현이 handle implementation을 또 반복하거나 rollback-only target을 임의로 늘리는 식으로 잘못 widen될 위험입니다.
- 여전히 남은 리스크는 current repo에 `reviewed_memory_applied_effect_target` 자체가 아직 구현되지 않았다는 점입니다.
- 따라서 current `rollback_source_ref`는 계속 unresolved가 truthful하고, full source family / `reviewed_memory_capability_basis` / `unblocked_all_required` / emitted transition record / apply result도 계속 닫혀 있어야 합니다.
