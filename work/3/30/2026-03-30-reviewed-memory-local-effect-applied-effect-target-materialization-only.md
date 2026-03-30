## 변경 파일
- `app/web.py`
- `tests/test_smoke.py`
- `tests/test_web_app.py`
- `docs/NEXT_STEPS.md`
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`
- `docs/PRODUCT_SPEC.md`
- `docs/ARCHITECTURE.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `plandoc/2026-03-29-reviewed-memory-applied-effect-target-contract.md`
- `plandoc/2026-03-29-reviewed-memory-rollback-backer-contract.md`
- `plandoc/2026-03-29-reviewed-memory-capability-basis-source-contract.md`
- `plandoc/2026-03-29-reviewed-memory-unblocked-capability-path-contract.md`
- `work/3/30/2026-03-30-reviewed-memory-local-effect-applied-effect-target-materialization-only.md`

## 사용 skill
- `doc-sync`
- `release-check`
- `work-log-closeout`

## 변경 이유
- 최신 summary implementation closeout과 최신 reviewed-memory closeout을 둘 다 다시 읽고 이어받았습니다.
- 이전 closeout에서 이어받은 핵심 리스크는 exact same-aggregate `reviewed_memory_local_effect_presence_record`가 이미 truthfully materialize되는데도, 그 바로 위 shared internal `reviewed_memory_applied_effect_target` helper가 계속 explicit absence로 남아 있어서 contract chain이 한 단계 덜 닫혀 있었다는 점이었습니다.
- 이번 라운드는 summary reopen이 아니라 reviewed-memory `applied_effect_target only`가 current next slice인 상태였고, handle/basis/status/UI를 동시에 열면 current shipped contract를 과장하게 되므로 target helper 하나만 열었습니다.

## 핵심 변경
- `app/web.py`
  - `_build_recurrence_aggregate_reviewed_memory_applied_effect_target(...)`가 이제 오직 exact same-aggregate `reviewed_memory_local_effect_presence_record` result가 있을 때만 internal shared target을 materialize합니다.
  - target helper는 same exact aggregate identity, exact supporting refs, optional supporting review refs, matching `boundary_source_ref`, existing `applied_effect_id`, existing `present_locally_at`, necessary-only `first_seen_at` anchor를 다시 검증하고 나서만 아래 shape를 반환합니다.
    - `target_version = first_same_session_reviewed_memory_applied_effect_target_v1`
    - `target_scope = same_session_exact_recurrence_aggregate_only`
    - `effect_target_kind = applied_reviewed_memory_effect`
    - `target_capability_boundary = local_effect_presence_only`
    - `target_stage = effect_present_local_only`
  - `reviewed_memory_reversible_effect_handle(...)`는 그대로 unresolved를 유지하고, `rollback_source_ref`도 그대로 unresolved를 유지합니다.
- 테스트
  - exact same-aggregate proof-record/store-backed positive path에서 `event_source -> record -> target`까지만 materialize되고, handle / `rollback_source_ref` / `reviewed_memory_capability_basis` / `reviewed_memory_transition_record` / `blocked_all_required` UI semantics는 그대로라는 focused regression을 `tests/test_smoke.py`, `tests/test_web_app.py`에 추가했습니다.
  - mismatched aggregate identity에서는 target helper가 계속 absent인지도 같이 고정했습니다.
  - payload serialization에서는 `reviewed_memory_applied_effect_target`가 여전히 payload-visible 하지 않음을 유지했습니다.
- 문서
  - touched reviewed-memory docs와 `plandoc/`를 current truth에 맞춰, internal shared target은 now materialized but payload-hidden이고 next smallest slice는 `reviewed_memory_reversible_effect_handle only`라는 상태로 동기화했습니다.

## 검증
- 실행: `rg -n "reviewed_memory_local_effect_presence_record|reviewed_memory_applied_effect_target|reviewed_memory_reversible_effect_handle|rollback_source_ref|reviewed_memory_capability_basis|unblocked_all_required|blocked_all_required|reviewed_memory_transition_record" app/web.py storage/session_store.py core/agent_loop.py tests/test_smoke.py tests/test_web_app.py docs/NEXT_STEPS.md docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md plandoc/2026-03-29-reviewed-memory-applied-effect-target-contract.md plandoc/2026-03-29-reviewed-memory-rollback-backer-contract.md`
- 실행: `python3 -m py_compile app/web.py storage/session_store.py core/agent_loop.py tests/test_smoke.py tests/test_web_app.py`
- 실행: `python3 -m unittest -v tests.test_smoke tests.test_web_app`
  - 결과: `Ran 176 tests in 2.072s`
  - 결과: `OK`
- 실행: `make e2e-test`
  - 결과: `12 passed (3.4m)`
- 실행: `git diff --check`

## 남은 리스크
- 이번 라운드에서 해소한 리스크는 exact same-aggregate source-consumer record가 이미 있는 current repo 상태에서도 shared internal applied-effect target helper가 계속 비어 있던 점입니다.
- 여전히 남은 리스크는 rollback-side capability layer가 아직 없다는 점입니다. 그래서 `reviewed_memory_reversible_effect_handle`는 계속 unresolved이고 `rollback_source_ref`도 계속 unresolved입니다.
- `reviewed_memory_capability_basis`, `reviewed_memory_capability_status.capability_outcome = blocked_all_required`, `reviewed_memory_transition_record`, enabled submit, note input, reviewed-memory apply result는 이번 라운드에서도 그대로 막혀 있어야 하며 실제로 그대로 유지됩니다.
- `first_seen_at` alone, `candidate_review_record`, approval-backed save support, historical adjuncts, `review_queue_items`, `task_log` replay alone은 여전히 canonical local proof/fact/source/target/backer basis가 아닙니다.
- current next slice가 summary reopen이 아니라 reviewed-memory `applied_effect_target only`였던 이유는 summary-side truthful split이 이미 shipped truth로 닫혀 있고, reviewed-memory chain에서는 `record` 위의 one-helper gap만 남아 있었기 때문입니다. 이제 다음 최소 슬라이스는 truthful same-aggregate local reversible-effect handle materialization only입니다.
