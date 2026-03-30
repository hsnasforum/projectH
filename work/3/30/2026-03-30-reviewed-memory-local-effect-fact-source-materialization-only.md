## 변경 파일
- `app/web.py`
- `tests/test_smoke.py`
- `tests/test_web_app.py`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/ARCHITECTURE.md`
- `docs/MILESTONES.md`
- `docs/NEXT_STEPS.md`
- `docs/TASK_BACKLOG.md`

## 사용 skill
- `doc-sync`
- `release-check`
- `work-log-closeout`

## 변경 이유
- 직전 closeout에서 이어진 핵심 리스크는 exact same-aggregate proof-boundary와 fact-source-instance는 이미 열렸지만, 그 위의 truthful local `reviewed_memory_local_effect_presence_fact_source` helper가 아직 absence였다는 점이었습니다.
- 이번 라운드 목표는 그 gap만 가장 작게 메우면서도, raw-event 이상 체인과 capability/status/UI 계약은 그대로 묶어 두는 것이었습니다.

## 핵심 변경
- `_build_recurrence_aggregate_reviewed_memory_local_effect_presence_fact_source(...)`가 이제 exact same-aggregate `reviewed_memory_local_effect_presence_fact_source_instance` result가 있을 때만 internal same-session fact-source를 materialize하도록 연결했습니다.
- 새 fact-source는 현재 aggregate identity, supporting refs, resolved `boundary_source_ref`, necessary-only `first_seen_at`, current `evaluated_at`가 모두 exact same aggregate에 묶일 때만 열리고, lower layer의 `applied_effect_id`와 `present_locally_at`를 그대로 재사용합니다.
- `reviewed_memory_local_effect_presence_event`, `reviewed_memory_local_effect_presence_event_producer`, `reviewed_memory_local_effect_presence_event_source`, `reviewed_memory_local_effect_presence_record`, `reviewed_memory_applied_effect_target`, `reviewed_memory_reversible_effect_handle`, `rollback_source_ref`, `reviewed_memory_capability_basis`, `reviewed_memory_transition_record`는 이번 라운드에서도 계속 absent 또는 unresolved로 유지했습니다.
- focused regression을 추가해 fact-source positive path와 event 이상 체인의 continued absence를 함께 고정했습니다.
- root docs는 current truth를 fact-source materialized / event absent 기준으로 동기화했고, 다음 최소 slice wording을 local event materialization only로 옮겼습니다.

## 검증
- `python3 -m py_compile app/web.py storage/session_store.py core/agent_loop.py tests/test_smoke.py tests/test_web_app.py`
- `python3 -m unittest -v tests.test_smoke tests.test_web_app`
- `make e2e-test`
- `git diff --check`
- `rg -n "reviewed_memory_local_effect_presence_fact_source|reviewed_memory_local_effect_presence_event\\b|reviewed_memory_local_effect_presence_event_producer|reviewed_memory_local_effect_presence_event_source|reviewed_memory_local_effect_presence_record|reviewed_memory_applied_effect_target|reviewed_memory_reversible_effect_handle|rollback_source_ref|reviewed_memory_capability_basis|unblocked_all_required|blocked_all_required|reviewed_memory_transition_record" app/web.py storage/session_store.py core/agent_loop.py tests/test_smoke.py tests/test_web_app.py docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md plandoc/2026-03-29-reviewed-memory-local-effect-presence-fact-source-contract.md plandoc/2026-03-29-reviewed-memory-local-effect-presence-event-contract.md plandoc/2026-03-29-reviewed-memory-applied-effect-target-contract.md plandoc/2026-03-29-reviewed-memory-rollback-backer-contract.md"`

## 남은 리스크
- 이전 closeout에서 남아 있던 `fact_source_instance exists but fact_source absent` 리스크는 이번 라운드에서 해소했습니다.
- 여전히 raw-event와 producer/event-source/source-consumer/target/handle/rollback backer 계층은 truthful materialization이 없어 계속 absent 또는 unresolved입니다.
- `reviewed_memory_capability_basis`는 여전히 absent이고 `reviewed_memory_capability_status.capability_outcome`도 계속 `blocked_all_required`입니다.
- proof/fact/source 계층은 여전히 payload-hidden internal only이며, UI의 `검토 메모 적용 시작`은 계속 blocked-visible / disabled 상태입니다.
