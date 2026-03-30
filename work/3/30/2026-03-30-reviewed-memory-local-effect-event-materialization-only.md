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
- `work/3/30/2026-03-30-reviewed-memory-local-effect-event-materialization-only.md`

## 사용 skill
- `doc-sync`
- `release-check`
- `work-log-closeout`

## 변경 이유
- 이전 closeout 기준으로 exact same-aggregate `reviewed_memory_local_effect_presence_fact_source`까지는 truthfully materialize됐지만, 그 위 `reviewed_memory_local_effect_presence_event` helper는 아직 absent였습니다.
- 이번 라운드 목표는 payload-visible surface, blocked aggregate affordance, capability outcome, transition record absence를 그대로 둔 채, exact same-aggregate lower fact-source 결과 위에 one truthful local event helper만 여는 것이었습니다.
- `docs/NEXT_STEPS.md`를 포함한 touched docs에는 next slice가 이미 `event only`여야 했고, 남아 있던 residual stale fact-source wording도 같이 정리해야 했습니다.

## 핵심 변경
- `app/web.py`
  - `_build_recurrence_aggregate_reviewed_memory_local_effect_presence_event(...)`를 실제 lower chain에 연결했습니다.
  - helper는 exact same-aggregate `reviewed_memory_local_effect_presence_fact_source`가 있을 때만 materialize되고, current aggregate identity, supporting refs, resolved `boundary_source_ref`, necessary-only `first_seen_at`, current `evaluated_at`가 모두 맞을 때만 결과를 만듭니다.
  - 새 event result는 새 identity나 시간을 발명하지 않고 lower fact-source의 `applied_effect_id`와 `present_locally_at`를 그대로 재사용합니다.
  - `reviewed_memory_local_effect_presence_event_producer(...)`는 여전히 explicit absence를 유지하게 두었습니다.
- `tests/test_smoke.py`
  - truthful same-aggregate lower chain이 있을 때 event helper만 열리고 producer, event-source, source-consumer, target, reversible handle, `rollback_source_ref`, capability basis, transition record는 계속 absent 또는 unresolved인 경로를 고정했습니다.
  - `first_seen_at` alone, `candidate_review_record`, queue presence, approval-backed save support, historical adjunct, `task_log` replay alone으로 higher chain이 열리지 않는 기존 경계도 유지 검증했습니다.
- `tests/test_web_app.py`
  - service/web payload 경로에서 internal event helper가 truthfully materialize되더라도 payload에는 여전히 `reviewed_memory_local_effect_presence_event`가 드러나지 않고, aggregate card와 `검토 메모 적용 시작` disabled 상태, `blocked_all_required`, transition record absence가 그대로 유지되는 점을 고정했습니다.
- 문서
  - root docs와 `plandoc/`를 current truth에 맞춰 동기화했습니다.
  - event helper는 now materialized, producer helper는 still absent, next slice는 `event_producer only`로 맞췄습니다.
  - `docs/NEXT_STEPS.md`에 남아 있던 residual stale fact-source wording은 touched section 기준으로 정리했습니다.

## 검증
- 실행:
  - `python3 -m py_compile app/web.py storage/session_store.py core/agent_loop.py tests/test_smoke.py tests/test_web_app.py`
  - `python3 -m unittest -v tests.test_smoke tests.test_web_app`
  - `make e2e-test`
  - `git diff --check`
  - `rg -n "reviewed_memory_local_effect_presence_event\\b|reviewed_memory_local_effect_presence_event_producer|reviewed_memory_local_effect_presence_event_source|reviewed_memory_local_effect_presence_record|reviewed_memory_applied_effect_target|reviewed_memory_reversible_effect_handle|rollback_source_ref|reviewed_memory_capability_basis|unblocked_all_required|blocked_all_required|reviewed_memory_transition_record" app/web.py storage/session_store.py core/agent_loop.py tests/test_smoke.py tests/test_web_app.py docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md plandoc/2026-03-29-reviewed-memory-local-effect-presence-event-contract.md plandoc/2026-03-29-reviewed-memory-applied-effect-target-contract.md plandoc/2026-03-29-reviewed-memory-rollback-backer-contract.md`
- 결과:
  - syntax check 통과
  - `tests.test_smoke`, `tests.test_web_app` 통과
  - Playwright smoke 통과
  - `git diff --check` 통과
  - sanity sweep 실행 완료

## 남은 리스크
- 이전 closeout에서 이어받은 리스크였던 "fact-source above event absence"는 이번 라운드에서 해소했습니다.
- 이번 라운드에서도 `reviewed_memory_local_effect_presence_event_producer`, `reviewed_memory_local_effect_presence_event_source`, `reviewed_memory_local_effect_presence_record`, `reviewed_memory_applied_effect_target`, `reviewed_memory_reversible_effect_handle`, `rollback_source_ref`는 여전히 absent 또는 unresolved입니다.
- `reviewed_memory_capability_basis`는 여전히 absent이고, `reviewed_memory_capability_status.capability_outcome`도 계속 `blocked_all_required`입니다.
- current aggregate card는 visible-but-disabled 그대로이며, payload-visible event, emitted transition record, apply result, UI enablement는 여전히 없습니다.
- 다음 slice는 truthful same-aggregate `reviewed_memory_local_effect_presence_event_producer` materialization only가 가장 작은 후속 범위입니다.
