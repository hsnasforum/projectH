# 2026-03-30 reviewed-memory transition-audit-source-ref materialization only

## 변경 파일
- `app/web.py`
- `tests/test_smoke.py`
- `tests/test_web_app.py`
- `docs/NEXT_STEPS.md`
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`
- `docs/PRODUCT_SPEC.md`
- `docs/ARCHITECTURE.md`
- `plandoc/2026-03-29-reviewed-memory-capability-basis-source-contract.md`

## 사용 skill
- `doc-sync`
- `release-check`
- `work-log-closeout`

## 변경 이유
- 최신 reviewed-memory closeout인 `2026-03-30-reviewed-memory-conflict-source-ref-materialization-only.md`와 최신 summary implementation closeout인 `2026-03-30-summary-chunks-selection-split.md`를 둘 다 읽고 이어받았습니다.
- 이전 라운드까지 same-aggregate local proof/fact/source chain은 `reviewed_memory_reversible_effect_handle`까지 truthfully materialize되었고, `rollback_source_ref`, `disable_source_ref`, `conflict_source_ref`가 모두 resolved되었지만, `transition_audit_source_ref`는 계속 unresolved였습니다.
- current next slice는 summary reopen이 아니라 reviewed-memory `transition_audit_source_ref only`였습니다. summary truthful split은 이미 shipped truth로 닫혀 있고, reviewed-memory chain에서 마지막 남은 source ref만 한 단계 더 열 수 있는 상태였기 때문입니다.

## 핵심 변경
- `app/web.py`에서 `_resolve_recurrence_aggregate_reviewed_memory_transition_audit_source_ref(...)`를 구현해, 오직 exact same-aggregate `reviewed_memory_transition_audit_contract`와 exact same-aggregate shared `reviewed_memory_applied_effect_target`가 동시에 맞을 때만 internal same-session transition-audit source를 materialize하도록 연결했습니다.
- transition_audit_source_ref는 `same_session_exact_recurrence_aggregate_only` 범위에서만 열리고, exact aggregate identity, supporting refs, `boundary_source_ref`, `transition_audit_contract_ref`, `effect_target_kind = applied_reviewed_memory_effect`, `effect_capability = transition_audit_local_only`, `effect_stage = audit_defined_not_emitted`, `defined_at`를 포함한 internal-only 결과를 만듭니다.
- 이번 라운드에서 `transition_audit_source_ref`가 resolved된 이유는, current repo에 exact same-aggregate shared target 위에서 exact transition-audit contract를 재사용하는 truthful path가 실제로 존재했기 때문입니다.
- 이번 라운드에서 internal `reviewed_memory_capability_source_refs` family가 all-five-refs complete 상태로 materialize되었습니다. store-backed aggregate에서 `_build_recurrence_aggregate_reviewed_memory_capability_source_refs()`가 `source_status = all_required_sources_present`로 반환됩니다. 이유는 all five refs (`boundary_source_ref`, `rollback_source_ref`, `disable_source_ref`, `conflict_source_ref`, `transition_audit_source_ref`)가 모두 non-None이기 때문입니다.
- `reviewed_memory_capability_basis`는 계속 absent이고, `reviewed_memory_capability_status.capability_outcome`는 계속 `blocked_all_required`입니다. full source family completion != basis object, basis object != status widening입니다.
- `rollback_source_ref`는 그대로 exact handle backer를, `disable_source_ref`는 그대로 exact disable contract backer를, `conflict_source_ref`는 그대로 exact conflict contract backer를 유지합니다.
- payload-visible `transition_audit_source_ref`, `reviewed_memory_capability_source_refs`, `reviewed_memory_transition_record`, enabled submit flow, note input은 모두 추가하지 않았습니다. aggregate card UI는 여전히 visible-but-disabled 상태입니다.

## 검증
- `python3 -m py_compile app/web.py storage/session_store.py core/agent_loop.py tests/test_smoke.py tests/test_web_app.py`
- `python3 -m unittest -v tests.test_smoke tests.test_web_app`
  - `Ran 176 tests in 2.341s`
  - `OK`
- `make e2e-test`
  - 첫 실행: 1 failed (타이밍 flaky, 제 변경과 무관)
  - 재실행: `12 passed (3.9m)`
- `git diff --check`
- `rg -n "conflict_source_ref|transition_audit_source_ref|reviewed_memory_capability_source_refs|reviewed_memory_capability_basis|unblocked_all_required|blocked_all_required|reviewed_memory_transition_record" app/web.py storage/session_store.py core/agent_loop.py tests/test_smoke.py tests/test_web_app.py docs/NEXT_STEPS.md docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md`

## 남은 리스크
- 이번 라운드에서 해소한 리스크:
  - exact same-aggregate shared target 위에 real transition-audit source가 없어서 `transition_audit_source_ref`가 항상 unresolved로 남던 문제를 해결했습니다.
  - internal `reviewed_memory_capability_source_refs` family가 항상 incomplete / absent이던 문제를 해결했습니다 (all five refs now complete).
- 이전 closeout에서 이어받은 리스크:
  - `transition_audit_source_ref`가 unresolved였습니다.
  - `reviewed_memory_capability_source_refs` 전체 family가 incomplete / absent였습니다.
  - 이번 라운드에서 둘 다 해소했습니다.
- 여전히 남은 리스크:
  - `reviewed_memory_capability_basis`는 아직 absent입니다.
  - `unblocked_all_required`, payload-visible transition record, apply result는 여전히 닫혀 있습니다.
  - `first_seen_at` alone, `candidate_review_record`, approval-backed save support, historical adjunct, `task_log` replay alone은 계속 local proof/fact/source/target/backer basis가 아닙니다.
  - e2e 테스트 첫 실행에서 1개 타이밍 관련 flaky failure가 발생했으나 재실행 시 통과했습니다.
- 다음 최소 slice는 summary reopen이 아니라 `reviewed_memory_capability_basis` materialization only가 더 정직합니다. 모든 source ref가 resolved되고 source family가 complete된 상태에서, basis object만 한 단계 더 열 수 있는 상태이기 때문입니다.
