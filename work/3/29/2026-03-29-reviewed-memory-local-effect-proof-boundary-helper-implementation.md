# 2026-03-29 reviewed-memory local effect proof-boundary helper 구현

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
- `work/3/29/2026-03-29-reviewed-memory-local-effect-proof-boundary-helper-implementation.md`

## 사용 skill
- `mvp-scope`: current shipped blocked aggregate affordance와 next lower proof-boundary layer만 분리해서 좁게 구현하기 위해 사용했습니다.
- `doc-sync`: helper 추가 이후 root docs와 `plandoc/`의 current truth를 `proof-boundary helper exists but absent`로 맞추기 위해 사용했습니다.
- `release-check`: 실제 실행한 검증만 closeout과 최종 응답에 남기고, 미실행 검증을 섞지 않기 위해 사용했습니다.
- `work-log-closeout`: 이번 구현 라운드의 변경, 검증, 잔여 리스크를 `/work` 형식으로 기록하기 위해 사용했습니다.

## 변경 이유
- 직전 closeout에서 이어받은 핵심 리스크는 exact future `reviewed_memory_local_effect_presence_proof_boundary` contract는 문서로 닫혔지만, current repo에는 그 internal helper 구현이 없다는 점이었습니다.
- 이번 라운드는 proof-boundary helper 하나만 가장 작게 추가하고, same round에서 fact-source-instance helper materialization이나 상위 helper chain widening을 열지 않는 것이 목표였습니다.
- fake proof boundary를 만들지 않고 current repo truth상 absence를 유지해야 했기 때문에, helper는 exact same-aggregate scope 검증만 하고 계속 `None`을 반환하도록 두는 것이 가장 정직했습니다.

## 핵심 변경
- `app/web.py`에 `_build_recurrence_aggregate_reviewed_memory_local_effect_presence_proof_boundary(...)`를 추가했습니다.
- 새 helper는 same exact aggregate identity, exact supporting refs, optional supporting review refs, current resolved `boundary_source_ref`, deterministic `evaluated_at`까지만 검증하고, current repo에 truthful local proof boundary가 없으므로 `None`을 반환합니다.
- `reviewed_memory_local_effect_presence_fact_source_instance`, `reviewed_memory_local_effect_presence_fact_source`, `reviewed_memory_local_effect_presence_event`, producer / event-source / source-consumer / target / handle helpers, `rollback_source_ref`, `reviewed_memory_capability_basis`, `reviewed_memory_transition_record`, blocked aggregate-card affordance는 모두 그대로 유지했습니다.
- `tests/test_smoke.py`, `tests/test_web_app.py`에 proof-boundary helper absent 회귀, boundary draft missing 시 absent 회귀, support-only trace 무시 회귀, fake proof-boundary object 무시 회귀를 추가했습니다.
- root docs와 `plandoc/`는 current truth를 `proof-boundary helper exists but absent`로 동기화했고, next slice wording을 `one truthful same-aggregate local proof-boundary materialization only`로 올렸습니다.

## 검증
- 실행: `python3 -m py_compile app/web.py storage/session_store.py core/agent_loop.py tests/test_smoke.py tests/test_web_app.py`
- 실행: `python3 -m unittest -v tests.test_smoke tests.test_web_app`
  - 결과: `Ran 169 tests in 2.105s`, `OK`
- 실행: `make e2e-test`
  - 결과: `12 passed`
- 실행: `git diff --check`
- 실행: `rg -n "reviewed_memory_local_effect_presence_proof_boundary|reviewed_memory_local_effect_presence_fact_source_instance|reviewed_memory_local_effect_presence_fact_source|reviewed_memory_local_effect_presence_event\\b|reviewed_memory_local_effect_presence_event_producer|reviewed_memory_local_effect_presence_event_source|reviewed_memory_local_effect_presence_record|reviewed_memory_applied_effect_target|reviewed_memory_reversible_effect_handle|rollback_source_ref|reviewed_memory_capability_basis|unblocked_all_required|blocked_all_required|reviewed_memory_transition_record" app/web.py storage/session_store.py core/agent_loop.py tests/test_smoke.py tests/test_web_app.py docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md plandoc/2026-03-29-reviewed-memory-local-effect-proof-boundary-contract.md plandoc/2026-03-29-reviewed-memory-local-effect-presence-fact-source-contract.md plandoc/2026-03-29-reviewed-memory-local-effect-presence-event-contract.md plandoc/2026-03-29-reviewed-memory-applied-effect-target-contract.md plandoc/2026-03-29-reviewed-memory-rollback-backer-contract.md"`

## 남은 리스크
- 이전 closeout에서 이어받은 “proof-boundary contract는 있지만 helper 구현이 없다”는 리스크는 이번 라운드에서 해소했습니다.
- 이번 라운드에서 새로 정리된 current truth는 `reviewed_memory_local_effect_presence_proof_boundary` helper가 now exists-but-absent이고, 그 위 helper chain은 그대로 absence / unresolved라는 점입니다.
- 여전히 남은 핵심 리스크는 current repo에 first local `applied_effect_id`와 same-instant `present_locally_at`를 정직하게 mint할 real same-aggregate local proof boundary가 없다는 점입니다.
- 따라서 다음 slice도 proof-boundary helper materialization만 좁게 열어야 하고, fact-source-instance helper materialization, raw-event helper materialization, producer helper widening, basis emission, `unblocked_all_required`, enabled trigger, emitted transition record는 계속 뒤로 남겨야 합니다.
