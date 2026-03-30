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

## 사용 skill
- `doc-sync`
- `release-check`
- `work-log-closeout`

## 변경 이유
- 이전 closeout에서 이어받은 리스크는 `reviewed_memory_local_effect_presence_proof_record` contract와 helper는 이미 있었지만, 그 helper가 truthfully consume할 exact canonical local proof-record/store entry materialization path가 코드에 없었다는 점입니다.
- 이번 라운드에서는 상위 helper chain을 열지 않고, same-session exact aggregate scope에서만 consume 가능한 가장 작은 internal canonical proof-record materialization path만 구현해야 했습니다.
- 동시에 current shipped flow에는 아직 truthful proof-record writer가 없으므로, 기본 repo state는 계속 absence여야 했습니다.

## 핵심 변경
- `app/web.py`에서 internal same-session store boundary `reviewed_memory_local_effect_presence_proof_record_store`를 읽고, exact aggregate candidate에 internal-only `_reviewed_memory_local_effect_presence_proof_record_store_entries`로 주입한 뒤 payload 직렬화 시 다시 제거하도록 정리했습니다.
- `_build_recurrence_aggregate_reviewed_memory_local_effect_presence_proof_record(...)`는 이제 exact same-aggregate store entry가 하나일 때만 canonical proof record를 materialize합니다.
- materialization 조건은 `proof_record_version`, `proof_record_scope`, `aggregate_identity_ref`, `supporting_source_message_refs`, `supporting_candidate_refs`, optional `supporting_review_refs`, `boundary_source_ref`, `effect_target_kind`, `proof_capability_boundary`, `proof_record_stage`, `applied_effect_id`, `present_locally_at` exact match입니다.
- `first_seen_at` alone, `candidate_review_record`, `review_queue_items`, approval-backed save support, historical adjunct, `task_log` replay alone은 계속 proof-record basis에서 제외했습니다.
- `reviewed_memory_local_effect_presence_proof_boundary`, fact-source-instance helper, fact-source helper, raw-event helper, producer helper, event-source helper, source-consumer helper, target helper, handle helper, `rollback_source_ref`, `reviewed_memory_capability_basis`, `reviewed_memory_transition_record`, `blocked_all_required` UI semantics는 그대로 유지했습니다.
- 회귀 테스트는 exact internal store entry가 있을 때 proof-record helper만 materialize되고 상위 helper chain과 payload/UI는 그대로 닫혀 있는지 고정했습니다.
- 문서는 current truth를 반영해 “helper는 now consume-ready, but current shipped flows still mint no proof-record entry”로 맞췄고, next slice를 one truthful canonical proof-record writer only로 갱신했습니다.

## 검증
- 실행:
  - `python3 -m py_compile app/web.py storage/session_store.py core/agent_loop.py tests/test_smoke.py tests/test_web_app.py`
  - `python3 -m unittest -v tests.test_smoke tests.test_web_app`
  - `make e2e-test`
  - `git diff --check`
  - `rg -n "reviewed_memory_local_effect_presence_proof_record|reviewed_memory_local_effect_presence_proof_boundary|reviewed_memory_local_effect_presence_fact_source_instance|reviewed_memory_local_effect_presence_fact_source|reviewed_memory_local_effect_presence_event\\b|reviewed_memory_local_effect_presence_event_producer|reviewed_memory_local_effect_presence_event_source|reviewed_memory_local_effect_presence_record|reviewed_memory_applied_effect_target|reviewed_memory_reversible_effect_handle|rollback_source_ref|reviewed_memory_capability_basis|unblocked_all_required|blocked_all_required|reviewed_memory_transition_record" app/web.py storage/session_store.py core/agent_loop.py tests/test_smoke.py tests/test_web_app.py docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md plandoc/2026-03-29-reviewed-memory-local-effect-proof-record-contract.md plandoc/2026-03-29-reviewed-memory-local-effect-proof-boundary-contract.md plandoc/2026-03-29-reviewed-memory-local-effect-presence-fact-source-contract.md plandoc/2026-03-29-reviewed-memory-local-effect-presence-event-contract.md plandoc/2026-03-29-reviewed-memory-applied-effect-target-contract.md plandoc/2026-03-29-reviewed-memory-rollback-backer-contract.md"`
- 결과:
  - `python3 -m unittest -v tests.test_smoke tests.test_web_app` -> `Ran 171 tests ... OK`
  - `make e2e-test` -> `12 passed`

## 남은 리스크
- 이번 라운드에서 해소한 리스크는 canonical proof-record helper가 exact same-session internal store entry를 truthfully consume할 수 있는 code path 부재였습니다.
- 여전히 남은 리스크는 current shipped flows 어디에서도 `reviewed_memory_local_effect_presence_proof_record_store` entry를 실제로 mint하지 않는다는 점입니다. 그래서 기본 repo state에서는 proof-record helper도 계속 absence이고, proof-boundary 및 모든 상위 helper도 그대로 닫혀 있습니다.
- 다음 구현 슬라이스는 one truthful same-aggregate canonical local proof-record writer only가 가장 작습니다. 이 writer가 생기기 전에는 proof-boundary helper materialization, fact-source-instance helper materialization, raw-event/helper chain, basis, `unblocked_all_required`, enabled trigger, emitted record를 열면 widening이 됩니다.
