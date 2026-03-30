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
- `plandoc/2026-03-29-reviewed-memory-local-effect-presence-fact-source-contract.md`
- `plandoc/2026-03-29-reviewed-memory-local-effect-presence-event-contract.md`
- `plandoc/2026-03-29-reviewed-memory-applied-effect-presence-source-contract.md`
- `plandoc/2026-03-29-reviewed-memory-applied-effect-target-contract.md`
- `plandoc/2026-03-29-reviewed-memory-rollback-backer-contract.md`
- `plandoc/2026-03-29-reviewed-memory-capability-basis-source-contract.md`
- `plandoc/2026-03-29-reviewed-memory-unblocked-capability-path-contract.md`

## 사용 skill
- `mvp-scope`
- `doc-sync`
- `release-check`
- `work-log-closeout`

## 변경 이유
- 직전 closeout에서 이어받은 리스크는 internal `reviewed_memory_local_effect_presence_fact_source` helper는 이미 있지만, 그 helper가 truthfully consume할 real same-aggregate local fact-source instance는 아직 없다는 점이었습니다.
- 이번 라운드에서는 fake local proof를 만들지 않고, 그 부재를 더 아래의 internal materialization boundary로 내려서 current absence truth를 코드와 문서에 같이 고정할 필요가 있었습니다.

## 핵심 변경
- `app/web.py`에 internal `_build_recurrence_aggregate_reviewed_memory_local_effect_presence_fact_source_instance(...)` helper를 추가했습니다.
- 새 helper는 same exact aggregate identity, supporting refs, optional supporting review refs, current resolved `boundary_source_ref`, deterministic `evaluated_at`까지만 확인하고, current repo에 truthful local fact-source instance가 없으므로 그대로 `None`을 반환합니다.
- 기존 `reviewed_memory_local_effect_presence_fact_source` helper는 이제 이 new instance helper를 probe하도록 정리했습니다. current repo truth상 instance가 없어서 helper 역시 계속 absent입니다.
- raw-event helper, producer helper, event-source helper, source-consumer helper, target helper, reversible handle, `rollback_source_ref`, `reviewed_memory_capability_basis`, `reviewed_memory_transition_record`, blocked UI affordance는 모두 그대로 유지했습니다.
- `tests/test_smoke.py`, `tests/test_web_app.py`에 new instance helper absent 회귀, boundary draft missing 회귀, support-only trace 무시 회귀, fake fact-source-instance input 무시 회귀를 추가했습니다.
- root docs와 `plandoc/`은 “fact-source helper exists but absent”에서 한 단계 더 내려가 “fact-source-instance helper exists but absent, fact-source helper now probes it and still stays absent”로 동기화했습니다.
- 이전 closeout에서 남아 있던 “fact-source helper 아래 real proof boundary 부재” 리스크는 이번 라운드에서 code-level materialization boundary 추가로 해소했습니다.

## 검증
- 실행: `python3 -m py_compile app/web.py storage/session_store.py core/agent_loop.py tests/test_smoke.py tests/test_web_app.py`
- 실행: `python3 -m unittest -v tests.test_smoke tests.test_web_app`
  - 결과: `Ran 169 tests`, `OK`
- 실행: `make e2e-test`
  - 결과: `12 passed`
- 실행: `git diff --check`
- 실행: `rg -n 'reviewed_memory_local_effect_presence_fact_source|reviewed_memory_local_effect_presence_event\\b|reviewed_memory_local_effect_presence_event_producer|reviewed_memory_local_effect_presence_event_source|reviewed_memory_local_effect_presence_record|reviewed_memory_applied_effect_target|reviewed_memory_reversible_effect_handle|rollback_source_ref|reviewed_memory_capability_basis|unblocked_all_required|blocked_all_required|reviewed_memory_transition_record' app/web.py storage/session_store.py core/agent_loop.py tests/test_smoke.py tests/test_web_app.py docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md plandoc/2026-03-29-reviewed-memory-local-effect-presence-fact-source-contract.md plandoc/2026-03-29-reviewed-memory-local-effect-presence-event-contract.md plandoc/2026-03-29-reviewed-memory-applied-effect-presence-source-contract.md plandoc/2026-03-29-reviewed-memory-applied-effect-target-contract.md plandoc/2026-03-29-reviewed-memory-rollback-backer-contract.md`

## 남은 리스크
- 여전히 real same-aggregate local fact-source instance 자체는 없습니다. 따라서 `reviewed_memory_local_effect_presence_fact_source`와 그 위 helper chain은 모두 truthfully absent/unresolved입니다.
- `candidate_review_record`, approval-backed save support, historical adjunct, queue presence, `task_log` replay alone은 계속 local fact/source/target/backer basis가 아니므로, real local proof boundary를 어디에 둘지 다음 라운드에서 더 좁게 정해야 합니다.
- 다음 리스크는 first truthful same-aggregate local fact-source instance를 정확히 어떤 local proof에서 mint할지, 그리고 그 시점의 `applied_effect_id` / `present_locally_at`를 어디서 canonical하게 만들지입니다.
