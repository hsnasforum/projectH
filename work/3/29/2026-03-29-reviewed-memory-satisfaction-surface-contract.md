# 2026-03-29 reviewed-memory satisfaction-surface contract

## 변경 파일
- `docs/PRODUCT_SPEC.md`
- `docs/ARCHITECTURE.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`
- `docs/NEXT_STEPS.md`
- `plandoc/2026-03-29-reviewed-memory-satisfaction-surface-contract.md`
- `work/3/29/2026-03-29-reviewed-memory-satisfaction-surface-contract.md`

## 사용 skill
- `mvp-scope`
- `approval-flow-audit`
- `doc-sync`
- `release-check`
- `work-log-closeout`

## 변경 이유
- 직전 closeout에서 shipped `reviewed_memory_unblock_contract`는 blocked readiness threshold를 truthfully 드러내지만, future satisfied capability outcome을 어떤 최소 surface로 열어야 하는지는 아직 exact contract가 없다는 리스크를 이어받았습니다.
- 이 경계가 없으면 later widening이 `contract exists`, `blocked threshold`, satisfied capability outcome, emitted transition record, apply result를 한 번에 섞어 과장할 위험이 컸습니다.

## 핵심 변경
- future satisfaction surface는 `Option B`로 고정했습니다:
  - shipped `reviewed_memory_unblock_contract`는 blocked-threshold contract only로 유지
  - later widening이 reopen 되면 one separate read-only `reviewed_memory_capability_status`를 추가
- future `reviewed_memory_capability_status`의 최소 shape를 고정했습니다:
  - `capability_version = same_session_reviewed_memory_capabilities_v1`
  - `readiness_target = eligible_for_reviewed_memory_draft`
  - exact `required_preconditions`
  - `capability_outcome`
    - `blocked_all_required`
    - `unblocked_all_required`
  - `satisfaction_basis_boundary = canonical_reviewed_memory_layer_capabilities_only`
  - `partial_state_policy = partial_states_not_materialized`
  - `evaluated_at`
- `unblocked_all_required`는 one exact same-session aggregate가 all-required capability family를 실제로 만족해 reviewed-memory draft planning only가 truthfully 열릴 수 있다는 뜻으로만 고정했습니다.
- approval-backed save, historical adjunct, review acceptance, queue presence, `task_log` replay alone은 future satisfaction basis가 아니라는 점을 다시 명시했습니다.
- current source-message candidate / durable projection / review trace / recurrence key / same-session aggregate / blocked marker / precondition status / contract chain / unblock contract / future satisfaction surface / future emitted transition record / future apply 경계를 문서에 다시 좁게 고정했습니다.

## 검증
- `git diff --check`
- `rg -n "reviewed_memory_unblock_contract|unblocked_all_required|blocked_all_required|eligible_for_reviewed_memory_draft|eligible_for_reviewed_memory_draft_planning_only|reviewed_memory_transition_audit_contract|satisfaction surface|readiness_target" docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md README.md plandoc/2026-03-29-reviewed-memory-satisfaction-surface-contract.md`
- 미실행:
  - `python3 -m py_compile ...`
  - `python3 -m unittest ...`
  - `make e2e-test`

## 남은 리스크
- 이전 closeout에서 이어받은 리스크:
  - shipped `reviewed_memory_unblock_contract` 위에서 future satisfied capability outcome을 어떤 최소 surface로 열지 아직 exact contract가 없었습니다.
- 이번 라운드에서 해소한 리스크:
  - `contract exists` / shipped blocked threshold / future satisfied capability outcome을 3단으로 분리했고, later widening 시 separate satisfaction surface를 쓰도록 고정했습니다.
  - `unblocked_all_required`를 emitted transition record나 apply result가 아닌 draft-planning readiness only로 다시 좁혔습니다.
- 여전히 남은 리스크:
  - future `reviewed_memory_capability_status`는 아직 미구현입니다.
  - `readiness_target = eligible_for_reviewed_memory_draft`를 later satisfied surface에서도 그대로 유지할지, 더 좁은 planning-only label로 바꿀지는 아직 open question입니다.
  - reviewed-memory store / apply / emitted transition record / repeated-signal promotion / cross-session counting / user-level memory는 계속 later layer입니다.
