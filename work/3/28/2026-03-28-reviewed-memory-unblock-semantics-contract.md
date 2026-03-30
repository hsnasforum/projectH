# 2026-03-28 reviewed-memory unblock semantics contract

## 변경 파일
- `docs/PRODUCT_SPEC.md`
- `docs/ARCHITECTURE.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`
- `docs/NEXT_STEPS.md`
- `plandoc/2026-03-28-reviewed-memory-unblock-semantics-contract.md`
- `work/3/28/2026-03-28-reviewed-memory-unblock-semantics-contract.md`

## 사용 skill
- `mvp-scope`: same-session aggregate가 blocked-only surface를 언제 벗어날 수 있는지 current MVP 범위 안에서 binary all-required semantics로 좁혔습니다.
- `approval-flow-audit`: approval-backed save, historical adjunct, review acceptance, `task_log` mirror가 unblock satisfaction basis처럼 읽히지 않도록 기존 경계를 다시 확인했습니다.
- `doc-sync`: same-session unblock semantics 계약을 root docs와 `plandoc`에 current-truth 문구로 동기화했습니다.
- `release-check`: 실제 실행한 `git diff --check`와 `rg` 결과만 기준으로 handoff를 남깁니다.
- `work-log-closeout`: 저장소 규칙에 맞는 `/work` closeout 형식으로 이번 문서 라운드와 남은 리스크를 기록했습니다.

## 변경 이유
- 직전 closeout에서 boundary/rollback/disable/conflict/transition-audit contract는 모두 shipped 되었지만, 그 read-only contract surface가 언제 실제 same-session unblock readiness로 넘어갈 수 있는지는 아직 exact semantics가 없었습니다.
- 이 경계가 없으면 current blocked-only contract를 너무 빨리 readiness나 eligibility로 오해하게 되고, later reviewed-memory apply나 repeated-signal promotion을 과장해서 여는 위험이 컸습니다.

## 핵심 변경
- same-session unblock을 “one exact same-session aggregate가 all-required preconditions satisfied 상태로 reviewed-memory draft planning only readiness에 들어가는 것”으로 고정했습니다.
- current shipped `reviewed_memory_boundary_draft`, `reviewed_memory_rollback_contract`, `reviewed_memory_disable_contract`, `reviewed_memory_conflict_contract`, `reviewed_memory_transition_audit_contract`는 모두 `contract exists` only이고, object existence alone은 `satisfied`가 아니라는 점을 문서로 분리했습니다.
- first unblock threshold는 binary only로 고정했습니다:
  - current shipped state = `blocked_all_required`
  - first future widened state = `unblocked_all_required`
  - partial satisfaction은 later inspectable이 되더라도 current phase에서는 still blocked-only입니다.
- current `future_transition_target = eligible_for_reviewed_memory_draft`는 유지하되, 의미를 “reviewed-memory draft planning only”로 더 좁게 정의했습니다.
- next implementation slice는 current blocked-only status object를 덮어쓰지 않는 one read-only `reviewed_memory_unblock_contract` only로 추천했습니다.

## 검증
- `git diff --check`
- `rg -n "reviewed_memory_transition_audit_contract|operator_auditable_reviewed_memory_transition|reviewed_memory_precondition_status|blocked_all_required|eligible_for_reviewed_memory_draft|same_session_exact_recurrence_aggregate_only|task_log|cross-session" docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md README.md plandoc/2026-03-28-reviewed-memory-unblock-semantics-contract.md`
- 미실행:
  - `python3 -m py_compile ...`
  - `python3 -m unittest ...`
  - `make e2e-test`

## 남은 리스크
- 이전 closeout에서 이어받은 리스크:
  - precondition surface는 모두 current payload에 보이지만, “contract exists”와 “actually satisfied”의 경계가 아직 없었습니다.
- 이번 라운드에서 해소한 리스크:
  - same-session unblock을 all-required binary threshold로 고정했고, current shipped contract objects가 satisfaction을 뜻하지 않는다는 점을 명시했습니다.
  - `eligible_for_reviewed_memory_draft`를 apply나 promotion이 아닌 planning-only target으로 다시 좁혔습니다.
- 여전히 남은 리스크:
  - current `reviewed_memory_precondition_status`는 여전히 blocked-only이고, future `reviewed_memory_unblock_contract`는 아직 미구현입니다.
  - reviewed-memory store/apply, emitted transition record, repeated-signal promotion, cross-session counting, user-level memory는 계속 later layer입니다.
