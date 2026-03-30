## 변경 파일
- `docs/PRODUCT_SPEC.md`
- `docs/ARCHITECTURE.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`
- `docs/NEXT_STEPS.md`
- `plandoc/2026-03-29-reviewed-memory-local-effect-proof-record-contract.md`
- `plandoc/2026-03-29-reviewed-memory-local-effect-proof-boundary-contract.md`
- `plandoc/2026-03-29-reviewed-memory-local-effect-presence-fact-source-contract.md`
- `plandoc/2026-03-29-reviewed-memory-local-effect-presence-event-contract.md`
- `plandoc/2026-03-29-reviewed-memory-applied-effect-target-contract.md`
- `plandoc/2026-03-29-reviewed-memory-rollback-backer-contract.md`
- `plandoc/2026-03-29-reviewed-memory-capability-basis-source-contract.md`
- `plandoc/2026-03-29-reviewed-memory-unblocked-capability-path-contract.md`
- `work/3/29/2026-03-29-reviewed-memory-local-effect-proof-record-contract.md`

## 사용 skill
- `mvp-scope`
- `doc-sync`
- `release-check`
- `work-log-closeout`

## 변경 이유
- 직전 closeout에서 `reviewed_memory_local_effect_presence_proof_boundary` helper는 이미 코드에 들어갔지만, 그 helper가 truthfully materialize할 exact canonical local proof record/store가 아직 없다는 리스크를 이어받았습니다.
- proof-boundary helper가 exact `first_seen_at` anchor와 support-only exclusion rule까지 이미 코드로 드러낸 상태라, 그 아래의 first canonical record/store를 먼저 닫지 않고 더 위 helper를 reopen하면 fake widening이 됩니다.
- 그래서 이번 라운드는 제품 코드를 바꾸지 않고, proof-boundary helper 아래의 smallest truthful layer를 문서 계약으로 먼저 고정했습니다.

## 핵심 변경
- one shared internal `reviewed_memory_local_effect_presence_proof_record` contract를 새로 추가했습니다.
  - `proof_record_version = first_same_session_reviewed_memory_local_effect_presence_proof_record_v1`
  - `proof_record_scope = same_session_exact_recurrence_aggregate_only`
  - exact `aggregate_identity_ref`
  - exact supporting refs
  - matching `boundary_source_ref`
  - `effect_target_kind = applied_reviewed_memory_effect`
  - `proof_capability_boundary = local_effect_presence_only`
  - `proof_record_stage = canonical_presence_recorded_local_only`
  - first local `applied_effect_id`
  - same-instant `present_locally_at`
- exact `first_seen_at`는 necessary-only anchor로 다시 고정했습니다.
  - canonical proof record가 생기기 전에는 proof boundary가 열리지 않습니다.
  - `first_seen_at` alone, `candidate_review_record`, `review_queue_items`, approval-backed save support, historical adjunct, `task_log` replay는 모두 canonical proof record가 아닙니다.
- current helper chain 경계를 다시 정리했습니다.
  - current proof-boundary helper는 still absent
  - current fact-source-instance helper는 still absent
  - current fact-source helper는 still absent
  - current raw-event / producer / event-source / source-consumer / target helper는 still absent
  - current handle helper와 `rollback_source_ref`는 still unresolved
  - `reviewed_memory_capability_basis`는 still absent
  - `capability_outcome = blocked_all_required`는 still current truth
- next slice wording을 proof-boundary materialization에서 one internal same-aggregate canonical local proof-record scaffold only로 다시 맞췄습니다.

## 검증
- 실행: `git diff --check`
- 실행: `rg -n 'reviewed_memory_local_effect_presence_proof_boundary|reviewed_memory_local_effect_presence_fact_source_instance|reviewed_memory_local_effect_presence_fact_source|reviewed_memory_local_effect_presence_event\\b|reviewed_memory_local_effect_presence_event_producer|reviewed_memory_local_effect_presence_event_source|reviewed_memory_local_effect_presence_record|reviewed_memory_applied_effect_target|reviewed_memory_reversible_effect_handle|rollback_source_ref|reviewed_memory_capability_basis|unblocked_all_required|blocked_all_required|reviewed_memory_transition_record' docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md app/web.py app/templates/index.html plandoc/2026-03-29-reviewed-memory-local-effect-proof-record-contract.md plandoc/2026-03-29-reviewed-memory-local-effect-proof-boundary-contract.md plandoc/2026-03-29-reviewed-memory-local-effect-presence-fact-source-contract.md plandoc/2026-03-29-reviewed-memory-local-effect-presence-event-contract.md plandoc/2026-03-29-reviewed-memory-applied-effect-target-contract.md plandoc/2026-03-29-reviewed-memory-rollback-backer-contract.md'`

## 남은 리스크
- 이전 closeout에서 이어받은 핵심 리스크였던 “proof-boundary helper 아래의 exact canonical lower layer가 비어 있다”는 점은 이번 라운드에서 contract로 닫았습니다.
- 하지만 canonical local proof record/store 자체는 아직 미구현이라, current proof-boundary helper는 계속 absent이고 그 위 helper chain도 그대로 absent/unresolved입니다.
- canonical proof record가 어느 internal local store boundary에 놓일지, 그리고 proof-boundary helper가 그 record를 같은 adjacent round에서 바로 consume할지 한 verification round를 더 둘지는 여전히 남아 있습니다.
