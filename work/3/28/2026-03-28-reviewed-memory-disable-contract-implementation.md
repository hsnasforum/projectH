# 2026-03-28 reviewed-memory disable contract implementation

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
- `plandoc/2026-03-28-reviewed-memory-disable-contract.md`
- `work/3/28/2026-03-28-reviewed-memory-disable-contract-implementation.md`

## 사용 skill
- `mvp-scope`: same-session aggregate 위의 새 disable contract를 current MVP 범위 안의 additive read-only projection으로만 고정했습니다.
- `approval-flow-audit`: review acceptance, approval-backed save, historical adjunct가 disable contract basis나 target으로 승격되지 않도록 기존 경계를 다시 확인했습니다.
- `doc-sync`: 새 `reviewed_memory_disable_contract` 구현에 맞춰 root docs와 `plandoc`을 current truth로 동기화했습니다.
- `release-check`: 실제 실행한 `py_compile`, `unittest`, `make e2e-test`, `git diff --check`, `rg` 결과만 기준으로 closeout을 남깁니다.
- `work-log-closeout`: 저장소 규칙에 맞는 `/work` closeout 형식으로 이번 구현과 남은 리스크를 기록했습니다.

## 변경 이유
- 직전 closeout에서 `disable_ready_reviewed_memory_effect` exact contract는 문서로 닫혔지만, current payload에는 그 later stop-apply target boundary를 inspect할 read-only `reviewed_memory_disable_contract` object가 아직 없었습니다.
- 이 object가 없으면 current serialization에서 stop-apply target kind와 exact aggregate/supporting refs가 여전히 추상적으로만 남아 later reviewed-memory/apply 방향을 과장하기 쉬웠습니다.

## 핵심 변경
- `app/web.py`의 same-session aggregate builder에 `reviewed_memory_disable_contract` helper를 추가했습니다.
- contract object는 current aggregate item 아래 read-only sibling 필드로만 붙고, shape는 아래로 고정했습니다:
  - `disable_version = first_reviewed_memory_effect_stop_apply_v1`
  - `reviewed_scope = same_session_exact_recurrence_aggregate_only`
  - `aggregate_identity_ref`
  - `supporting_source_message_refs`
  - `supporting_candidate_refs`
  - optional `supporting_review_refs`
  - `disable_target_kind = future_applied_reviewed_memory_effect_only`
  - `disable_stage = contract_only_not_applied`
  - `effect_behavior = stop_apply_without_reversal`
  - `audit_trace_expectation = operator_visible_local_transition_required`
  - `defined_at = last_seen_at`
- contract basis는 current same-session exact aggregate, current boundary draft/rollback contract, exact current supporting refs만 사용했고, `candidate_review_record`는 optional support ref일 뿐 identity basis를 넓히지 않도록 유지했습니다.
- `aggregate_promotion_marker`, `reviewed_memory_precondition_status`, `reviewed_memory_boundary_draft`, `reviewed_memory_rollback_contract`, `recurrence_aggregate_candidates` identity rule, `candidate_recurrence_key`, `durable_candidate`, `candidate_review_record`, `review_queue_items` semantics는 유지했습니다.
- helper-level / payload-level regression을 보강했고, docs와 `plandoc`은 disable contract shipped 상태와 다음 conflict-contract 방향으로 동기화했습니다.

## 검증
- `python3 -m py_compile app/web.py storage/session_store.py core/agent_loop.py tests/test_smoke.py tests/test_web_app.py`
- `python3 -m unittest -v tests.test_smoke tests.test_web_app`
  - `169 tests` passed
- `make e2e-test`
  - `11 passed`
- `git diff --check`
- `rg -n "reviewed_memory_disable_contract|disable_target_kind|effect_behavior|stop_apply_without_reversal|reviewed_memory_rollback_contract|reviewed_memory_boundary_draft|same_session_exact_recurrence_aggregate_only" app/web.py storage/session_store.py core/agent_loop.py tests/test_smoke.py tests/test_web_app.py docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md plandoc/2026-03-28-reviewed-memory-disable-contract.md`

## 남은 리스크
- 이전 closeout에서 이어받은 리스크:
  - disable contract는 문서로 닫혔지만 current payload에는 그 later stop-apply target boundary를 inspect할 read-only object가 없었습니다.
- 이번 라운드에서 해소한 리스크:
  - current aggregate item마다 read-only `reviewed_memory_disable_contract`가 붙으면서 stop-apply target kind와 exact aggregate/supporting refs가 payload에 드러납니다.
  - `defined_at = last_seen_at`로 고정해 임의 mutable timestamp를 추가하지 않았습니다.
- 여전히 남은 리스크:
  - contract object는 stop-apply target contract only이고, reviewed-memory store/apply, disable state machine, conflict/operator-audit mechanics는 여전히 미구현입니다.
  - next precondition인 `conflict_visible_reviewed_memory_scope` exact contract가 아직 닫히지 않았습니다.
  - cross-session counting과 user-level memory는 계속 later layer입니다.
