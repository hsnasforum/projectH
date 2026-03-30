# 2026-03-29 reviewed-memory local effect presence fact-source helper 구현

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
- `work/3/29/2026-03-29-reviewed-memory-local-effect-presence-fact-source-helper-implementation.md`

## 사용 skill
- `mvp-scope`: current shipped reviewed-memory helper chain을 current MVP 범위 안에서 좁게 유지하기 위해 사용
- `doc-sync`: helper 추가 이후 root docs와 `plandoc/` wording을 current implementation truth에 맞추기 위해 사용
- `release-check`: 실행한 검증만 정직하게 남기고 unchanged UI/basis/status 경계를 다시 확인하기 위해 사용
- `work-log-closeout`: `/work` closeout 형식을 현재 repo 규칙에 맞춰 남기기 위해 사용

## 변경 이유
- 직전 closeout에서는 exact future `reviewed_memory_local_effect_presence_fact_source` contract만 문서로 고정됐고, current repo에는 해당 internal helper 구현이 없었습니다.
- raw-event helper 아래의 fact-source helper가 없으면 다음 라운드에서 local proof 부재와 helper 부재가 다시 섞일 위험이 남았습니다.
- 이번 라운드는 one-helper internal scaffold만 추가하고 상위 helper chain, payload, UI, status를 그대로 멈춰 두는 것이 가장 작은 truthful slice였습니다.

## 핵심 변경
- `app/web.py`에 `_build_recurrence_aggregate_reviewed_memory_local_effect_presence_fact_source(...)`를 추가하고, same exact aggregate identity, supporting refs, optional review refs, resolved `boundary_source_ref`, deterministic `evaluated_at`까지만 검증한 뒤 current repo truth상 local proof가 없어서 `None`을 반환하도록 고정했습니다.
- raw-event helper, producer helper, event-source helper, source-consumer helper, target helper, reversible handle, `rollback_source_ref`, `reviewed_memory_capability_basis`, `reviewed_memory_transition_record`, blocked UI는 의도적으로 건드리지 않았습니다.
- `tests/test_smoke.py`, `tests/test_web_app.py`에 새 fact-source helper absent 회귀와 fake fact-source/support-only trace가 상위 helper chain을 열지 못하는 회귀를 추가했습니다.
- root docs와 `plandoc/`를 helper exists-but-absent current truth로 동기화했고, next slice wording을 `truthful same-aggregate local fact-source materialization only`로 갱신했습니다.
- 이전 closeout에서 이어받은 “exact fact-source contract는 있지만 helper 구현이 없다”는 리스크는 해소했습니다.

## 검증
- `python3 -m py_compile app/web.py storage/session_store.py core/agent_loop.py tests/test_smoke.py tests/test_web_app.py`
- `python3 -m unittest -v tests.test_smoke tests.test_web_app`
  - 결과: `Ran 169 tests in 2.105s`, `OK`
- `make e2e-test`
  - 결과: `12 passed`
- `git diff --check`
- `rg -n 'reviewed_memory_local_effect_presence_fact_source|reviewed_memory_local_effect_presence_event\\b|reviewed_memory_local_effect_presence_event_producer|reviewed_memory_local_effect_presence_event_source|reviewed_memory_local_effect_presence_record|reviewed_memory_applied_effect_target|reviewed_memory_reversible_effect_handle|rollback_source_ref|reviewed_memory_capability_basis|unblocked_all_required|blocked_all_required|reviewed_memory_transition_record' app/web.py storage/session_store.py core/agent_loop.py tests/test_smoke.py tests/test_web_app.py docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md plandoc/2026-03-29-reviewed-memory-local-effect-presence-fact-source-contract.md plandoc/2026-03-29-reviewed-memory-local-effect-presence-event-contract.md plandoc/2026-03-29-reviewed-memory-applied-effect-presence-source-contract.md plandoc/2026-03-29-reviewed-memory-applied-effect-target-contract.md plandoc/2026-03-29-reviewed-memory-rollback-backer-contract.md'`

## 남은 리스크
- current repo에는 여전히 truthful same-aggregate local fact-source instance가 없어서 새 helper도 계속 absence를 유지합니다.
- raw-event helper, producer helper, event-source helper, source-consumer helper, target helper, reversible handle, `rollback_source_ref`는 모두 여전히 absence 또는 unresolved입니다.
- `reviewed_memory_capability_basis`, `unblocked_all_required`, enabled trigger, emitted transition record, reviewed-memory apply result는 여전히 열리지 않았고, 이번 라운드에서도 열면 안 되는 상태를 유지했습니다.
- 다음 slice에서는 one truthful same-aggregate local fact-source materialization만 열어야 하며, raw-event helper consumption이나 상위 helper widening은 그 뒤로 남겨야 합니다.
