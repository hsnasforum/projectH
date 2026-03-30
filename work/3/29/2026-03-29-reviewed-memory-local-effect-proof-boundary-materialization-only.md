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
- `plandoc/2026-03-29-reviewed-memory-local-effect-proof-boundary-contract.md`
- `plandoc/2026-03-29-reviewed-memory-local-effect-presence-fact-source-contract.md`
- `plandoc/2026-03-29-reviewed-memory-local-effect-presence-event-contract.md`
- `plandoc/2026-03-29-reviewed-memory-applied-effect-target-contract.md`
- `plandoc/2026-03-29-reviewed-memory-rollback-backer-contract.md`
- `plandoc/2026-03-29-reviewed-memory-capability-basis-source-contract.md`
- `plandoc/2026-03-29-reviewed-memory-unblocked-capability-path-contract.md`

## 사용 skill
- `doc-sync`
- `release-check`
- `work-log-closeout`

## 변경 이유
- 직전 라운드에서 same-session internal `reviewed_memory_local_effect_presence_proof_record_store` writer와 `reviewed_memory_local_effect_presence_proof_record` helper가 이미 truthfully 열렸지만, 그 위의 `reviewed_memory_local_effect_presence_proof_boundary` helper는 여전히 exact same-aggregate result를 만들지 못하고 있었습니다.
- 이번 라운드는 그 다음 최소 단계로서 proof-boundary helper 하나만 열고, fact-source-instance 이하 체인과 capability/basis/transition/UI semantics는 그대로 묶어 두어야 했습니다.
- 이전 closeout에서 이어받은 리스크는 "writer truth는 생겼지만 proof-boundary가 아직 absent라 이후 체인이 모두 닫혀 있다"는 점과 "일부 root docs에 stale writer wording이 남아 있을 수 있다"는 점이었습니다.

## 핵심 변경
- `app/web.py`
  - `_build_recurrence_aggregate_reviewed_memory_local_effect_presence_proof_boundary(...)`가 이제 existing exact same-aggregate canonical proof-record helper result를 바로 상위에서 consume합니다.
  - proof-boundary는 `same_session_exact_recurrence_aggregate_only` scope, exact aggregate identity, exact supporting refs, resolved `boundary_source_ref`, necessary-only `first_seen_at`, existing `applied_effect_id`, existing `present_locally_at`가 모두 현재 aggregate와 다시 맞을 때만 internal-only result를 materialize합니다.
  - helper result shape는 `proof_boundary_version`, `proof_boundary_scope`, `aggregate_identity_ref`, `supporting_source_message_refs`, `supporting_candidate_refs`, optional `supporting_review_refs`, `boundary_source_ref`, `effect_target_kind`, `proof_capability_boundary`, `proof_stage`, `applied_effect_id`, `present_locally_at`만 포함합니다.
  - `_build_recurrence_aggregate_reviewed_memory_local_effect_presence_fact_source_instance(...)`는 새 proof-boundary helper를 probe하지만, 이번 라운드에서는 explicit absence를 그대로 유지하도록 두었습니다.
- 테스트
  - proof-record store entry가 없으면 proof-boundary helper가 계속 absent인지 유지 검증을 남겼습니다.
  - exact same-aggregate proof-record/store entry가 있을 때만 proof-boundary helper가 열리고, fact-source-instance 이하 체인과 `rollback_source_ref`, `reviewed_memory_capability_basis`, `reviewed_memory_transition_record`, `capability_outcome = blocked_all_required`가 그대로 유지되는 focused regression을 추가했습니다.
  - payload serialization에서는 proof-record/proof-boundary/fact-source-instance 이하 객체가 여전히 payload-visible 하지 않음을 다시 고정했습니다.
- 문서
  - touched root docs와 `plandoc/`를 current truth에 맞춰 갱신했습니다.
  - stale한 "no shipped proof-record writer" 문맥은 이번에 touch한 문서 범위에서는 정리했습니다.
  - next truthful slice를 proof-boundary가 아니라 fact-source-instance materialization only로 이동했습니다.

## 검증
- 실행함: `python3 -m py_compile app/web.py storage/session_store.py core/agent_loop.py tests/test_smoke.py tests/test_web_app.py`
- 실행함: `python3 -m unittest -v tests.test_smoke tests.test_web_app`
- 실행함: `make e2e-test`
- 실행함: `git diff --check`
- 실행함: `rg -n "reviewed_memory_local_effect_presence_proof_record_store|reviewed_memory_local_effect_presence_proof_record|reviewed_memory_local_effect_presence_proof_boundary|reviewed_memory_local_effect_presence_fact_source_instance|reviewed_memory_local_effect_presence_fact_source|reviewed_memory_local_effect_presence_event\\b|reviewed_memory_local_effect_presence_event_producer|reviewed_memory_local_effect_presence_event_source|reviewed_memory_local_effect_presence_record|reviewed_memory_applied_effect_target|reviewed_memory_reversible_effect_handle|rollback_source_ref|reviewed_memory_capability_basis|unblocked_all_required|blocked_all_required|reviewed_memory_transition_record" app/web.py storage/session_store.py core/agent_loop.py tests/test_smoke.py tests/test_web_app.py docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md plandoc/2026-03-29-reviewed-memory-local-effect-proof-record-contract.md plandoc/2026-03-29-reviewed-memory-local-effect-proof-boundary-contract.md plandoc/2026-03-29-reviewed-memory-local-effect-presence-fact-source-contract.md plandoc/2026-03-29-reviewed-memory-local-effect-presence-event-contract.md plandoc/2026-03-29-reviewed-memory-applied-effect-target-contract.md plandoc/2026-03-29-reviewed-memory-rollback-backer-contract.md`

## 남은 리스크
- 이번 라운드에서 해소한 리스크는 "existing truthful proof-record/store entry가 있어도 proof-boundary helper가 항상 absent였다"는 점과 "touch한 문서에 stale writer wording이 남아 있을 수 있다"는 점입니다.
- 여전히 남은 리스크는 proof-boundary 위의 `reviewed_memory_local_effect_presence_fact_source_instance` 이하 전체 체인이 모두 absent라는 점입니다. 따라서 `reviewed_memory_capability_basis`, `rollback_source_ref`, `unblocked_all_required`, emitted transition record는 아직 열 수 없습니다.
- `first_seen_at` alone, `candidate_review_record`, approval-backed save support, historical adjunct, queue presence, `task_log` replay alone은 여전히 canonical local proof/fact/source/target/backer basis가 아닙니다. 이 선을 흐리면 current contract chain truthfulness가 깨집니다.
- root docs 전체와 historical `/work` note 전체를 전수 재작성한 것은 아니므로, 이번 라운드에서 touch하지 않은 오래된 기록에는 이전 wording이 남아 있을 수 있습니다.
