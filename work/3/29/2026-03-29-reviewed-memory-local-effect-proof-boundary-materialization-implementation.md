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

## 사용 skill
- `mvp-scope`
- `doc-sync`
- `release-check`
- `work-log-closeout`

## 변경 이유
- 이전 closeout에서 이어받은 리스크는 internal `reviewed_memory_local_effect_presence_proof_boundary` helper가 이미 존재하지만, current repo에는 그 helper가 truthfully materialize할 real same-aggregate local proof boundary가 아직 없다는 점이었습니다.
- 이번 라운드에서는 fake proof boundary를 만들지 않고, current helper가 어떤 입력을 최소 전제로 보되 무엇을 절대 proof로 오해하지 않는지 코드와 회귀로 더 명시할 필요가 있었습니다.

## 핵심 변경
- `app/web.py`의 `reviewed_memory_local_effect_presence_proof_boundary` helper가 이제 exact aggregate `first_seen_at` anchor가 없으면 바로 absence를 유지하도록 했습니다.
- 같은 helper에서 `candidate_review_record`, `review_queue_items`, approval-backed save support, historical adjunct, `task_log` replay를 support/mirror trace로만 취급하고 proof boundary로 materialize하지 않도록 current truth를 코드로 고정했습니다.
- `tests/test_smoke.py`, `tests/test_web_app.py`에 `first_seen_at`가 빠진 aggregate에서도 proof-boundary helper와 그 위 helper chain이 계속 absent/unresolved인지 확인하는 회귀를 추가했습니다.
- root docs와 `plandoc`에 현재 helper가 exact `first_seen_at`를 필요 anchor로만 보고, review/save/history/task-log traces는 여전히 proof boundary가 아니라는 구현 현실을 동기화했습니다.
- 이번 라운드에서 해소한 리스크는 “proof-boundary helper가 unconditional `None`처럼 보이면서 current exclusion rule이 코드상 충분히 드러나지 않던 점”입니다.

## 검증
- `python3 -m py_compile app/web.py storage/session_store.py core/agent_loop.py tests/test_smoke.py tests/test_web_app.py`
- `python3 -m unittest -v tests.test_smoke tests.test_web_app`
  - `Ran 169 tests in 2.614s`
  - `OK`
- `make e2e-test`
  - `12 passed`
- `git diff --check`
- `rg -n "reviewed_memory_local_effect_presence_proof_boundary|reviewed_memory_local_effect_presence_fact_source_instance|reviewed_memory_local_effect_presence_fact_source|reviewed_memory_local_effect_presence_event\\b|reviewed_memory_local_effect_presence_event_producer|reviewed_memory_local_effect_presence_event_source|reviewed_memory_local_effect_presence_record|reviewed_memory_applied_effect_target|reviewed_memory_reversible_effect_handle|rollback_source_ref|reviewed_memory_capability_basis|unblocked_all_required|blocked_all_required|reviewed_memory_transition_record" app/web.py storage/session_store.py core/agent_loop.py tests/test_smoke.py tests/test_web_app.py docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md plandoc/2026-03-29-reviewed-memory-local-effect-proof-boundary-contract.md plandoc/2026-03-29-reviewed-memory-local-effect-presence-fact-source-contract.md plandoc/2026-03-29-reviewed-memory-local-effect-presence-event-contract.md plandoc/2026-03-29-reviewed-memory-applied-effect-target-contract.md plandoc/2026-03-29-reviewed-memory-rollback-backer-contract.md"`

## 남은 리스크
- 여전히 남은 리스크는 first local `applied_effect_id`와 same-instant `present_locally_at`를 canonical하게 mint할 real same-aggregate local proof boundary가 current repo에 없다는 점입니다.
- 그래서 `reviewed_memory_local_effect_presence_fact_source_instance`, `reviewed_memory_local_effect_presence_fact_source`, raw-event/helper chain, `reviewed_memory_capability_basis`, `reviewed_memory_transition_record`, `unblocked_all_required`는 계속 absence/unresolved입니다.
- 다음 slice는 one truthful same-aggregate local proof-boundary materialization only 자체를 여는 것이 아니라, 그보다 더 아래에서 canonical local proof record를 어디에 둘지 정하는 adjacent implementation이 필요할 수 있습니다.
