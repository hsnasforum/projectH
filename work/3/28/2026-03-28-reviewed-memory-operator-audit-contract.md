# 2026-03-28 reviewed-memory operator-audit contract

## 변경 파일
- `docs/PRODUCT_SPEC.md`
- `docs/ARCHITECTURE.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`
- `docs/NEXT_STEPS.md`
- `plandoc/2026-03-28-reviewed-memory-operator-audit-contract.md`
- `work/3/28/2026-03-28-reviewed-memory-operator-audit-contract.md`

## 사용 skill
- `mvp-scope`: same-session aggregate 위의 future operator-auditable layer를 current shipped boundary/rollback/disable/conflict surface와 섞지 않도록 범위를 다시 좁혔습니다.
- `approval-flow-audit`: review acceptance, approval-backed save, historical adjunct, `task_log`가 canonical transition record나 transition basis처럼 읽히지 않도록 approval/review/audit 경계를 다시 확인했습니다.
- `doc-sync`: operator-audit contract 결정이 root docs와 `plandoc`에 같은 current-truth 문구로 남도록 동기화했습니다.
- `release-check`: 실제 실행한 `git diff --check`와 `rg` 결과만 기준으로 handoff 상태를 정리합니다.
- `work-log-closeout`: 저장소 규칙에 맞는 `/work` closeout 형식으로 이번 문서 라운드와 남은 리스크를 남깁니다.

## 변경 이유
- 직전 closeout에서 `reviewed_memory_conflict_contract`까지는 shipped 되었지만, 어떤 later reviewed-memory transition이 canonical operator-visible trace를 남겨야 하는지는 아직 문서로 닫히지 않았습니다.
- 이 경계가 없으면 later reviewed-memory apply, stop-apply, rollback reversal, conflict visibility 이후 어떤 local transition record가 canonical인지 계속 모호하게 남습니다.

## 핵심 변경
- `operator_auditable_reviewed_memory_transition`를 one later reviewed-memory transition마다 canonical local transition identity와 explicit operator-visible trace가 필요하다는 계약으로 고정했습니다.
- first operator-audit scope는 `same_session_exact_recurrence_aggregate_only`로 고정했고, first transition action vocabulary는 `future_reviewed_memory_apply`, `future_reviewed_memory_stop_apply`, `future_reviewed_memory_reversal`, `future_reviewed_memory_conflict_visibility` 네 개만 허용하도록 문서화했습니다.
- current `reviewed_memory_boundary_draft`, `reviewed_memory_rollback_contract`, `reviewed_memory_disable_contract`, `reviewed_memory_conflict_contract`는 basis ref 또는 neighboring contract로 남고 transition result 자체는 아니라고 다시 못 박았습니다.
- current append-only `task_log`는 audit mirror일 뿐 canonical reviewed-memory transition source가 아니라고 고정했고, future shape에도 `audit_store_boundary = canonical_transition_record_separate_from_task_log`를 넣어 그 분리를 명시했습니다.
- approval-backed save support, historical adjuncts, review acceptance, queue presence, and task-log replay alone는 canonical transition state를 만들지 못한다고 root docs와 `plandoc`에 맞춰 다시 동기화했습니다.
- next implementation slice는 one read-only `reviewed_memory_transition_audit_contract` only로 추천했습니다.

## 검증
- 실행: `git diff --check`
- 실행: `rg -n "operator_auditable_reviewed_memory_transition|reviewed_memory_conflict_contract|reviewed_memory_disable_contract|reviewed_memory_rollback_contract|reviewed_memory_boundary_draft|reviewed_memory_precondition_status|aggregate_promotion_marker|same_session_exact_recurrence_aggregate_only|task_log|cross-session" docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md README.md plandoc/2026-03-28-reviewed-memory-operator-audit-contract.md`
- 미실행: `python3 -m py_compile ...`
- 미실행: `python3 -m unittest ...`
- 미실행: `make e2e-test`

## 남은 리스크
- 이전 closeout에서 이어받은 리스크:
  - boundary/rollback/disable/conflict contract는 생겼지만 reviewed-memory layer 위에서 어떤 transition이 canonical operator-visible trace를 남겨야 하는지는 아직 exact contract가 없었습니다.
- 이번 라운드에서 해소한 리스크:
  - first operator-audit scope와 first transition action vocabulary를 fixed narrow contract로 문서화했습니다.
  - `task_log`가 canonical transition store가 아니라는 점과 current shipped contracts가 transition result가 아니라는 점을 분리했습니다.
- 여전히 남은 리스크:
  - `reviewed_memory_transition_audit_contract`를 실제 payload에 어떤 최소 shape로 materialize할지 구현은 아직 남아 있습니다.
  - reviewed-memory store/apply, repeated-signal promotion, cross-session counting, user-level memory는 계속 later layer입니다.
