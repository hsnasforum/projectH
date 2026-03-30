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
- 직전 closeout에서 이어받은 핵심 리스크는 exact same-aggregate proof-boundary까지는 truthfully 열렸지만, 그 바로 위 `reviewed_memory_local_effect_presence_fact_source_instance` helper가 여전히 `None`을 반환해서 helper chain의 다음 truthful lower fact layer가 비어 있다는 점이었습니다.
- 이번 라운드는 그 리스크만 해소하고, `fact_source` 이상 상위 체인과 capability/UI/transition semantics는 그대로 잠가 둔 채 one truthful same-aggregate local fact-source-instance materialization only를 구현하기 위해 진행했습니다.

## 핵심 변경
- `app/web.py`
  - `_build_recurrence_aggregate_reviewed_memory_local_effect_presence_fact_source_instance(...)`가 이제 exact same-aggregate proof-boundary result가 있을 때만 internal-only result를 materialize합니다.
  - helper는 current aggregate identity, supporting refs, resolved `boundary_source_ref`, necessary-only `first_seen_at`, reused `applied_effect_id`, reused `present_locally_at`가 모두 exact same aggregate와 맞을 때만 `fact_source_instance_version`, `fact_source_instance_scope`, `fact_capability_boundary`, `fact_stage`를 포함한 최소 shape를 반환합니다.
  - `_build_recurrence_aggregate_reviewed_memory_local_effect_presence_fact_source(...)`는 새 fact-source-instance를 probe만 하고 계속 `None`을 반환하도록 유지해서 이번 라운드 범위를 fact-source-instance까지만 고정했습니다.
- 회귀 테스트
  - truthful hidden proof-record/store entry와 proof-boundary가 있을 때 fact-source-instance만 열리고, `fact_source`, event family, target, handle, `rollback_source_ref`, `reviewed_memory_capability_basis`, `reviewed_memory_transition_record`, `blocked_all_required`가 그대로 유지되는지 고정했습니다.
  - fake injected fact-source-instance payload, support-only signals, historical adjunct, approval-backed save, `task_log` replay alone으로 higher chain이 열리지 않는 경로를 계속 검증했습니다.
- 문서 동기화
  - root docs와 `plandoc/`를 현재 truth에 맞게 갱신했습니다.
  - proof-record writer 존재, proof-boundary materialization 완료, fact-source-instance materialization 완료, next slice가 `fact_source` only라는 현재 상태로 맞췄습니다.

## 검증
- 실행: `python3 -m py_compile app/web.py storage/session_store.py core/agent_loop.py tests/test_smoke.py tests/test_web_app.py`
- 실행: `python3 -m unittest -v tests.test_smoke tests.test_web_app`
- 실행: `make e2e-test`
- 실행: `git diff --check`
- 실행: `rg -n "reviewed_memory_local_effect_presence_fact_source_instance|reviewed_memory_local_effect_presence_fact_source|reviewed_memory_local_effect_presence_event\\b|reviewed_memory_local_effect_presence_event_producer|reviewed_memory_local_effect_presence_event_source|reviewed_memory_local_effect_presence_record|reviewed_memory_applied_effect_target|reviewed_memory_reversible_effect_handle|rollback_source_ref|reviewed_memory_capability_basis|unblocked_all_required|blocked_all_required|reviewed_memory_transition_record" app/web.py storage/session_store.py core/agent_loop.py tests/test_smoke.py tests/test_web_app.py docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md plandoc/2026-03-29-reviewed-memory-local-effect-presence-fact-source-contract.md plandoc/2026-03-29-reviewed-memory-local-effect-presence-event-contract.md plandoc/2026-03-29-reviewed-memory-applied-effect-target-contract.md plandoc/2026-03-29-reviewed-memory-rollback-backer-contract.md"`

## 남은 리스크
- 이번 라운드에서 해소한 리스크:
  - truthful same-aggregate fact-source-instance helper path가 더 이상 비어 있지 않고, exact same-aggregate proof-boundary 위에서만 재사용된 `applied_effect_id`와 `present_locally_at`로 materialize됩니다.
- 여전히 남은 리스크:
  - `reviewed_memory_local_effect_presence_fact_source`는 아직 absent입니다.
  - `reviewed_memory_local_effect_presence_event`, `reviewed_memory_local_effect_presence_event_producer`, `reviewed_memory_local_effect_presence_event_source`, `reviewed_memory_local_effect_presence_record`, `reviewed_memory_applied_effect_target`, `reviewed_memory_reversible_effect_handle`, `rollback_source_ref`, `reviewed_memory_capability_basis`, `reviewed_memory_transition_record`는 계속 absent 또는 unresolved입니다.
  - `reviewed_memory_capability_status.capability_outcome`는 계속 `blocked_all_required`이고, aggregate card UI도 계속 blocked-but-visible입니다.
  - payload-visible emission은 이번 라운드에서도 열지 않았기 때문에, 현재 truth는 internal-only helper materialization까지만 확장되었습니다.
