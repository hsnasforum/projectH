# 2026-03-29 reviewed-memory rollback-source unresolved implementation

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
- `plandoc/2026-03-29-reviewed-memory-capability-basis-source-contract.md`
- `plandoc/2026-03-29-reviewed-memory-unblocked-capability-path-contract.md`
- `work/3/29/2026-03-29-reviewed-memory-rollback-source-unresolved-implementation.md`

## 사용 skill
- `mvp-scope`: second backer 범위를 `rollback_source_ref` exact-scope unresolved slice로 제한했습니다.
- `approval-flow-audit`: approval-backed save, historical adjunct, review acceptance, `task_log` replay가 rollback backer처럼 읽히지 않도록 경계를 다시 점검했습니다.
- `doc-sync`: root docs와 `plandoc`를 current implementation truth에 맞춰 동기화했습니다.
- `release-check`: 실제 실행한 syntax, unittest, e2e, diff, `rg` 결과만 기준으로 라운드를 닫았습니다.
- `work-log-closeout`: 저장소 형식에 맞춰 이번 구현 라운드의 변경과 남은 리스크를 기록했습니다.

## 변경 이유
- 이전 closeout에서 `boundary_source_ref`는 same exact aggregate scope에서 truthfully resolve되기 시작했지만, `rollback_source_ref`를 가리킬 real later local rollback-capability source는 아직 없었습니다.
- 이 상태에서 second backer를 억지로 열면 current rollback contract, review acceptance, approval-backed save support, historical adjunct, `task_log` replay를 local backer처럼 잘못 해석할 위험이 있었습니다.

## 핵심 변경
- `app/web.py`의 `_resolve_recurrence_aggregate_reviewed_memory_rollback_source_ref(...)`가 current `reviewed_memory_rollback_contract`, aggregate identity, supporting refs, optional review refs, required preconditions를 exact same aggregate scope로 검증한 뒤에만 unresolved state를 유지하도록 바꿨습니다.
- current repo에 later applied-effect rollback-capability backer가 아직 없기 때문에 resolver는 계속 `None`을 반환하며, fake `rollback_source_ref`는 여전히 열리지 않습니다.
- `boundary_source_ref` truth는 그대로 유지했고, full `reviewed_memory_capability_source_refs` family는 계속 non-materialized 상태로 남겼습니다.
- `reviewed_memory_capability_basis` absence, `reviewed_memory_capability_status.capability_outcome = blocked_all_required`, blocked aggregate-card affordance, `reviewed_memory_transition_record` absence도 그대로 유지했습니다.
- focused regression을 추가해 rollback resolver가 aggregate mismatch, missing precondition, missing rollback contract, support-only traces에서도 계속 unresolved를 유지하는지 확인했습니다.
- root docs와 `plandoc`은 “boundary는 resolved, rollback은 exact-scope-validated but unresolved”라는 current implementation truth로 맞췄습니다.

## 검증
- 실행: `python3 -m py_compile app/web.py storage/session_store.py core/agent_loop.py tests/test_smoke.py tests/test_web_app.py`
- 실행: `python3 -m unittest -v tests.test_smoke tests.test_web_app`
  - 결과: `169` tests passed
- 실행: `make e2e-test`
  - 결과: `12` browser tests passed
- 실행: `git diff --check`
- 실행: `rg -n "rollback_source_ref|boundary_source_ref|reviewed_memory_capability_source_refs|reviewed_memory_capability_basis|unblocked_all_required|blocked_all_required|reviewed_memory_capability_status|reviewed_memory_transition_record|검토 메모 적용 시작|candidate_review_record" app/web.py storage/session_store.py core/agent_loop.py tests/test_smoke.py tests/test_web_app.py docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md plandoc/2026-03-29-reviewed-memory-capability-basis-source-contract.md plandoc/2026-03-29-reviewed-memory-unblocked-capability-path-contract.md`

## 남은 리스크
- 이전 closeout에서 이어받은 핵심 리스크:
  - `boundary_source_ref`는 열렸지만 `rollback_source_ref`를 가리킬 real later local rollback-capability source backer가 아직 없었습니다.
- 이번 라운드에서 해소한 리스크:
  - `rollback_source_ref` unresolved state를 아무 aggregate에나 열린 stub가 아니라 exact same aggregate / exact rollback contract에 묶인 unresolved truth로 고정했습니다.
  - support-only traces나 fake input이 second backer처럼 오해되는 경로를 더 줄였습니다.
- 여전히 남은 리스크:
  - real later local `rollback_source_ref` backer는 아직 없습니다.
  - `disable_source_ref`, `conflict_source_ref`, `transition_audit_source_ref`도 계속 unresolved입니다.
  - `reviewed_memory_capability_basis`, `unblocked_all_required`, enabled trigger, emitted transition record, reviewed-memory apply result, repeated-signal promotion, cross-session counting, user-level memory는 계속 later layer입니다.
