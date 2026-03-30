## 변경 파일
- `app/web.py`
- `tests/test_smoke.py`
- `tests/test_web_app.py`
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
- `work/3/29/2026-03-29-reviewed-memory-local-effect-proof-record-writer-implementation.md`

## 사용 skill
- `doc-sync`
- `release-check`
- `work-log-closeout`

## 변경 이유
- 직전 closeout들에서 이어진 핵심 리스크는 `reviewed_memory_local_effect_presence_proof_record` helper가 exact same-session internal store entry를 consume할 수 있어도, current shipped path 어디에서도 그 canonical proof-record/store entry를 truthfully mint하지 못한다는 점이었습니다.
- 이번 라운드는 그 리스크만 가장 좁게 해소해야 했고, proof-boundary 이상 체인이나 blocked UI semantics를 동시에 열면 current shipped contract를 과장하게 되므로 writer 하나만 열도록 범위를 제한했습니다.

## 핵심 변경
- `app/web.py`의 session serialization 경로에서 recurrence aggregate를 한 번 예비 계산한 뒤, current exact aggregate state와 exact supporting refs, resolved `boundary_source_ref`, necessary-only `first_seen_at` anchor를 모두 만족할 때만 one exact payload-hidden canonical proof-record/store entry를 mint하도록 했습니다.
- 새 internal writer는 `proof_record_version`, `proof_record_scope`, `aggregate_identity_ref`, `supporting_source_message_refs`, `supporting_candidate_refs`, optional `supporting_review_refs`, `boundary_source_ref`, `effect_target_kind`, `proof_capability_boundary`, `proof_record_stage`, deterministic `applied_effect_id`, `present_locally_at`만 담고, helper는 여전히 그 exact same-session entry가 있을 때만 결과를 만들도록 유지했습니다.
- writer가 열려도 `reviewed_memory_local_effect_presence_proof_boundary`, `reviewed_memory_local_effect_presence_fact_source_instance`, `reviewed_memory_local_effect_presence_fact_source`, `reviewed_memory_local_effect_presence_event`, `reviewed_memory_local_effect_presence_event_producer`, `reviewed_memory_local_effect_presence_event_source`, `reviewed_memory_local_effect_presence_record`, `reviewed_memory_applied_effect_target`, `reviewed_memory_reversible_effect_handle`, `rollback_source_ref`, `reviewed_memory_capability_basis`, `reviewed_memory_transition_record`는 계속 absent/unresolved로 남도록 유지했습니다.
- `first_seen_at` alone, `candidate_review_record`, `review_queue_items`, approval-backed save support, historical adjunct, `task_log` replay alone로는 canonical proof/fact/source/target/backer가 열리지 않는 focused regression을 추가했고, root docs와 `plandoc/`는 "next slice = proof-boundary materialization only"로 동기화했습니다.
- 이전 closeout에서 남은 "writer 부재" 리스크는 해소했습니다. 대신 canonical proof-record/store가 아직 proof-boundary 위 계층을 열지 않으며, store persistence boundary를 별도 local store로 widen할지 여부는 여전히 open question으로 남겼습니다.

## 검증
- 실행함: `python3 -m py_compile app/web.py storage/session_store.py core/agent_loop.py tests/test_smoke.py tests/test_web_app.py`
- 실행함: `python3 -m unittest -v tests.test_smoke tests.test_web_app`
- 실행함: `make e2e-test`
- 실행함: `git diff --check`
- 실행함: `rg -n "reviewed_memory_local_effect_presence_proof_record_store|reviewed_memory_local_effect_presence_proof_record|reviewed_memory_local_effect_presence_proof_boundary|reviewed_memory_local_effect_presence_fact_source_instance|reviewed_memory_local_effect_presence_fact_source|reviewed_memory_local_effect_presence_event\\b|reviewed_memory_local_effect_presence_event_producer|reviewed_memory_local_effect_presence_event_source|reviewed_memory_local_effect_presence_record|reviewed_memory_applied_effect_target|reviewed_memory_reversible_effect_handle|rollback_source_ref|reviewed_memory_capability_basis|unblocked_all_required|blocked_all_required|reviewed_memory_transition_record" app/web.py tests/test_smoke.py tests/test_web_app.py docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md plandoc/2026-03-29-reviewed-memory-local-effect-proof-record-contract.md plandoc/2026-03-29-reviewed-memory-local-effect-proof-boundary-contract.md plandoc/2026-03-29-reviewed-memory-local-effect-presence-fact-source-contract.md plandoc/2026-03-29-reviewed-memory-local-effect-presence-event-contract.md plandoc/2026-03-29-reviewed-memory-applied-effect-target-contract.md plandoc/2026-03-29-reviewed-memory-rollback-backer-contract.md plandoc/2026-03-29-reviewed-memory-capability-basis-source-contract.md plandoc/2026-03-29-reviewed-memory-unblocked-capability-path-contract.md"`

## 남은 리스크
- current writer는 payload-hidden same-session canonical proof-record/store entry만 mint하고, proof-boundary helper above layer는 여전히 `None`을 유지합니다. 따라서 fact-source/event/target/basis/unblocked path는 아직 전혀 열리지 않았습니다.
- `rollback_source_ref`는 여전히 exact-scope-validated but unresolved 상태이고, `reviewed_memory_capability_status.capability_outcome`도 계속 `blocked_all_required`입니다.
- current blocked aggregate-card affordance는 그대로 유지되므로 UI readiness나 submit semantics는 이번 라운드에서 전혀 넓어지지 않았습니다.
- canonical proof-record/store boundary를 나중에 session persistence only로 둘지, 별도 reviewed-memory local store로 분리할지는 아직 결정되지 않았습니다.
