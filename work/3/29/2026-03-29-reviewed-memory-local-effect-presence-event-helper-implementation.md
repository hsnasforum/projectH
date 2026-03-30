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
- `plandoc/2026-03-29-reviewed-memory-local-effect-presence-event-contract.md`
- `plandoc/2026-03-29-reviewed-memory-applied-effect-presence-source-contract.md`
- `plandoc/2026-03-29-reviewed-memory-applied-effect-target-contract.md`
- `plandoc/2026-03-29-reviewed-memory-rollback-backer-contract.md`
- `plandoc/2026-03-29-reviewed-memory-capability-basis-source-contract.md`
- `plandoc/2026-03-29-reviewed-memory-unblocked-capability-path-contract.md`
- `work/3/29/2026-03-29-reviewed-memory-local-effect-presence-event-helper-implementation.md`

## 사용 skill
- `mvp-scope`
- `doc-sync`
- `release-check`
- `work-log-closeout`

## 변경 이유
- 직전 closeout에서 이어받은 핵심 리스크는, exact raw local effect-presence event contract는 문서로 닫혔지만 current repo에는 그 contract를 담을 internal `reviewed_memory_local_effect_presence_event` helper조차 없어서 producer helper 아래의 raw fact layer가 코드에 부재하다는 점이었습니다.
- 이번 라운드는 그 raw helper 하나만 가장 작게 추가하고, same round에서 producer helper, event-source helper, source-consumer helper, target helper, basis, status widening, UI enablement를 열지 않는 것이 목표였습니다.

## 핵심 변경
- `app/web.py`에 `_build_recurrence_aggregate_reviewed_memory_local_effect_presence_event(...)`를 추가했습니다.
- 새 helper는 same exact aggregate identity, exact supporting refs, optional supporting review refs, current resolved `boundary_source_ref`, deterministic `evaluated_at`까지만 검증하고, current repo에 truthful local event source가 없으므로 계속 `None`을 반환합니다.
- producer helper는 이번 라운드에서 새 raw helper를 직접 소비하지 않게 유지했습니다. 따라서 `reviewed_memory_local_effect_presence_event_producer`, `reviewed_memory_local_effect_presence_event_source`, `reviewed_memory_local_effect_presence_record`, `reviewed_memory_applied_effect_target`, `reviewed_memory_reversible_effect_handle`, `rollback_source_ref`는 그대로 absence 또는 unresolved입니다.
- `tests/test_smoke.py`, `tests/test_web_app.py`에는 raw helper absent, boundary draft missing 시 raw helper absent, support-only traces로 raw helper 미생성, fake raw event object로도 상위 chain 미개방 회귀를 추가했습니다.
- root docs와 `plandoc/`는 current truth를 “raw local event helper exists but absent”로 동기화했고, next slice wording을 “same-aggregate local effect-presence event materialization only”로 갱신했습니다.

## 검증
- 실행: `python3 -m py_compile app/web.py storage/session_store.py core/agent_loop.py tests/test_smoke.py tests/test_web_app.py`
- 실행: `python3 -m unittest -v tests.test_smoke tests.test_web_app`
  - 결과: `169` tests passed
- 실행: `make e2e-test`
  - 결과: `12` passed
- 실행: `git diff --check`
- 실행: `rg -n "reviewed_memory_local_effect_presence_event\\b|reviewed_memory_local_effect_presence_event_producer|reviewed_memory_local_effect_presence_event_source|reviewed_memory_local_effect_presence_record|reviewed_memory_applied_effect_target|reviewed_memory_reversible_effect_handle|rollback_source_ref|reviewed_memory_capability_basis|unblocked_all_required|blocked_all_required|reviewed_memory_transition_record" app/web.py storage/session_store.py core/agent_loop.py tests/test_smoke.py tests/test_web_app.py docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md plandoc/2026-03-29-reviewed-memory-local-effect-presence-event-contract.md plandoc/2026-03-29-reviewed-memory-applied-effect-presence-source-contract.md plandoc/2026-03-29-reviewed-memory-applied-effect-target-contract.md plandoc/2026-03-29-reviewed-memory-rollback-backer-contract.md`

## 남은 리스크
- 이번 라운드에서 해소한 리스크는 raw local fact layer helper 부재입니다. 이제 producer helper 아래의 exact layer는 코드와 테스트에 존재합니다.
- 여전히 남은 리스크는 truthful same-aggregate local effect-presence fact를 실제로 mint할 real local event source가 current repo에 없다는 점입니다. 그래서 raw helper는 계속 absence를 유지하고, 상위 helper chain도 전부 닫혀 있습니다.
- 다음 slice는 one truthful same-aggregate local effect-presence event materialization only가 가장 작습니다. raw helper가 이미 있으므로 그 아래의 real local fact만 열어도 producer helper 이전 층을 정직하게 한 단계 올릴 수 있습니다.
