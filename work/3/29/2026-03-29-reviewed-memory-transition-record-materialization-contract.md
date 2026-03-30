# 2026-03-29 reviewed-memory transition-record materialization contract

## 변경 파일
- `docs/PRODUCT_SPEC.md`
- `docs/ARCHITECTURE.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`
- `docs/NEXT_STEPS.md`
- `plandoc/2026-03-29-reviewed-memory-emitted-transition-record-contract.md`
- `plandoc/2026-03-29-reviewed-memory-transition-record-materialization-contract.md`
- `work/3/29/2026-03-29-reviewed-memory-transition-record-materialization-contract.md`

## 사용 skill
- `mvp-scope`
- `approval-flow-audit`
- `doc-sync`
- `release-check`
- `work-log-closeout`

## 변경 이유
- 직전 closeout에서 future emitted transition record의 shape는 이미 닫혔지만, 무엇이 first truthful emission trigger인지와 current payload absence를 언제까지 truthful current state로 유지해야 하는지가 아직 exact contract로 닫히지 않았습니다.
- 이 질문이 열려 있으면 later implementation이 contract existence나 `task_log` replay만으로 fake emitted record를 합성할 위험이 남아 있었습니다.

## 핵심 변경
- current shipped payload absence를 그대로 유지하면서, future emitted-record materialization rule을 별도 contract로 고정했습니다.
- current repo truth는 다음으로 고정했습니다:
  - current shipped payload still emits no `reviewed_memory_transition_record`
  - current absence means only that no emitted transition has happened yet
  - current absence does not mean missing audit contract, missing emitted-record shape, or opened apply result
- first truthful emission trigger는 one exact future action으로 고정했습니다:
  - first emitted action = `future_reviewed_memory_apply` only
  - materialization requires:
    - truthful `capability_outcome = unblocked_all_required`
    - one actual operator-visible `future_reviewed_memory_apply`
    - one real `canonical_transition_id`
    - one explicit `operator_reason_or_note`
    - one local `emitted_at`
- `future_reviewed_memory_stop_apply` / `future_reviewed_memory_reversal` / `future_reviewed_memory_conflict_visibility`는 first action에서 제외했고, `task_log` mirroring은 first implementation round에서 optional이라고 닫았습니다.

## 검증
- `git diff --check`
- `rg -n "reviewed_memory_transition_record|current shipped payload still emits no such object|transition_action_vocabulary|task_log_mirror_relation|canonical_transition_id|operator_reason_or_note|record_stage" docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md README.md plandoc/2026-03-29-reviewed-memory-transition-record-materialization-contract.md plandoc/2026-03-29-reviewed-memory-emitted-transition-record-contract.md`

## 남은 리스크
- 이전 closeout에서 이어받은 리스크:
  - emitted transition record의 shape는 정해졌지만, first truthful emission trigger와 current absence policy는 아직 exact contract가 없었습니다.
- 이번 라운드에서 해소한 리스크:
  - current absence가 why truthful 인지와 first emitted action이 무엇인지 문서로 고정했습니다.
  - `task_log` replay나 contract existence alone이 emitted record basis처럼 읽히는 경로를 막았습니다.
- 여전히 남은 리스크:
  - emitted transition record는 아직 미구현입니다.
  - later non-apply actions가 같은 record shape를 그대로 쓸지, action-specific extension이 필요한지는 아직 open question입니다.
  - reviewed-memory apply, repeated-signal promotion, cross-session counting, user-level memory는 계속 later layer입니다.
