# 2026-03-30 reviewed-memory capability-basis materialization only

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

## 사용 skill
- 없음

## 변경 이유
- 최신 `/work`인 `2026-03-30-reviewed-memory-transition-audit-source-ref-materialization-only.md`와 최신 `/verify`인 `2026-03-30-e2e-568-recurrence-aggregate-verification.md`를 읽고 이어받았습니다.
- 이전 라운드까지 internal `reviewed_memory_capability_source_refs` family가 all five refs complete (`source_status = all_required_sources_present`)로 materialize되었으나 `reviewed_memory_capability_basis`는 계속 absent이었습니다.
- 이번 슬라이스의 목표는 complete된 source family 위에 one truthful `reviewed_memory_capability_basis` object만 materialize하는 것이었습니다.

## 핵심 변경
- `app/web.py`에서 `_build_recurrence_aggregate_reviewed_memory_capability_basis(...)` 메서드가 이전에는 source refs complete 확인 후에도 항상 `return None`을 반환했습니다. 이번 라운드에서 truthful basis object를 생성하도록 변경했습니다.
- basis object 구조:
  - `basis_version = same_session_reviewed_memory_capability_basis_v1`
  - `reviewed_scope = same_session_exact_recurrence_aggregate_only`
  - `aggregate_identity_ref` (exact aggregate key)
  - `supporting_source_message_refs`, `supporting_candidate_refs`
  - optional `supporting_review_refs` (review 지원이 있을 때만)
  - `required_preconditions` (unblock_contract에서 가져온 precondition 목록)
  - `basis_status = all_required_capabilities_present`
  - `satisfaction_basis_boundary = canonical_reviewed_memory_layer_capabilities_only`
  - deterministic `evaluated_at = last_seen_at`
- basis는 complete된 capability source refs가 있고, unblock_contract이 일치하고, aggregate_key / supporting refs / last_seen_at가 모두 유효할 때만 materialize됩니다.
- `_build_recurrence_aggregate_reviewed_memory_capability_status(...)` 메서드는 기존에 basis present → `unblocked_all_required`로 widening하는 로직이 있었으나, 이번 라운드에서는 basis가 present 해도 `capability_outcome = blocked_all_required`를 유지하도록 변경했습니다. status widening은 후속 라운드로 명시적으로 미룹니다.
- payload-visible `reviewed_memory_capability_basis` object가 이제 aggregate card에 노출됩니다.
- `reviewed_memory_capability_status.capability_outcome`은 계속 `blocked_all_required`입니다.
- aggregate card `검토 메모 적용 시작`은 계속 visible-but-disabled입니다.
- `reviewed_memory_transition_record`는 계속 absent입니다.
- enabled submit flow, `unblocked_all_required`, emitted record는 열지 않았습니다.

## 검증
- `python3 -m py_compile app/web.py storage/session_store.py core/agent_loop.py tests/test_smoke.py tests/test_web_app.py` — 통과
- `python3 -m unittest -v tests.test_smoke tests.test_web_app` — 176 tests OK
- `make e2e-test` — 12 passed (3.6m)
- `git diff --check` — 통과

## 남은 리스크
- `reviewed_memory_capability_basis`는 이제 materialized이고, `reviewed_memory_capability_status.capability_outcome`는 여전히 `blocked_all_required`입니다.
- `unblocked_all_required`는 후속 라운드에서 별도로 열어야 합니다.
- `reviewed_memory_transition_record`는 여전히 absent입니다.
- enabled submit flow, emitted record, apply result는 여전히 닫혀 있습니다.
- dirty worktree가 여전히 매우 넓습니다.
