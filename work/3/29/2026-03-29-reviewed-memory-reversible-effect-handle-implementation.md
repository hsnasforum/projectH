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
- `plandoc/2026-03-29-reviewed-memory-rollback-backer-contract.md`
- `plandoc/2026-03-29-reviewed-memory-capability-basis-source-contract.md`
- `plandoc/2026-03-29-reviewed-memory-unblocked-capability-path-contract.md`
- `work/3/29/2026-03-29-reviewed-memory-reversible-effect-handle-implementation.md`

## 사용 skill
- `mvp-scope`
- `approval-flow-audit`
- `doc-sync`
- `release-check`
- `work-log-closeout`

## 변경 이유
- 이전 closeout에서는 `rollback_source_ref` resolver가 exact aggregate / exact contract / exact supporting refs 기준으로 unresolved 상태까지만 고정되어 있었고, 그 위의 real later local rollback-capability backer는 아직 코드에 없었습니다.
- 이번 라운드에서는 그 공백을 가장 작은 범위로 메우기 위해 one internal local `reviewed_memory_reversible_effect_handle` helper를 추가하고, `rollback_source_ref`가 contract existence가 아니라 그 helper를 통해서만 later backer를 찾도록 연결해야 했습니다.
- 동시에 current repo에는 still no later local applied reviewed-memory effect target이 있으므로, fake handle이나 status widening 없이 truthful absence를 유지해야 했습니다.

## 핵심 변경
- `app/web.py`
  - `_build_recurrence_aggregate_reviewed_memory_reversible_effect_handle(...)`를 추가했습니다.
  - helper는 same exact aggregate, same supporting refs, current `reviewed_memory_rollback_contract`, current resolved `boundary_source_ref`, `rollback_ready_reviewed_memory_effect` precondition까지 확인한 뒤에만 later local handle을 평가합니다.
  - current repo에는 아직 truthful local applied-effect target이 없으므로 helper는 계속 `None`을 반환합니다.
  - `_resolve_recurrence_aggregate_reviewed_memory_rollback_source_ref(...)`는 이제 contract-only path를 쓰지 않고, 위 internal handle helper 결과가 있을 때만 later ref를 만들 수 있게 정리했습니다.
- 회귀
  - ordinary aggregate와 support-only traces에서 internal handle helper가 계속 absence인지 검증했습니다.
  - fake `reviewed_memory_reversible_effect_handle` aggregate input만으로는 helper나 `rollback_source_ref`가 resolve되지 않음을 고정했습니다.
  - `reviewed_memory_capability_basis` absence, `reviewed_memory_capability_status.capability_outcome = blocked_all_required`, `reviewed_memory_transition_record` absence가 그대로 유지됨을 다시 확인했습니다.
- 문서
  - current implementation fact를 narrow sync 했습니다.
  - 내부 `reviewed_memory_reversible_effect_handle` helper가 이제 same exact aggregate에서 평가되지만, current repo에는 later local applied reviewed-memory effect target이 없어서 still no result라는 점만 추가했습니다.
  - UI, emitted record, basis object, `unblocked_all_required` semantics는 widen하지 않았습니다.

## 검증
- 실행: `python3 -m py_compile app/web.py storage/session_store.py core/agent_loop.py tests/test_smoke.py tests/test_web_app.py`
- 실행: `python3 -m unittest -v tests.test_smoke tests.test_web_app`
  - 결과: `169` tests passed
- 실행: `make e2e-test`
  - 결과: `12` tests passed
- 실행: `git diff --check`
- 실행: `rg -n "reviewed_memory_reversible_effect_handle|rollback_source_ref|boundary_source_ref|reviewed_memory_capability_source_refs|reviewed_memory_capability_basis|unblocked_all_required|blocked_all_required|reviewed_memory_transition_record|candidate_review_record" app/web.py storage/session_store.py core/agent_loop.py tests/test_smoke.py tests/test_web_app.py docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md plandoc/2026-03-29-reviewed-memory-rollback-backer-contract.md plandoc/2026-03-29-reviewed-memory-capability-basis-source-contract.md plandoc/2026-03-29-reviewed-memory-unblocked-capability-path-contract.md`

## 남은 리스크
- 이전 closeout에서 이어받은 리스크였던 “real rollback-capability backer 부재”는 helper layer 기준으로는 해소했지만, actual later local applied reviewed-memory effect target은 여전히 없습니다.
- 이번 라운드에서 해소한 리스크는 `rollback_source_ref`가 더 이상 current rollback contract나 support-only traces를 backer처럼 오해하지 않게 된 점입니다.
- 여전히 남은 리스크는 real handle target이 아직 없어서 `rollback_source_ref`가 계속 unresolved라는 점과, `disable_source_ref`, `conflict_source_ref`, `transition_audit_source_ref`가 모두 여전히 unresolved라는 점입니다.
