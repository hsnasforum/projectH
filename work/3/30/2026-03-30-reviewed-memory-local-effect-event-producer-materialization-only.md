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
- 직전 closeout 기준으로 exact same-aggregate local event까지는 truthful 하게 materialize되지만, 그 위 `reviewed_memory_local_effect_presence_event_producer` helper는 아직 absence였습니다.
- 이번 라운드는 hidden lower chain을 재사용해 one truthful same-aggregate producer layer만 열고, event-source 이상·capability basis·transition emission은 계속 닫힌 상태로 유지해야 했습니다.
- touched docs에는 next slice가 이미 `event-source only`로 넘어가야 하므로, stale한 producer-absent wording을 같이 정리할 필요가 있었습니다.

## 핵심 변경
- `app/web.py`
  - `_build_recurrence_aggregate_reviewed_memory_local_effect_presence_event_producer(...)`가 이제 exact same-aggregate `reviewed_memory_local_effect_presence_event` result가 있을 때만 internal producer result를 materialize합니다.
  - producer helper는 current aggregate identity, supporting refs, resolved `boundary_source_ref`, necessary-only `first_seen_at`, current `evaluated_at`를 다시 검증하고, lower event의 `applied_effect_id`와 `present_locally_at`를 그대로 재사용합니다.
  - producer shape는 `producer_version = first_same_session_reviewed_memory_local_effect_presence_event_producer_v1`, `producer_scope = same_session_exact_recurrence_aggregate_only`, `producer_capability_boundary = local_effect_presence_only`, `producer_stage = presence_event_recorded_local_only`를 사용합니다.
  - `_build_recurrence_aggregate_reviewed_memory_local_effect_presence_event_source(...)`는 이번 라운드에도 producer를 probe만 하고 계속 `None`을 반환하도록 유지했습니다.
- `tests/test_smoke.py`, `tests/test_web_app.py`
  - truthful same-aggregate lower chain이 있으면 producer helper만 열리고, event-source / record / target / handle / `rollback_source_ref` / capability basis / transition record는 계속 absent 또는 unresolved인 점을 고정했습니다.
  - fake payload object, support-only signals, `first_seen_at` alone, approval-backed save support, historical adjunct, `task_log` replay alone으로 higher chain이 열리지 않는 기존 negative truth도 유지했습니다.
- docs / plandoc
  - current truth를 producer materialized / event-source still absent로 동기화했습니다.
  - next slice wording을 `event-source only`로 맞췄습니다.

## 검증
- 실행함: `python3 -m py_compile app/web.py storage/session_store.py core/agent_loop.py tests/test_smoke.py tests/test_web_app.py`
- 실행함: `python3 -m unittest -v tests.test_smoke tests.test_web_app`
- 실행함: `make e2e-test`
- 실행함: `git diff --check`
- 실행함: `rg -n "reviewed_memory_local_effect_presence_event_producer|reviewed_memory_local_effect_presence_event_source|reviewed_memory_local_effect_presence_record|reviewed_memory_applied_effect_target|reviewed_memory_reversible_effect_handle|rollback_source_ref|reviewed_memory_capability_basis|unblocked_all_required|blocked_all_required|reviewed_memory_transition_record" app/web.py storage/session_store.py core/agent_loop.py tests/test_smoke.py tests/test_web_app.py docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md plandoc/2026-03-29-reviewed-memory-local-effect-presence-event-contract.md plandoc/2026-03-29-reviewed-memory-applied-effect-target-contract.md plandoc/2026-03-29-reviewed-memory-rollback-backer-contract.md`

## 남은 리스크
- 이전 closeout에서 이어받은 리스크:
  - truthful same-aggregate local event는 열렸지만 producer helper가 아직 absent였고, 그 위 event-source / record / target / handle chain도 전부 닫혀 있었습니다.
- 이번 라운드에서 해소한 리스크:
  - exact same-aggregate lower event를 재사용하는 truthful local event-producer layer를 열어, hidden proof/fact/event chain이 producer까지는 끊기지 않도록 만들었습니다.
- 여전히 남은 리스크:
  - `reviewed_memory_local_effect_presence_event_source`, `reviewed_memory_local_effect_presence_record`, `reviewed_memory_applied_effect_target`는 계속 absent입니다.
  - `reviewed_memory_reversible_effect_handle`와 `rollback_source_ref`는 계속 unresolved입니다.
  - `reviewed_memory_capability_basis`는 계속 absent이고, `reviewed_memory_capability_status.capability_outcome`는 계속 `blocked_all_required`입니다.
  - producer layer는 internal-only라 payload-visible surface, enabled trigger submit, note input, emitted transition record에는 아무 변화가 없습니다.
  - aggregate card는 계속 blocked-but-visible이며 `검토 메모 적용 시작`은 disabled입니다.
