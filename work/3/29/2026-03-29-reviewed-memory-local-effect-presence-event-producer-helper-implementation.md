# 2026-03-29 reviewed-memory local effect-presence event producer helper implementation

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
- `plandoc/2026-03-29-reviewed-memory-applied-effect-presence-source-contract.md`
- `plandoc/2026-03-29-reviewed-memory-applied-effect-target-contract.md`
- `plandoc/2026-03-29-reviewed-memory-rollback-backer-contract.md`
- `plandoc/2026-03-29-reviewed-memory-capability-basis-source-contract.md`
- `plandoc/2026-03-29-reviewed-memory-unblocked-capability-path-contract.md`
- `work/3/29/2026-03-29-reviewed-memory-local-effect-presence-event-producer-helper-implementation.md`

## 사용 skill
- `mvp-scope`: current shipped contract와 next-slice wording을 지금 구현 경계에 맞췄습니다.
- `doc-sync`: code/test 변화에 맞춰 root docs와 `plandoc/`를 구현 truth 기준으로 동기화했습니다.
- `release-check`: 필수 py_compile, unittest, Playwright smoke, diff check를 실제 실행 결과 기준으로 정리했습니다.
- `work-log-closeout`: 이번 라운드 변경, 검증, 남은 리스크를 `/work` closeout 형식에 맞춰 기록했습니다.

## 변경 이유
- 직전 closeout에서 이어받은 핵심 리스크는 `reviewed_memory_local_effect_presence_event_source` helper 아래의 truthful local effect-presence event producer가 아직 없다는 점이었습니다.
- current repo에는 still no real local event가 있으므로, fake producer를 만들지 않고 exact-scope producer helper 층을 먼저 코드로 닫아 둘 필요가 있었습니다.
- 이 층을 분리하지 않으면 current contracts, support-only traces, fake aggregate injection이 later local event producer처럼 오해될 위험이 계속 남습니다.

## 핵심 변경
- `app/web.py`에 internal `_build_recurrence_aggregate_reviewed_memory_local_effect_presence_event_producer(...)` helper를 추가했습니다.
- new helper는 same exact aggregate identity, exact supporting refs, current resolved `boundary_source_ref`, deterministic `evaluated_at`까지만 검증하고, current repo에 truthful local effect-presence event가 없으므로 계속 `None`을 반환합니다.
- existing `reviewed_memory_local_effect_presence_event_source` helper는 이제 new producer helper만 probe하고, producer가 없으면 계속 absence를 유지하도록 바꿨습니다.
- existing `reviewed_memory_local_effect_presence_record`, `reviewed_memory_applied_effect_target`, `reviewed_memory_reversible_effect_handle`, `rollback_source_ref`, `reviewed_memory_capability_basis`, `capability_outcome = blocked_all_required`, blocked aggregate UI, `reviewed_memory_transition_record` absence는 그대로 유지했습니다.
- `tests/test_smoke.py`, `tests/test_web_app.py`에 ordinary aggregate, missing boundary draft, support-only traces, fake producer input에서도 new producer helper와 상위 helper들이 계속 absence/unresolved인지 회귀를 추가했습니다.
- root docs와 `plandoc/`는 current truth를 `reviewed_memory_local_effect_presence_event_producer` helper exists but absent, `reviewed_memory_local_effect_presence_event_source` helper probes it and still stays absent로 다시 맞추고, next slice wording을 “truthful local effect-presence event producer materialization only”로 갱신했습니다.

## 검증
- 실행: `python3 -m py_compile app/web.py storage/session_store.py core/agent_loop.py tests/test_smoke.py tests/test_web_app.py`
- 실행: `python3 -m unittest -v tests.test_smoke tests.test_web_app`
  - 결과: `169` tests passed
- 실행: `make e2e-test`
  - 결과: `12` tests passed
- 실행: `git diff --check`
- 실행: `rg -n "reviewed_memory_local_effect_presence_event_producer|reviewed_memory_local_effect_presence_event_source|reviewed_memory_local_effect_presence_record|reviewed_memory_applied_effect_target|reviewed_memory_reversible_effect_handle|rollback_source_ref|disable_source_ref|reviewed_memory_capability_basis|unblocked_all_required|blocked_all_required|reviewed_memory_transition_record" app/web.py storage/session_store.py core/agent_loop.py tests/test_smoke.py tests/test_web_app.py docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md plandoc/2026-03-29-reviewed-memory-applied-effect-presence-source-contract.md plandoc/2026-03-29-reviewed-memory-applied-effect-target-contract.md plandoc/2026-03-29-reviewed-memory-rollback-backer-contract.md plandoc/2026-03-29-reviewed-memory-capability-basis-source-contract.md plandoc/2026-03-29-reviewed-memory-unblocked-capability-path-contract.md`

## 남은 리스크
- 이전 closeout에서 이어받은 리스크였던 “exact local effect-presence event producer 부재”는 helper boundary 기준으로는 더 명확히 분리됐지만, truthful local event 자체는 여전히 없습니다.
- 이번 라운드에서 해소한 것은 current repo가 contracts/support traces/fake aggregate input을 event producer처럼 읽지 못하게 producer helper 경계를 코드와 테스트로 고정한 점입니다.
- 여전히 남은 리스크는 real local event가 없어서 `reviewed_memory_local_effect_presence_event_producer`, `reviewed_memory_local_effect_presence_event_source`, `reviewed_memory_local_effect_presence_record`, `reviewed_memory_applied_effect_target`, `reviewed_memory_reversible_effect_handle`, `rollback_source_ref`가 모두 계속 absence/unresolved라는 점입니다.
- 다음 slice는 one truthful same-aggregate local effect-presence event producer materialization only가 가장 작습니다. basis object, `unblocked_all_required`, enabled trigger, emitted transition record, reviewed-memory apply result보다 먼저 그 local event 하나를 truthfully 열어야 현재 helper chain이 실제 result를 만들 수 있습니다.
