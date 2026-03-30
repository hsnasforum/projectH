# 2026-03-30 reviewed-memory local effect reversible-effect handle materialization only

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
- `plandoc/2026-03-29-reviewed-memory-rollback-backer-contract.md`
- `plandoc/2026-03-29-reviewed-memory-capability-basis-source-contract.md`
- `plandoc/2026-03-29-reviewed-memory-unblocked-capability-path-contract.md`

## 사용 skill
- `doc-sync`
- `release-check`
- `work-log-closeout`

## 변경 이유
- 최신 reviewed-memory closeout인 `2026-03-30-reviewed-memory-local-effect-applied-effect-target-materialization-only.md`와 최신 summary implementation closeout인 `2026-03-30-summary-chunks-selection-split.md`를 읽고 이어받았습니다.
- 이전 라운드까지 same-aggregate local proof/fact/source chain은 `reviewed_memory_applied_effect_target`까지는 truthfully materialize되었지만, rollback-side later local backer인 `reviewed_memory_reversible_effect_handle`은 계속 비어 있었습니다.
- current next slice는 summary reopen이 아니라 reviewed-memory `reversible_effect_handle only`였습니다. summary truthful split은 이미 shipped truth로 닫혀 있고, reviewed-memory chain만 한 단계 더 위로 정확히 열 수 있는 상태였기 때문입니다.

## 핵심 변경
- `app/web.py`에서 `_build_recurrence_aggregate_reviewed_memory_reversible_effect_handle(...)`를 구현해, 오직 exact same-aggregate `reviewed_memory_applied_effect_target`와 exact same-aggregate `reviewed_memory_rollback_contract`가 동시에 맞을 때만 internal same-session rollback-capability handle을 materialize하도록 연결했습니다.
- handle은 `same_session_exact_recurrence_aggregate_only` 범위에서만 열리고, exact aggregate identity, supporting refs, optional supporting review refs, `boundary_source_ref`, `rollback_contract_ref`, necessary-only `first_seen_at` anchor, `applied_effect_id`, `present_locally_at`를 다시 검증한 뒤 deterministic `handle_id`와 `defined_at`를 포함한 internal-only 결과를 만듭니다.
- 같은 라운드에서 `_resolve_recurrence_aggregate_reviewed_memory_rollback_source_ref(...)`도 그 same handle만 backer로 하여 resolve되도록 열었습니다. 이번 라운드에서 `rollback_source_ref`가 resolved 된 이유는, current repo에 exact same-aggregate shared target 위에서 exact rollback contract를 재사용하는 truthful handle path가 실제로 존재했기 때문입니다.
- `disable_source_ref`, `conflict_source_ref`, `transition_audit_source_ref`는 그대로 unresolved로 유지했고, 그 결과 `reviewed_memory_capability_source_refs`는 여전히 incomplete / absent입니다.
- `reviewed_memory_capability_basis`는 계속 absent이고, `reviewed_memory_capability_status.capability_outcome`는 계속 `blocked_all_required`입니다. handle 하나가 생겼다고 full capability source family, basis, status widening, emitted transition record를 함께 열지는 않았습니다.
- payload-visible `reviewed_memory_reversible_effect_handle`, payload-visible `rollback_source_ref`, `reviewed_memory_transition_record`, enabled submit flow, note input은 모두 추가하지 않았습니다. aggregate card UI는 여전히 visible-but-disabled 상태입니다.

## 검증
- `python3 -m py_compile app/web.py tests/test_smoke.py tests/test_web_app.py`
- `python3 -m py_compile app/web.py storage/session_store.py core/agent_loop.py tests/test_smoke.py tests/test_web_app.py`
- `python3 -m unittest -v tests.test_smoke tests.test_web_app`
  - `Ran 176 tests in 2.555s`
- `make e2e-test`
  - `12 passed (3.5m)`
- `git diff --check`
- `rg -n "reviewed_memory_reversible_effect_handle|rollback_source_ref|reviewed_memory_capability_source_refs|reviewed_memory_capability_basis|unblocked_all_required|blocked_all_required|reviewed_memory_transition_record" app/web.py storage/session_store.py core/agent_loop.py tests/test_smoke.py tests/test_web_app.py docs/NEXT_STEPS.md docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md plandoc/2026-03-29-reviewed-memory-rollback-backer-contract.md plandoc/2026-03-29-reviewed-memory-capability-basis-source-contract.md`

## 남은 리스크
- 이번 라운드에서 해소한 리스크:
  - exact same-aggregate shared target above layer에 real rollback-capability backer가 없어서 `rollback_source_ref`가 항상 unresolved로 남던 문제를 해결했습니다.
- 여전히 남은 리스크:
  - `disable_source_ref`, `conflict_source_ref`, `transition_audit_source_ref`는 아직 unresolved입니다.
  - `reviewed_memory_capability_source_refs` 전체 family는 still incomplete / absent입니다.
  - `reviewed_memory_capability_basis`, `unblocked_all_required`, payload-visible transition record, apply result는 여전히 닫혀 있습니다.
  - `first_seen_at` alone, `candidate_review_record`, approval-backed save support, historical adjunct, `task_log` replay alone은 계속 local proof/fact/source/target/backer basis가 아닙니다.
- 다음 최소 slice는 summary reopen이 아니라 reviewed-memory `disable_source_ref only`가 더 정직합니다. rollback-side handle과 `rollback_source_ref`는 이번 라운드에서 실제 truthful path가 생겼지만, capability basis를 열기 위해 필요한 full source family는 아직 남은 three refs가 닫혀 있기 때문입니다.
