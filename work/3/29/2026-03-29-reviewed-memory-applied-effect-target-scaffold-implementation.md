# 2026-03-29 reviewed-memory applied-effect target scaffold implementation

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
- `plandoc/2026-03-29-reviewed-memory-applied-effect-target-contract.md`
- `plandoc/2026-03-29-reviewed-memory-rollback-backer-contract.md`
- `plandoc/2026-03-29-reviewed-memory-capability-basis-source-contract.md`
- `plandoc/2026-03-29-reviewed-memory-unblocked-capability-path-contract.md`
- `work/3/29/2026-03-29-reviewed-memory-applied-effect-target-scaffold-implementation.md`

## 사용 skill
- `mvp-scope`: current blocked contract chain, target helper, later source/basis/emission layer를 다시 분리하고 이번 구현 범위를 scaffold-only로 제한했습니다.
- `doc-sync`: internal target helper가 추가됐지만 payload truth가 그대로라는 현재 구현 사실에 맞춰 root docs와 `plandoc`을 동기화했습니다.
- `release-check`: syntax, focused unittest, e2e, `rg`, `git diff --check`를 실제 실행 기준으로 정리했습니다.
- `work-log-closeout`: 저장소 `/work` 형식에 맞춰 이번 구현 라운드의 변경과 남은 리스크를 기록했습니다.

## 변경 이유
- 이전 closeout에서 이어받은 핵심 리스크는 exact future target contract는 문서로 닫혔지만, current repo에는 still no internal `reviewed_memory_applied_effect_target` helper implementation이라는 점이었습니다.
- 이 상태를 그대로 두면 next implementation이 current contract object, support-only trace, `task_log` replay를 target/backer처럼 잘못 읽을 위험이 남아 있었습니다.
- 그래서 이번 라운드는 payload-visible widening 없이 internal target helper만 가장 작게 추가하고, current repo에 truthful local effect-presence source가 아직 없으면 계속 absence를 유지하도록 고정해야 했습니다.

## 핵심 변경
- `app/web.py`
  - `_build_recurrence_aggregate_reviewed_memory_applied_effect_target(...)`를 추가했습니다.
  - helper는 same exact aggregate, exact supporting refs, current resolved `boundary_source_ref`, current unblock precondition chain까지 확인한 뒤에만 later local target을 평가합니다.
  - current repo에는 still no truthful local effect-presence source가 없으므로 helper는 계속 `None`을 반환합니다.
  - existing `reviewed_memory_reversible_effect_handle` helper는 이제 위 target helper를 probe하지만, same round에서는 계속 unresolved를 유지합니다.
- 회귀
  - ordinary aggregate에서 new target helper가 still absent인지 고정했습니다.
  - target helper가 absent이면 handle helper와 `rollback_source_ref`도 still unresolved인지 다시 확인했습니다.
  - support-only traces와 fake target input으로도 target/helper/backer/basis/status widening이 생기지 않음을 회귀로 추가했습니다.
- 문서
  - current implementation fact를 narrow sync 했습니다.
  - 이제 “target contract exists”가 아니라 “target helper exists but still resolves no result”가 current truth입니다.
  - next slice wording도 `one internal applied-effect target scaffold only`에서 `one real later local applied-effect-presence source implementation only`로 이동시켰습니다.

## 검증
- 실행: `python3 -m py_compile app/web.py storage/session_store.py core/agent_loop.py tests/test_smoke.py tests/test_web_app.py`
- 실행: `python3 -m unittest -v tests.test_smoke tests.test_web_app`
  - 결과: `169` tests passed
- 실행: `make e2e-test`
  - 결과: `12` tests passed
- 실행: `git diff --check`
- 실행: `rg -n "reviewed_memory_applied_effect_target|reviewed_memory_reversible_effect_handle|rollback_source_ref|disable_source_ref|reviewed_memory_capability_basis|unblocked_all_required|blocked_all_required|reviewed_memory_transition_record" app/web.py storage/session_store.py core/agent_loop.py tests/test_smoke.py tests/test_web_app.py docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md plandoc/2026-03-29-reviewed-memory-applied-effect-target-contract.md plandoc/2026-03-29-reviewed-memory-rollback-backer-contract.md plandoc/2026-03-29-reviewed-memory-capability-basis-source-contract.md`

## 남은 리스크
- 이전 closeout에서 이어받은 핵심 리스크:
  - current repo에는 `reviewed_memory_reversible_effect_handle` 아래의 exact local applied-effect target helper가 없었습니다.
- 이번 라운드에서 해소한 리스크:
  - internal `reviewed_memory_applied_effect_target` helper 자체는 코드에 생겼고, support-only traces나 fake input이 target/backer처럼 읽히는 경로를 막았습니다.
  - root docs와 `plandoc`의 next-slice wording도 helper-implemented-but-absent truth로 다시 맞췄습니다.
- 여전히 남은 리스크:
  - current repo에는 still no truthful local effect-presence source가 없습니다.
  - 그래서 `reviewed_memory_applied_effect_target` helper는 계속 absent, `reviewed_memory_reversible_effect_handle`는 계속 unresolved, `rollback_source_ref`도 계속 unresolved입니다.
  - full source family, `reviewed_memory_capability_basis`, `unblocked_all_required`, enabled trigger, emitted transition record, reviewed-memory apply result, repeated-signal promotion, cross-session counting, user-level memory는 계속 later layer입니다.
