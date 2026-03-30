## 변경 파일
- `docs/PRODUCT_SPEC.md`
- `docs/ARCHITECTURE.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`
- `docs/NEXT_STEPS.md`
- `plandoc/2026-03-29-reviewed-memory-local-effect-presence-fact-source-contract.md`
- `plandoc/2026-03-29-reviewed-memory-local-effect-presence-event-contract.md`
- `plandoc/2026-03-29-reviewed-memory-applied-effect-presence-source-contract.md`
- `plandoc/2026-03-29-reviewed-memory-applied-effect-target-contract.md`
- `plandoc/2026-03-29-reviewed-memory-rollback-backer-contract.md`
- `plandoc/2026-03-29-reviewed-memory-capability-basis-source-contract.md`
- `plandoc/2026-03-29-reviewed-memory-unblocked-capability-path-contract.md`
- `work/3/29/2026-03-29-reviewed-memory-local-effect-presence-fact-source-contract.md`

## 사용 skill
- `mvp-scope`
- `doc-sync`
- `release-check`
- `work-log-closeout`

## 변경 이유
- 직전 closeout인 `2026-03-29-reviewed-memory-local-effect-presence-event-helper-implementation.md`까지는 internal `reviewed_memory_local_effect_presence_event` helper가 이미 코드에 들어갔지만, 그 helper가 truthfully materialize할 exact later local fact source가 아직 정의되지 않았습니다.
- 이 리스크가 남아 있으면 다음 구현 라운드가 current contracts, blocked affordance, approval-backed save support, historical adjunct, `task_log` replay를 잘못 raw local fact처럼 읽을 위험이 있었습니다.
- 그래서 이번 라운드는 제품 코드를 더 밀지 않고, raw-event helper 아래의 exact local fact source contract와 next-slice wording을 문서로 먼저 닫았습니다.

## 핵심 변경
- new shared internal `reviewed_memory_local_effect_presence_fact_source` contract를 `plandoc/2026-03-29-reviewed-memory-local-effect-presence-fact-source-contract.md`에 추가했습니다.
- exact shape를 `fact_source_version = first_same_session_reviewed_memory_local_effect_presence_fact_source_v1`, `fact_source_scope = same_session_exact_recurrence_aggregate_only`, exact aggregate identity ref, exact supporting refs, matching `boundary_source_ref`, `effect_target_kind = applied_reviewed_memory_effect`, `fact_capability_boundary = local_effect_presence_only`, `fact_stage = presence_fact_available_local_only`, local `applied_effect_id`, local `present_locally_at`로 고정했습니다.
- current helper chain을 다시 분리했습니다.
  - current raw-event helper `reviewed_memory_local_effect_presence_event` exists but absent
  - current producer helper `reviewed_memory_local_effect_presence_event_producer` exists but absent
  - current event-source helper `reviewed_memory_local_effect_presence_event_source` exists but absent
  - current source-consumer helper `reviewed_memory_local_effect_presence_record` exists but absent
  - current target helper `reviewed_memory_applied_effect_target` exists but absent
  - current handle helper `reviewed_memory_reversible_effect_handle` exists but unresolved
  - future local fact source stays below all of those helper results
- root docs와 related `plandoc/`의 current-truth wording을 `raw local fact`가 아니라 `local fact source` 기준으로 다시 맞췄습니다.
- next slice recommendation도 `one truthful same-aggregate local effect-presence event materialization only`에서 `one internal same-aggregate local fact-source scaffold only`로 한 단계 더 아래로 내렸습니다.
- previous risk 해소:
  - raw-event helper 아래의 exact missing layer가 무엇인지 문서로 고정했습니다.
  - next implementation slice가 producer/event-source/target/basis 쪽으로 잘못 widen되는 리스크를 줄였습니다.

## 검증
- 실행:
  - `git diff --check`
  - `rg -n "reviewed_memory_local_effect_presence_event\\b|reviewed_memory_local_effect_presence_event_producer|reviewed_memory_local_effect_presence_event_source|reviewed_memory_local_effect_presence_record|reviewed_memory_applied_effect_target|reviewed_memory_reversible_effect_handle|rollback_source_ref|reviewed_memory_capability_basis|unblocked_all_required|blocked_all_required|reviewed_memory_transition_record" docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md app/web.py app/templates/index.html plandoc/2026-03-29-reviewed-memory-local-effect-presence-fact-source-contract.md plandoc/2026-03-29-reviewed-memory-local-effect-presence-event-contract.md plandoc/2026-03-29-reviewed-memory-applied-effect-presence-source-contract.md plandoc/2026-03-29-reviewed-memory-applied-effect-target-contract.md plandoc/2026-03-29-reviewed-memory-rollback-backer-contract.md"`
- 미실행:
  - 없음

## 남은 리스크
- current repo에는 still no truthful `reviewed_memory_local_effect_presence_fact_source` instance가 있어서 raw-event helper와 그 위 helper chain은 계속 absence/unresolved입니다.
- exact future fact source contract는 닫혔지만, 어떤 later local boundary가 first `applied_effect_id`와 `present_locally_at`를 mint할지는 아직 open question입니다.
- next code slice에서도 fake local fact source invention 없이 same-session exact aggregate scope를 유지해야 하고, producer helper, event-source helper, target helper, `reviewed_memory_capability_basis`, `unblocked_all_required`, enabled trigger, emitted record를 동시에 열지 않도록 계속 좁게 제어해야 합니다.
