# 2026-03-29 reviewed-memory capability-source helper implementation

## 변경 파일
- `app/web.py`
- `tests/test_smoke.py`
- `tests/test_web_app.py`
- `docs/PRODUCT_SPEC.md`
- `docs/ARCHITECTURE.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/MILESTONES.md`
- `docs/NEXT_STEPS.md`
- `docs/TASK_BACKLOG.md`
- `plandoc/2026-03-29-reviewed-memory-capability-basis-source-contract.md`
- `plandoc/2026-03-29-reviewed-memory-unblocked-capability-path-contract.md`
- `work/3/29/2026-03-29-reviewed-memory-capability-source-helper-implementation.md`

## 사용 skill
- `mvp-scope`: current blocked contract chain, internal source layer, later basis/apply layer를 다시 분리하고 이번 구현 범위를 helper-only로 제한했습니다.
- `approval-flow-audit`: `candidate_review_record`, approval-backed save, historical adjunct, `task_log` replay가 capability source로 오해되지 않도록 검증 축을 잡았습니다.
- `doc-sync`: implementation truth에 맞춰 root docs와 `plandoc` wording을 source-helper-implemented-but-unresolved 상태로 맞췄습니다.
- `release-check`: syntax, focused unittest, e2e, diff, `rg` 결과를 실제 실행 기준으로 정리했습니다.
- `work-log-closeout`: 저장소 형식에 맞춰 이번 구현 라운드의 변경과 남은 리스크를 기록했습니다.

## 변경 이유
- 이전 closeout에서 이어받은 핵심 리스크는 exact `reviewed_memory_capability_basis` source contract는 문서로 닫혔지만, current repo에는 still no internal `reviewed_memory_capability_source_refs` helper-family implementation이라는 점이었습니다.
- 이 상태를 그대로 두면 다음 구현이 current contract chain, review acceptance, approval-backed save support, historical adjunct, `task_log` replay를 source처럼 잘못 읽을 위험이 남아 있었습니다.
- 그래서 이번 라운드는 payload-visible basis object나 status widening이 아니라, internal source helper family만 최소로 세우고 current unresolved truth를 그대로 보존하는 데 집중했습니다.

## 핵심 변경
- `app/web.py`에 one exact internal aggregate-scoped helper family `_build_recurrence_aggregate_reviewed_memory_capability_source_refs(...)`를 추가했습니다.
- helper family는 current same-session exact aggregate의 current `reviewed_memory_transition_audit_contract` / `reviewed_memory_unblock_contract` chain이 여전히 일치하는지 검증한 뒤, future internal source shape를 구성할 문맥만 정리합니다.
- five capability source resolvers를 별도 helper로 추가했습니다:
  - `boundary_source_ref`
  - `rollback_source_ref`
  - `disable_source_ref`
  - `conflict_source_ref`
  - `transition_audit_source_ref`
- current repo에는 truthful later local source ref가 아직 없으므로, 위 resolver들은 모두 `None`을 반환하고 source family 전체도 unresolved를 유지합니다.
- `reviewed_memory_capability_basis` helper는 이제 internal source family를 선행 조건으로 보지만, 이번 라운드에서는 still `None`만 반환하도록 유지했습니다.
- 따라서 current truth는 그대로 보존됩니다:
  - `reviewed_memory_capability_basis` payload absence 유지
  - `reviewed_memory_capability_status.capability_outcome = blocked_all_required` 유지
  - `reviewed_memory_transition_record` absence 유지
  - aggregate card `검토 메모 적용 시작` disabled 유지
- focused regression을 보강했습니다:
  - ordinary aggregate payload에서 internal source helper가 unresolved인지
  - support-only signals와 `task_log` replay alone이 source family를 만들지 않는지
  - fake `reviewed_memory_capability_source_refs` input이 helper resolution, basis materialization, capability status widening을 만들지 않는지
- docs와 `plandoc`는 “internal helper family is now implemented, but still unresolved because no truthful later local source refs exist”라는 현재 truth로 동기화했습니다.

## 검증
- 실행: `python3 -m py_compile app/web.py storage/session_store.py core/agent_loop.py tests/test_smoke.py tests/test_web_app.py`
- 실행: `python3 -m unittest -v tests.test_smoke tests.test_web_app`
  - 결과: `169` tests passed
- 실행: `make e2e-test`
  - 결과: `12` tests passed
- 실행: `git diff --check`
- 실행: `rg -n 'reviewed_memory_capability_source_refs|reviewed_memory_capability_basis|unblocked_all_required|blocked_all_required|reviewed_memory_capability_status|reviewed_memory_transition_record|검토 메모 적용 시작|candidate_review_record' app/web.py storage/session_store.py core/agent_loop.py tests/test_smoke.py tests/test_web_app.py docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md plandoc/2026-03-29-reviewed-memory-capability-basis-source-contract.md plandoc/2026-03-29-reviewed-memory-unblocked-capability-path-contract.md`

## 남은 리스크
- 이전 closeout에서 이어받은 핵심 리스크:
  - internal source layer contract는 문서로 닫혔지만, current repo에 helper family 자체가 없어 다음 구현이 support-only traces를 source처럼 잘못 읽을 수 있었습니다.
- 이번 라운드에서 해소한 리스크:
  - internal source helper family를 코드에 세웠고, current repo에 truthful local source ref가 없을 때는 unresolved를 유지하도록 고정했습니다.
  - fake source input, `candidate_review_record`, approval-backed save, historical adjunct, `task_log` replay가 source resolution으로 오인되는 경로를 회귀로 막았습니다.
- 여전히 남은 리스크:
  - five capability source refs를 truthfully resolve할 real later local source backer는 아직 없습니다.
  - 그래서 `reviewed_memory_capability_basis`, `unblocked_all_required`, enabled aggregate card, note input, emitted transition record, reviewed-memory apply result는 계속 later layer입니다.
  - repeated-signal promotion, cross-session counting, user-level memory도 계속 닫혀 있습니다.
