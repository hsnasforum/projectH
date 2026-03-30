# 2026-03-29 reviewed-memory capability-status implementation

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
- `plandoc/2026-03-29-reviewed-memory-satisfaction-surface-contract.md`
- `work/3/29/2026-03-29-reviewed-memory-capability-status-implementation.md`

## 사용 skill
- `mvp-scope`
- `approval-flow-audit`
- `doc-sync`
- `release-check`
- `work-log-closeout`

## 변경 이유
- 직전 closeout에서 future satisfaction-surface contract는 문서로 닫혔지만, current payload에는 exact capability outcome을 inspect할 read-only `reviewed_memory_capability_status`가 아직 없다는 리스크를 이어받았습니다.
- 이 object가 없으면 later widening에서 blocked threshold, satisfied capability outcome, emitted transition record, apply result를 섞어 과장하기 쉬웠습니다.

## 핵심 변경
- current same-session `recurrence_aggregate_candidates` item 아래에 read-only `reviewed_memory_capability_status`를 additive sibling object로 materialize했습니다.
- current emitted shape는 아래로 고정했습니다:
  - `capability_version = same_session_reviewed_memory_capabilities_v1`
  - `readiness_target = eligible_for_reviewed_memory_draft`
  - exact `required_preconditions`
  - `capability_outcome = blocked_all_required`
  - `satisfaction_basis_boundary = canonical_reviewed_memory_layer_capabilities_only`
  - `partial_state_policy = partial_states_not_materialized`
  - `evaluated_at = aggregate.last_seen_at`
- current repo에는 satisfied later capability machinery가 아직 없으므로, `unblocked_all_required`는 vocabulary로만 남기고 current state로는 materialize하지 않도록 유지했습니다.
- `candidate_review_record`, approval-backed save, historical adjunct, `task_log` replay alone은 capability basis에 포함하지 않았고, existing contract chain 존재 자체도 satisfaction shortcut이 되지 않도록 유지했습니다.
- 테스트 기대값과 문서를 current shipped truth에 맞춰 동기화했고, next slice는 label-narrowing pass only로 다시 좁혔습니다.

## 검증
- `python3 -m py_compile app/web.py storage/session_store.py core/agent_loop.py tests/test_smoke.py tests/test_web_app.py`
- `python3 -m unittest -v tests.test_smoke tests.test_web_app`
- `make e2e-test`
- `git diff --check`
- `rg -n "reviewed_memory_capability_status|capability_outcome|blocked_all_required|unblocked_all_required|readiness_target|required_preconditions|reviewed_memory_unblock_contract|reviewed_memory_transition_audit_contract" app/web.py storage/session_store.py core/agent_loop.py tests/test_smoke.py tests/test_web_app.py docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md plandoc/2026-03-29-reviewed-memory-satisfaction-surface-contract.md`

## 남은 리스크
- 이전 closeout에서 이어받은 리스크:
  - future satisfaction surface contract는 문서로 닫혔지만, current payload에는 exact capability outcome을 inspect할 read-only `reviewed_memory_capability_status`가 없었습니다.
- 이번 라운드에서 해소한 리스크:
  - current aggregate item마다 read-only `reviewed_memory_capability_status`가 붙으면서 blocked threshold와 capability outcome surface가 payload에서 분리됩니다.
  - current emitted value를 `blocked_all_required`에 고정해 object existence가 `unblocked_all_required`처럼 읽히지 않도록 했습니다.
- 여전히 남은 리스크:
  - current repo에는 still satisfied later capability machinery가 없으므로 `unblocked_all_required`는 future vocabulary only입니다.
  - `readiness_target = eligible_for_reviewed_memory_draft`를 그대로 유지할지, 더 좁은 planning-only label로 바꿀지는 아직 open question입니다.
  - reviewed-memory store / apply / emitted transition record / repeated-signal promotion / cross-session counting / user-level memory는 계속 later layer입니다.
