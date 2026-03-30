## 변경 파일
- `app/web.py`
- `tests/test_smoke.py`
- `tests/test_web_app.py`
- `docs/NEXT_STEPS.md`
- `docs/PRODUCT_SPEC.md`
- `docs/ARCHITECTURE.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`
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
- 최신 reviewed-memory closeout인 `work/3/30/2026-03-30-reviewed-memory-local-effect-event-source-materialization-only.md`와 최신 summary implementation closeout인 `work/3/30/2026-03-30-summary-chunks-selection-split.md`를 둘 다 다시 읽고 이어받았습니다.
- summary 쪽 truthful split은 이미 shipped 상태로 닫혀 있고, reviewed-memory chain의 다음 최소 truthful 슬라이스는 event-source 바로 위의 same-aggregate local source-consumer record뿐이었습니다.
- 직전 라운드까지 proof-record/store -> proof-boundary -> fact-source-instance -> fact-source -> event -> event-producer -> event-source는 exact same-aggregate lower result만 재사용해 truthfully materialize됐지만, `reviewed_memory_local_effect_presence_record`는 아직 의도적으로 `None`이어서 다음 target slice로 못 넘어가고 있었습니다.

## 핵심 변경
- `app/web.py`
  - `_build_recurrence_aggregate_reviewed_memory_local_effect_presence_record(...)`를 열었습니다.
  - 이 helper는 오직 exact same-aggregate `reviewed_memory_local_effect_presence_event_source` 결과가 있을 때만 internal-only record를 materialize합니다.
  - 새 record는 `aggregate_identity_ref`, `supporting_source_message_refs`, `supporting_candidate_refs`, optional `supporting_review_refs`, `boundary_source_ref`, `applied_effect_id`, `present_locally_at`를 그대로 재검증 후 재사용합니다.
  - emitted shape는 `source_version = first_same_session_reviewed_memory_local_effect_presence_record_v1`, `source_scope = same_session_exact_recurrence_aggregate_only`, `source_capability_boundary = local_effect_presence_only`, `source_stage = presence_recorded_local_only`로 고정했습니다.
- unchanged by design
  - `reviewed_memory_applied_effect_target`는 계속 absent입니다.
  - `reviewed_memory_reversible_effect_handle`는 계속 unresolved입니다.
  - `rollback_source_ref`는 exact-scope-validated but unresolved 상태를 유지합니다.
  - `reviewed_memory_capability_basis`는 계속 absent입니다.
  - `reviewed_memory_capability_status.capability_outcome`는 계속 `blocked_all_required`입니다.
  - aggregate card, disabled `검토 메모 적용 시작`, emitted transition record absence, summary truthful split work는 그대로 유지했습니다.
- 회귀
  - store-backed exact aggregate에서 event-source 위로 record만 materialize되고, target/handle/rollback/basis/status/UI는 그대로라는 회귀를 `tests/test_smoke.py`와 `tests/test_web_app.py`에 반영했습니다.
  - fake source, support-only trace, mismatched aggregate context로는 record가 생기지 않는 기존 방어 경계는 유지했습니다.
- 문서 동기화
  - root docs와 plandoc에서 current shipped truth를 `record still absent`에서 `record materialized, target still absent`로 맞췄습니다.
  - 다음 최소 슬라이스를 summary reopen이 아니라 `reviewed_memory_applied_effect_target only`로 갱신했습니다.

## 검증
- 추가 점검
  - `rg -n "reviewed_memory_local_effect_presence_event_source|reviewed_memory_local_effect_presence_record|reviewed_memory_applied_effect_target|reviewed_memory_reversible_effect_handle|rollback_source_ref|reviewed_memory_capability_basis|unblocked_all_required|blocked_all_required|reviewed_memory_transition_record" app/web.py storage/session_store.py core/agent_loop.py tests/test_smoke.py tests/test_web_app.py docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md plandoc/2026-03-29-reviewed-memory-applied-effect-target-contract.md plandoc/2026-03-29-reviewed-memory-rollback-backer-contract.md`
- 문법 확인
  - `python3 -m py_compile app/web.py tests/test_smoke.py tests/test_web_app.py`
  - `python3 -m py_compile app/web.py storage/session_store.py core/agent_loop.py tests/test_smoke.py tests/test_web_app.py`
- 서비스 회귀
  - `python3 -m unittest -v tests.test_smoke tests.test_web_app`
  - 결과: `Ran 176 tests in 2.073s`, `OK`
- 브라우저 smoke
  - `make e2e-test`
  - 결과: `12 passed (3.3m)`
- diff hygiene
  - `git diff --check`

## 남은 리스크
- current same-aggregate local source-consumer record는 internal-only로만 materialize됩니다. payload-visible record는 여전히 없습니다.
- `reviewed_memory_applied_effect_target`, `reviewed_memory_reversible_effect_handle`, `rollback_source_ref`, `reviewed_memory_capability_basis`, `unblocked_all_required`, `reviewed_memory_transition_record`는 모두 여전히 닫혀 있습니다.
- `first_seen_at` alone, `candidate_review_record`, review queue presence, approval-backed save support, historical adjunct, `task_log` replay alone은 여전히 local proof/fact/source/target/backer basis가 아닙니다.
- summary는 short/per-chunk/reduce/summary_chunks selection까지 이미 shipped truth로 닫혀 있으므로 current next slice는 summary reopen이 아니라 reviewed-memory `applied_effect_target only`가 맞습니다.
