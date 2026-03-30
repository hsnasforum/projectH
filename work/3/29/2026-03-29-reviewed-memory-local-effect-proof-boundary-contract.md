# 2026-03-29 reviewed-memory local effect proof-boundary contract

## 변경 파일
- `docs/PRODUCT_SPEC.md`
- `docs/ARCHITECTURE.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`
- `docs/NEXT_STEPS.md`
- `plandoc/2026-03-29-reviewed-memory-local-effect-proof-boundary-contract.md`
- `plandoc/2026-03-29-reviewed-memory-local-effect-presence-fact-source-contract.md`
- `plandoc/2026-03-29-reviewed-memory-local-effect-presence-event-contract.md`
- `plandoc/2026-03-29-reviewed-memory-applied-effect-presence-source-contract.md`
- `plandoc/2026-03-29-reviewed-memory-applied-effect-target-contract.md`
- `plandoc/2026-03-29-reviewed-memory-rollback-backer-contract.md`
- `plandoc/2026-03-29-reviewed-memory-capability-basis-source-contract.md`
- `plandoc/2026-03-29-reviewed-memory-unblocked-capability-path-contract.md`
- `work/3/29/2026-03-29-reviewed-memory-local-effect-proof-boundary-contract.md`

## 사용 skill
- `mvp-scope`: current shipped contract, next design target, long-term north star를 섞지 않고 exact proof-boundary layer만 문서로 고정했습니다.
- `doc-sync`: current helper-chain truth와 next-slice wording을 root docs와 `plandoc/`에 맞췄습니다.
- `release-check`: 문서-only round 기준으로 실제 실행한 `git diff --check`와 `rg` 검증만 정직하게 남기도록 정리했습니다.
- `work-log-closeout`: 이번 설계 정리 라운드의 변경, 검증, 잔여 리스크를 `/work` closeout 형식으로 기록했습니다.

## 변경 이유
- 직전 closeout에서 이어받은 핵심 리스크는 internal `reviewed_memory_local_effect_presence_fact_source_instance` helper는 이미 코드에 있지만, 그 helper가 truthfully materialize할 exact later local proof boundary가 아직 없다는 점이었습니다.
- current repo는 still no real local proof boundary를 가지므로, 바로 materialization 구현을 밀기보다 first `applied_effect_id`와 first `present_locally_at`를 어디서 mint할지 문서로 먼저 닫는 것이 더 정직했습니다.
- 이 layer를 분리하지 않으면 current fact-source-instance helper, fact-source helper, raw-event helper, producer helper, event-source helper, source-consumer helper, target helper, handle helper의 absence 경계가 계속 모호해질 위험이 있었습니다.

## 핵심 변경
- 새 설계 문서 `plandoc/2026-03-29-reviewed-memory-local-effect-proof-boundary-contract.md`를 추가했습니다.
- exact future lower layer를 one shared internal `reviewed_memory_local_effect_presence_proof_boundary`로 고정했습니다.
  - `proof_boundary_version = first_same_session_reviewed_memory_local_effect_presence_proof_boundary_v1`
  - `proof_boundary_scope = same_session_exact_recurrence_aggregate_only`
  - exact aggregate identity + exact supporting refs + matching `boundary_source_ref`
  - `effect_target_kind = applied_reviewed_memory_effect`
  - `proof_capability_boundary = local_effect_presence_only`
  - `proof_stage = first_presence_proved_local_only`
  - first local `applied_effect_id`
  - same-instant `present_locally_at`
- current shipped helper chain도 다시 분리해 적었습니다.
  - current `reviewed_memory_local_effect_presence_fact_source_instance` helper exists but absent
  - current `reviewed_memory_local_effect_presence_fact_source` helper exists but absent
  - current `reviewed_memory_local_effect_presence_event` / producer / event-source / source-consumer / target helpers remain absent
  - current `reviewed_memory_reversible_effect_handle` and `rollback_source_ref` remain unresolved
  - current `reviewed_memory_capability_basis` remains absent
  - current `reviewed_memory_capability_status.capability_outcome` remains `blocked_all_required`
- root docs와 기존 `plandoc/`의 next-step wording도 `fact-source instance`가 아니라 `proof-boundary scaffold only` 기준으로 다시 맞췄습니다.
- support / mirror boundary도 다시 못 박았습니다.
  - `candidate_review_record`
  - queue presence
  - approval-backed save alone
  - historical adjunct alone
  - `task_log` replay alone
  - contract object existence alone
  - above inputs are never the local proof boundary

## 검증
- 실행: `git diff --check`
- 실행: `rg -n "reviewed_memory_local_effect_presence_fact_source_instance|reviewed_memory_local_effect_presence_fact_source|reviewed_memory_local_effect_presence_event\\b|reviewed_memory_local_effect_presence_event_producer|reviewed_memory_local_effect_presence_event_source|reviewed_memory_local_effect_presence_record|reviewed_memory_applied_effect_target|reviewed_memory_reversible_effect_handle|rollback_source_ref|reviewed_memory_capability_basis|unblocked_all_required|blocked_all_required|reviewed_memory_transition_record" docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md app/web.py app/templates/index.html plandoc/2026-03-29-reviewed-memory-local-effect-proof-boundary-contract.md plandoc/2026-03-29-reviewed-memory-local-effect-presence-fact-source-contract.md plandoc/2026-03-29-reviewed-memory-local-effect-presence-event-contract.md plandoc/2026-03-29-reviewed-memory-applied-effect-target-contract.md plandoc/2026-03-29-reviewed-memory-rollback-backer-contract.md"`
- 미실행:
  - `python3 -m py_compile ...`
  - `python3 -m unittest ...`
  - `make e2e-test`
  - 이유: 이번 라운드는 제품 코드 변경 없는 문서 계약 작업이었기 때문입니다.

## 남은 리스크
- 이전 closeout에서 이어받은 리스크였던 “fact-source-instance helper 아래의 exact later local proof boundary 부재”는 문서 계약 기준으로는 해소했습니다.
- 이번 라운드에서 해소한 것은 first `applied_effect_id`와 first `present_locally_at`를 mint할 lower boundary naming, scope, relation, and next-slice ordering을 current helper chain 아래에 분명히 고정한 점입니다.
- 여전히 남은 리스크는 current repo에 그 proof boundary를 담을 actual internal scaffold나 materialization이 아직 없다는 점입니다.
- 따라서 current `reviewed_memory_local_effect_presence_fact_source_instance` helper, `reviewed_memory_local_effect_presence_fact_source` helper, `reviewed_memory_local_effect_presence_event` helper, producer helper, event-source helper, source-consumer helper, target helper, handle helper, `rollback_source_ref`, `reviewed_memory_capability_basis`, `reviewed_memory_transition_record`는 모두 그대로 absence 또는 unresolved입니다.
- 다음 slice는 one internal same-aggregate local proof-boundary scaffold only가 가장 작습니다. fact-source-instance helper materialization, raw-event helper materialization, basis object emission, `unblocked_all_required`, enabled trigger, emitted transition record보다 먼저 이 lower proof boundary를 internal-only로 여는 것이 current repo 상태에서 가장 정직합니다.
