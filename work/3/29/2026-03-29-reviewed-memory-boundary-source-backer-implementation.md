# 2026-03-29 reviewed-memory boundary-source backer implementation

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
- `work/3/29/2026-03-29-reviewed-memory-boundary-source-backer-implementation.md`

## 사용 skill
- `mvp-scope`: five source refs 중 first backer만 열고 basis/status/apply 쪽 widening을 막는 현재 MVP 경계를 유지했습니다.
- `approval-flow-audit`: `candidate_review_record`, approval-backed save, historical adjunct, `task_log` replay가 backer나 basis로 오인되지 않도록 회귀 기준을 유지했습니다.
- `doc-sync`: internal `boundary_source_ref` backer 하나만 resolved된 현재 구현 truth에 맞춰 root docs와 `plandoc`를 동기화했습니다.
- `release-check`: syntax, focused unittest, e2e, diff, `rg`를 실제 실행 기준으로 정리했습니다.
- `work-log-closeout`: 저장소 `/work` 형식에 맞춰 이번 구현 라운드의 변경과 남은 리스크를 기록했습니다.

## 변경 이유
- 이전 closeout에서 이어받은 핵심 리스크는 internal `reviewed_memory_capability_source_refs` helper family는 이미 있지만, current repo에 real later local source backer가 없어 family 전체가 unresolved라는 점이었습니다.
- 이 상태에서 basis object나 `unblocked_all_required`를 먼저 열면 current contract chain, support-only traces, `task_log` replay를 capability backer처럼 잘못 읽을 위험이 남아 있었습니다.
- 그래서 이번 라운드는 five refs 중 가장 작은 첫 backer 하나만 연결하고, same round에서 payload-visible basis, status widening, enabled trigger, emitted record, apply result를 열지 않는 데 집중했습니다.

## 핵심 변경
- `app/web.py`에서 `_resolve_recurrence_aggregate_reviewed_memory_boundary_source_ref(...)`가 더 이상 무조건 `None`만 반환하지 않고, same exact aggregate의 current `reviewed_memory_boundary_draft`와 source-context supporting refs가 정확히 맞을 때 one real later local backer를 internal-only로 반환하도록 구현했습니다.
- first backer는 existing aggregate-level blocked trigger affordance 기준으로 고정했습니다:
  - `ref_kind = aggregate_reviewed_memory_trigger_affordance`
  - fixed `trigger_action_label = 검토 메모 적용 시작`
  - fixed `trigger_state = visible_disabled`
  - fixed planning-only target meaning
- other four refs는 그대로 unresolved입니다:
  - `rollback_source_ref`
  - `disable_source_ref`
  - `conflict_source_ref`
  - `transition_audit_source_ref`
- 그래서 current truth도 그대로 유지됩니다:
  - full `reviewed_memory_capability_source_refs` family still unresolved
  - `reviewed_memory_capability_basis` still absent
  - `reviewed_memory_capability_status.capability_outcome = blocked_all_required` 유지
  - `reviewed_memory_transition_record` still absent
  - aggregate card `검토 메모 적용 시작` disabled 유지
- focused regression을 보강했습니다:
  - ordinary aggregate에서 `boundary_source_ref` 하나만 exact shape로 resolve되는지
  - aggregate identity mismatch나 missing boundary draft에서는 `boundary_source_ref`가 다시 `None`으로 떨어지는지
  - one backer만 있어도 full family / basis / status widening은 일어나지 않는지
  - `candidate_review_record`, approval-backed save, historical adjunct, `task_log` replay, fake source inputs가 여전히 basis/status를 만들지 않는지
- docs와 `plandoc`는 “first `boundary_source_ref` backer resolved, other four unresolved, family/basis/status still blocked” 상태로 동기화했고, next slice 추천을 `rollback_source_ref` backer only로 좁혔습니다.

## 검증
- 실행: `python3 -m py_compile app/web.py storage/session_store.py core/agent_loop.py tests/test_smoke.py tests/test_web_app.py`
- 실행: `python3 -m unittest -v tests.test_smoke tests.test_web_app`
  - 결과: `169` tests passed
- 실행: `make e2e-test`
  - 결과: `12` tests passed
- 실행: `git diff --check`
- 실행: `rg -n 'boundary_source_ref|reviewed_memory_capability_source_refs|reviewed_memory_capability_basis|unblocked_all_required|blocked_all_required|reviewed_memory_capability_status|reviewed_memory_transition_record|검토 메모 적용 시작|candidate_review_record' app/web.py storage/session_store.py core/agent_loop.py tests/test_smoke.py tests/test_web_app.py docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md plandoc/2026-03-29-reviewed-memory-capability-basis-source-contract.md plandoc/2026-03-29-reviewed-memory-unblocked-capability-path-contract.md`

## 남은 리스크
- 이전 closeout에서 이어받은 핵심 리스크:
  - source helper family는 있었지만 real later local source backer가 없어서 basis/source widening이 모두 막혀 있었습니다.
- 이번 라운드에서 해소한 리스크:
  - first `boundary_source_ref` backer를 same exact aggregate scope에서 truthfully resolve할 수 있게 했습니다.
  - current blocked trigger affordance를 더 ready하게 보이지 않게 유지하면서도, internal source layer가 support-only traces와 구분되도록 고정했습니다.
- 여전히 남은 리스크:
  - `rollback_source_ref`, `disable_source_ref`, `conflict_source_ref`, `transition_audit_source_ref`는 아직 unresolved입니다.
  - 그래서 full `reviewed_memory_capability_source_refs` family, `reviewed_memory_capability_basis`, `unblocked_all_required`, enabled aggregate card, note input, emitted transition record, reviewed-memory apply result는 모두 계속 later layer입니다.
  - repeated-signal promotion, cross-session counting, user-level memory도 계속 닫혀 있습니다.
