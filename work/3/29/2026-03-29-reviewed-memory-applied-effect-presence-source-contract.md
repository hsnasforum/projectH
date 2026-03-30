# 2026-03-29 reviewed-memory applied-effect-presence source contract

## 변경 파일
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
- `work/3/29/2026-03-29-reviewed-memory-applied-effect-presence-source-contract.md`

## 사용 skill
- `mvp-scope`: current blocked contract chain, current internal helper layers, future local effect-presence source, later basis/emission/apply layers를 다시 분리하고 이번 문서 범위를 source-contract-only로 제한했습니다.
- `doc-sync`: current implementation truth에 맞춰 root docs와 `plandoc`의 next-slice wording을 sync 했습니다.
- `release-check`: 실제 실행한 `git diff --check`와 `rg`만 기준으로 closeout을 정리했습니다.
- `work-log-closeout`: 저장소 `/work` 형식에 맞춰 이번 설계 라운드의 변경과 남은 리스크를 기록했습니다.

## 변경 이유
- 이전 closeout에서 이어받은 핵심 리스크는 internal `reviewed_memory_applied_effect_target` helper는 이미 구현됐지만, 그 helper가 truthfully materialize할 exact local effect-presence source가 아직 정의되지 않았다는 점이었습니다.
- 이 정의가 열려 있으면 다음 구현이 current contracts, support-only traces, review acceptance, 또는 `task_log` replay를 source처럼 잘못 읽을 위험이 남아 있었습니다.
- 또한 root docs와 `plandoc`의 next-slice wording은 “effect-presence source 구현” 수준까지만 말하고 있어서, 이번 라운드에서는 exact source 이름과 shape를 먼저 고정할 필요가 있었습니다.

## 핵심 변경
- exact local effect-presence source를 one shared internal `reviewed_memory_local_effect_presence_record`로 고정했습니다.
- 최소 contract shape를 아래로 정리했습니다.
  - `source_version = first_same_session_reviewed_memory_local_effect_presence_record_v1`
  - `source_scope = same_session_exact_recurrence_aggregate_only`
  - `aggregate_identity_ref`
  - exact supporting refs
  - matching `boundary_source_ref`
  - `effect_target_kind = applied_reviewed_memory_effect`
  - `source_capability_boundary = local_effect_presence_only`
  - `source_stage = presence_recorded_local_only`
  - local `applied_effect_id`
  - local `present_locally_at`
- current layer boundaries도 다시 고정했습니다.
  - rollback / disable contracts: still contract-only
  - `rollback_source_ref`: exact-scope-validated but unresolved
  - `reviewed_memory_applied_effect_target` helper: exists but absent
  - `reviewed_memory_reversible_effect_handle` helper: exists but unresolved
  - future local effect-presence source: exact later local source only
  - future target materialization / full source family / basis / `unblocked_all_required` / emitted record / apply result: all later
- shared-source vs rollback-first question도 닫았습니다.
  - source는 rollback-only가 아니라 shared source가 더 정직합니다.
  - 이유는 shipped `reviewed_memory_rollback_contract`와 `reviewed_memory_disable_contract`가 모두 `future_applied_reviewed_memory_effect_only`를 가리키고, capability meaning은 later handles에서 분리하는 편이 더 정확하기 때문입니다.
- next-slice wording을 repo 전반에서 다시 맞췄습니다.
  - 기존 “one real later local applied-effect-presence source implementation only”를
  - “one internal `reviewed_memory_local_effect_presence_record` scaffold only”로 좁혔습니다.

## 검증
- 실행: `git diff --check`
- 실행: `rg -n "reviewed_memory_applied_effect_target|local effect-presence source|reviewed_memory_reversible_effect_handle|rollback_source_ref|disable_source_ref|reviewed_memory_capability_basis|unblocked_all_required|blocked_all_required|reviewed_memory_transition_record" docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md app/web.py app/templates/index.html plandoc/2026-03-29-reviewed-memory-applied-effect-presence-source-contract.md plandoc/2026-03-29-reviewed-memory-applied-effect-target-contract.md plandoc/2026-03-29-reviewed-memory-rollback-backer-contract.md`
- 실행하지 않음: `python3 -m py_compile ...`, `python3 -m unittest ...`, `make e2e-test`
- 미실행 이유: 이번 라운드는 제품 코드 변경 없는 문서 계약 작업이었기 때문입니다.

## 남은 리스크
- 이전 closeout에서 이어받은 리스크:
  - target helper는 now implemented, but the repo still lacked an exact truthful local effect-presence source beneath it.
- 이번 라운드에서 해소한 리스크:
  - next implementation이 generic “effect presence”를 임의 object로 해석하는 대신, one exact shared internal source contract만 따르도록 경계를 닫았습니다.
  - root docs와 `plandoc`의 next-slice wording도 current implementation truth 기준으로 다시 맞췄습니다.
- 여전히 남은 리스크:
  - current repo에는 `reviewed_memory_local_effect_presence_record` implementation이 아직 없습니다.
  - 그래서 `reviewed_memory_applied_effect_target` helper는 계속 absent, `reviewed_memory_reversible_effect_handle` helper는 계속 unresolved, `rollback_source_ref`도 계속 unresolved입니다.
  - full source family, `reviewed_memory_capability_basis`, `unblocked_all_required`, enabled trigger, emitted transition record, reviewed-memory apply result, repeated-signal promotion, cross-session counting, user-level memory는 계속 later layer입니다.
