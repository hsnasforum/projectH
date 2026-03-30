# 2026-03-29 reviewed-memory local effect proof-record helper implementation

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
- `plandoc/2026-03-29-reviewed-memory-local-effect-proof-record-contract.md`
- `plandoc/2026-03-29-reviewed-memory-local-effect-proof-boundary-contract.md`
- `plandoc/2026-03-29-reviewed-memory-local-effect-presence-fact-source-contract.md`
- `plandoc/2026-03-29-reviewed-memory-local-effect-presence-event-contract.md`
- `plandoc/2026-03-29-reviewed-memory-applied-effect-target-contract.md`
- `plandoc/2026-03-29-reviewed-memory-rollback-backer-contract.md`
- `plandoc/2026-03-29-reviewed-memory-capability-basis-source-contract.md`
- `plandoc/2026-03-29-reviewed-memory-unblocked-capability-path-contract.md`

## 사용 skill
- `doc-sync`: 새 internal helper와 current absence semantics를 root docs / plandoc에 현재 구현 진실대로 맞췄습니다.
- `release-check`: 요청된 검증 명령을 실제로 실행하고 pass/fail 범위를 closeout에 고정했습니다.
- `work-log-closeout`: 이번 라운드의 변경 파일, 검증, 잔여 리스크를 `/work` 형식에 맞춰 기록했습니다.

## 변경 이유
- 이전 closeout에서 이어받은 리스크는 exact future `reviewed_memory_local_effect_presence_proof_record` contract는 문서로 닫혔지만, current repo에는 그 internal helper 구현이 아직 없어서 proof-boundary helper 아래의 lower layer가 코드에 드러나지 않던 점이었습니다.
- 이번 라운드에서는 fake canonical proof record를 만들지 않고, one internal helper boundary만 추가한 뒤 현재 repo truth상 absence를 그대로 유지하는 것이 가장 작은 정직한 구현이었습니다.

## 핵심 변경
- `app/web.py`에 `_build_recurrence_aggregate_reviewed_memory_local_effect_presence_proof_record(...)` helper를 추가했습니다.
- 새 helper는 same exact aggregate scope, exact supporting refs, resolved `boundary_source_ref`, exact `first_seen_at` anchor만 확인하고, `first_seen_at` alone, `candidate_review_record`, `review_queue_items`, approval-backed save support, historical adjunct, `task_log` replay는 canonical proof-record layer로 취급하지 않도록 고정한 뒤 현재 repo truth상 `None`을 반환합니다.
- `reviewed_memory_local_effect_presence_proof_boundary` helper는 이제 새 proof-record helper를 probe하지만, truthful canonical record/store entry가 아직 없어 계속 absence를 유지합니다.
- `tests/test_smoke.py`, `tests/test_web_app.py`에 `task_log` replay alone과 fake proof-record payload가 proof/fact/source/target/backer chain을 열지 못한다는 회귀를 추가했습니다.
- root docs와 `plandoc`에는 current helper truth를 반영하고, next slice wording을 `one truthful same-aggregate canonical local proof-record materialization only`로 좁게 갱신했습니다.
- 이번 라운드에서 해소한 리스크는 “canonical proof-record lower helper가 아직 코드에 없어서 proof-boundary helper 아래 레이어가 문서에만 존재하던 점”입니다.

## 검증
- `python3 -m py_compile app/web.py storage/session_store.py core/agent_loop.py tests/test_smoke.py tests/test_web_app.py`
- `python3 -m unittest -v tests.test_smoke tests.test_web_app`
  - `Ran 169 tests in 2.122s`
  - `OK`
- `make e2e-test`
  - `12 passed (3.2m)`
- `git diff --check`
- `rg -n "reviewed_memory_local_effect_presence_proof_record|reviewed_memory_local_effect_presence_proof_boundary|reviewed_memory_local_effect_presence_fact_source_instance|reviewed_memory_local_effect_presence_fact_source|reviewed_memory_local_effect_presence_event\\b|reviewed_memory_local_effect_presence_event_producer|reviewed_memory_local_effect_presence_event_source|reviewed_memory_local_effect_presence_record|reviewed_memory_applied_effect_target|reviewed_memory_reversible_effect_handle|rollback_source_ref|reviewed_memory_capability_basis|unblocked_all_required|blocked_all_required|reviewed_memory_transition_record" app/web.py storage/session_store.py core/agent_loop.py tests/test_smoke.py tests/test_web_app.py docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md plandoc/2026-03-29-reviewed-memory-local-effect-proof-record-contract.md plandoc/2026-03-29-reviewed-memory-local-effect-proof-boundary-contract.md plandoc/2026-03-29-reviewed-memory-local-effect-presence-fact-source-contract.md plandoc/2026-03-29-reviewed-memory-local-effect-presence-event-contract.md plandoc/2026-03-29-reviewed-memory-applied-effect-target-contract.md plandoc/2026-03-29-reviewed-memory-rollback-backer-contract.md"`

## 남은 리스크
- 여전히 남은 리스크는 first local `applied_effect_id`와 same-instant `present_locally_at`를 canonical하게 mint할 real same-aggregate canonical local proof-record/store entry가 current repo에 없다는 점입니다.
- 그래서 `reviewed_memory_local_effect_presence_proof_boundary`, `reviewed_memory_local_effect_presence_fact_source_instance`, `reviewed_memory_local_effect_presence_fact_source`, raw-event/helper chain, `reviewed_memory_capability_basis`, `reviewed_memory_transition_record`, `unblocked_all_required`는 계속 absence/unresolved입니다.
- 다음 slice는 one truthful same-aggregate canonical local proof-record materialization only가 가장 작습니다. 지금 repo에서 비어 있는 것은 상위 helper가 아니라 방금 추가한 proof-record helper 아래의 real canonical local store entry이기 때문입니다.
