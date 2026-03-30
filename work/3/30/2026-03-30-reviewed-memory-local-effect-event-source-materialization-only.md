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
- `plandoc/2026-03-29-reviewed-memory-applied-effect-target-contract.md`
- `plandoc/2026-03-29-reviewed-memory-rollback-backer-contract.md`
- `plandoc/2026-03-29-reviewed-memory-capability-basis-source-contract.md`
- `plandoc/2026-03-29-reviewed-memory-unblocked-capability-path-contract.md`
- `plandoc/2026-03-29-reviewed-memory-local-effect-presence-event-contract.md`
- `work/3/30/2026-03-30-reviewed-memory-local-effect-event-source-materialization-only.md`

## 사용 skill
- `doc-sync`
- `release-check`
- `work-log-closeout`

## 변경 이유
- 착수 전에 최신 summary implementation closeout인 `work/3/30/2026-03-30-summary-chunks-selection-split.md`와 최신 reviewed-memory closeout인 `work/3/30/2026-03-30-reviewed-memory-local-effect-event-producer-materialization-only.md`를 함께 읽고 이어받았습니다.
- summary 쪽 truthful split은 이미 shipped 상태로 닫혀 있었고, reviewed-memory chain의 다음 최소 truth gap이 `reviewed_memory_local_effect_presence_event_source` 부재였습니다.
- 이전 라운드 리스크는 exact same-aggregate producer까지는 materialize되지만 그 위 event-source가 계속 비어 있어서 source-consumer, target, handle, capability basis 쪽 검증을 더 올릴 수 없다는 점이었습니다.

## 핵심 변경
- `_build_recurrence_aggregate_reviewed_memory_local_effect_presence_event_source(...)`가 이제 exact same-aggregate `reviewed_memory_local_effect_presence_event_producer` 결과가 있을 때만 internal-only event-source를 materialize합니다.
- event-source는 `same_session_exact_recurrence_aggregate_only`, exact `aggregate_identity_ref`, supporting refs, `boundary_source_ref`, `applied_effect_id`, `present_locally_at`를 그대로 재검증하고 재사용합니다.
- `first_seen_at`는 계속 necessary-only anchor로 유지했고, `candidate_review_record`, queue presence, approval-backed save support, historical adjunct, `task_log` replay alone은 여전히 proof/fact/source/target/backer basis에서 제외했습니다.
- `reviewed_memory_local_effect_presence_record(...)`는 이번 라운드에도 explicit absence를 유지하도록 막아 두어 event-source alone이 record, target, handle, `rollback_source_ref`, `reviewed_memory_capability_basis`, `unblocked_all_required`, `reviewed_memory_transition_record`를 연쇄로 열지 않게 했습니다.
- focused regression은 store-backed exact aggregate에서 event-source만 materialize되고 record 이상은 계속 `None`이며, capability status와 UI blocked state가 그대로라는 점을 고정하도록 갱신했습니다.
- root docs와 plandoc은 current truth를 `event_source shipped / record next`로 동기화했습니다.

## 검증
- `rg -n "reviewed_memory_local_effect_presence_event_producer|reviewed_memory_local_effect_presence_event_source|reviewed_memory_local_effect_presence_record|reviewed_memory_applied_effect_target|reviewed_memory_reversible_effect_handle|rollback_source_ref|reviewed_memory_capability_basis|unblocked_all_required|blocked_all_required|reviewed_memory_transition_record" app/web.py storage/session_store.py core/agent_loop.py tests/test_smoke.py tests/test_web_app.py docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md plandoc/2026-03-29-reviewed-memory-local-effect-presence-event-contract.md plandoc/2026-03-29-reviewed-memory-applied-effect-target-contract.md plandoc/2026-03-29-reviewed-memory-rollback-backer-contract.md`
- `python3 -m py_compile app/web.py storage/session_store.py core/agent_loop.py tests/test_smoke.py tests/test_web_app.py`
- `python3 -m unittest -v tests.test_smoke tests.test_web_app`
  - `Ran 176 tests in 2.118s`
- `make e2e-test`
  - `12 passed (3.4m)`
- `git diff --check`

## 남은 리스크
- 이번 라운드에서 해소한 리스크는 same-aggregate producer 위에 truthful event-source가 없어서 chain 검증이 한 단계 멈춰 있던 점입니다.
- 여전히 `reviewed_memory_local_effect_presence_record`, `reviewed_memory_applied_effect_target`, `reviewed_memory_reversible_effect_handle`, `rollback_source_ref`, `reviewed_memory_capability_basis`, `reviewed_memory_transition_record`는 truthfully 비어 있거나 unresolved입니다.
- `reviewed_memory_capability_status.capability_outcome`와 `reviewed_memory_unblock_contract.unblock_status`는 계속 `blocked_all_required`가 맞습니다.
- aggregate trigger UI는 여전히 blocked-but-visible이고 `검토 메모 적용 시작`은 disabled로 남아 있습니다.
- 이번 라운드 착수 시점의 current next slice가 summary가 아니라 reviewed-memory `event-source only`였던 이유는 summary boundary work가 이미 shipped truth로 닫혀 있었고, reviewed-memory chain에서 exact same-aggregate producer 위 helper 하나가 아직 비어 있었기 때문입니다.
- 이번 라운드 이후의 다음 최소 slice는 summary reopen이 아니라 one truthful same-aggregate local `reviewed_memory_local_effect_presence_record` materialization only입니다.
