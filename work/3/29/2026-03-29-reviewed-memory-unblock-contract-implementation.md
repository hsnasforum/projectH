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
- `plandoc/2026-03-28-reviewed-memory-unblock-semantics-contract.md`

## 사용 skill
- `mvp-scope`
- `approval-flow-audit`
- `doc-sync`
- `release-check`
- `work-log-closeout`

## 변경 이유
- 직전 closeout에서 same-session unblock semantics는 문서로 닫혔지만, current payload에는 그 exact readiness threshold를 inspect할 `reviewed_memory_unblock_contract` object가 아직 없다는 리스크를 이어받았습니다.
- 이 상태에서는 current blocked-only surface와 future satisfied readiness의 경계가 여전히 추상적으로 남아, shipped contract object 존재 자체가 readiness처럼 오해될 위험이 있었습니다.

## 핵심 변경
- current same-session `recurrence_aggregate_candidates` item 아래에 read-only `reviewed_memory_unblock_contract`를 additive sibling object로 materialize했습니다.
- current emitted shape는 아래로 고정했습니다:
  - `unblock_version = same_session_reviewed_memory_unblock_v1`
  - `readiness_target = eligible_for_reviewed_memory_draft`
  - exact `required_preconditions`
  - `unblock_status = blocked_all_required`
  - `satisfaction_basis_boundary = canonical_reviewed_memory_layer_capabilities_only`
  - `partial_state_policy = partial_states_not_materialized`
  - `evaluated_at = aggregate.last_seen_at`
- current repo에는 satisfied later machinery가 아직 없으므로, `unblocked_all_required`는 vocabulary로만 남기고 current state로는 materialize하지 않도록 유지했습니다.
- `candidate_review_record`, approval-backed save, historical adjunct, `task_log` replay alone은 unblock basis에 포함하지 않았고, existing contract chain 존재 자체도 satisfaction shortcut이 되지 않도록 유지했습니다.
- 테스트 기대값과 문서를 current shipped truth에 맞춰 동기화했습니다.

## 검증
- `python3 -m py_compile app/web.py storage/session_store.py core/agent_loop.py tests/test_smoke.py tests/test_web_app.py`
- `python3 -m unittest -v tests.test_smoke tests.test_web_app`
- `make e2e-test`
- `git diff --check`
- `rg -n "reviewed_memory_unblock_contract|unblock_status|blocked_all_required|unblocked_all_required|readiness_target|required_preconditions|partial_state_policy|reviewed_memory_precondition_status|reviewed_memory_transition_audit_contract|same_session_exact_recurrence_aggregate_only" app/web.py storage/session_store.py core/agent_loop.py tests/test_smoke.py tests/test_web_app.py docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md plandoc/2026-03-28-reviewed-memory-unblock-semantics-contract.md`

## 남은 리스크
- 이전 closeout에서 이어받은 “blocked-only와 satisfied readiness의 경계가 payload에서 보이지 않는다”는 리스크는 이번 라운드에서 해소했습니다.
- 이번 라운드에서 해소한 범위는 readiness-threshold contract의 read-only materialization까지이며, actual satisfaction outcome이나 emitted transition record는 여전히 닫혀 있습니다.
- 여전히 남은 리스크:
  - `readiness_target = eligible_for_reviewed_memory_draft`라는 label이 long term에도 planning-only 의미를 충분히 드러내는지 아직 열려 있습니다.
  - current `reviewed_memory_unblock_contract`는 blocked contract only이며, satisfied vs unsatisfied를 truthfully 계산하는 later capability machinery는 여전히 없습니다.
