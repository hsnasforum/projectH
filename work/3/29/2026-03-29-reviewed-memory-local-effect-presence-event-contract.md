# 2026-03-29 reviewed-memory local effect-presence event contract

## 변경 파일
- `docs/PRODUCT_SPEC.md`
- `docs/ARCHITECTURE.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`
- `docs/NEXT_STEPS.md`
- `plandoc/2026-03-29-reviewed-memory-local-effect-presence-event-contract.md`
- `plandoc/2026-03-29-reviewed-memory-applied-effect-presence-source-contract.md`
- `plandoc/2026-03-29-reviewed-memory-applied-effect-target-contract.md`
- `plandoc/2026-03-29-reviewed-memory-rollback-backer-contract.md`
- `plandoc/2026-03-29-reviewed-memory-capability-basis-source-contract.md`
- `plandoc/2026-03-29-reviewed-memory-unblocked-capability-path-contract.md`
- `work/3/29/2026-03-29-reviewed-memory-local-effect-presence-event-contract.md`

## 사용 skill
- `mvp-scope`: current shipped contract, next design target, 더 later layer 경계를 다시 분리했습니다.
- `doc-sync`: root docs와 `plandoc/`을 current helper chain truth에 맞춰 동기화했습니다.
- `release-check`: 이번 문서 라운드에서 실제 실행한 검증만 남기도록 정리했습니다.
- `work-log-closeout`: 이번 라운드 변경, 검증, 남은 리스크를 `/work` 형식으로 기록했습니다.

## 변경 이유
- 직전 closeout에서 이어받은 핵심 리스크는 `reviewed_memory_local_effect_presence_event_producer` helper는 이미 있지만, 그 helper가 later truthfully materialize할 exact local effect-presence event 자체가 아직 문서로 닫히지 않았다는 점이었습니다.
- 이 정의가 없으면 다음 구현이 current contracts, support-only traces, 혹은 `task_log` replay를 raw local event처럼 잘못 읽을 위험이 남아 있습니다.
- 그래서 이번 라운드에서는 제품 코드를 더 밀지 않고, producer helper 아래의 exact local event만 먼저 계약으로 고정했습니다.

## 핵심 변경
- new `plandoc/2026-03-29-reviewed-memory-local-effect-presence-event-contract.md`를 추가해 exact later local effect-presence event를 one shared internal `reviewed_memory_local_effect_presence_event`로 고정했습니다.
- minimum event shape를 다음으로 닫았습니다:
  - `event_version = first_same_session_reviewed_memory_local_effect_presence_event_v1`
  - `event_scope = same_session_exact_recurrence_aggregate_only`
  - `aggregate_identity_ref`
  - exact supporting refs
  - matching `boundary_source_ref`
  - `effect_target_kind = applied_reviewed_memory_effect`
  - `event_capability_boundary = local_effect_presence_only`
  - `event_stage = presence_observed_local_only`
  - local `applied_effect_id`
  - local `present_locally_at`
- local identity rule도 최소로 고정했습니다:
  - first contract에서는 separate event id를 열지 않습니다.
  - `applied_effect_id`를 first truthful local identity로 재사용합니다.
  - `present_locally_at`는 first truthful local instant만 허용하고, `aggregate.last_seen_at`는 정확히 그 instant일 때만 재사용할 수 있게 적었습니다.
- producer helper / event-source helper / source-consumer helper / target helper / handle helper / rollback resolver / basis / `unblocked_all_required` / emitted record / apply result를 다시 층별로 분리했습니다.
- shared-vs-rollback-first 판단은 shared event 쪽으로 닫았습니다.
  - rollback과 later disable은 same later applied reviewed-memory effect boundary를 가리키고,
  - capability semantics는 later handles와 matching contract refs에서 분리하는 편이 더 정직하기 때문입니다.
- root docs와 기존 `plandoc/`의 stale next-step wording도 현재 기준으로 다시 맞췄습니다.
  - previous wording: `one truthful same-aggregate local effect-presence event producer materialization only`
  - current wording: `one internal same-aggregate local effect-presence event scaffold only`
  - 이유: exact local event contract가 지금 막 닫혔고, producer helper materialization보다 더 작은 next step이 바로 그 raw local event scaffold이기 때문입니다.

## 검증
- 실행: `git diff --check`
- 실행: `rg -n "reviewed_memory_local_effect_presence_event_producer|reviewed_memory_local_effect_presence_event_source|reviewed_memory_local_effect_presence_record|reviewed_memory_applied_effect_target|reviewed_memory_reversible_effect_handle|rollback_source_ref|reviewed_memory_capability_basis|unblocked_all_required|blocked_all_required|reviewed_memory_transition_record" docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md app/web.py app/templates/index.html plandoc/2026-03-29-reviewed-memory-local-effect-presence-event-contract.md plandoc/2026-03-29-reviewed-memory-applied-effect-presence-source-contract.md plandoc/2026-03-29-reviewed-memory-applied-effect-target-contract.md plandoc/2026-03-29-reviewed-memory-rollback-backer-contract.md`
- 미실행:
  - `python3 -m py_compile ...`
  - `python3 -m unittest ...`
  - `make e2e-test`
  - 이유: 이번 라운드는 제품 코드 변경 없는 문서 계약 작업이기 때문입니다.

## 남은 리스크
- 이전 closeout에서 이어받은 리스크였던 “producer helper 아래의 exact local event 부재”는 계약 기준으로는 더 명확히 분리됐지만, actual local event implementation은 여전히 없습니다.
- 이번 라운드에서 해소한 것은 current helper chain이 consume해야 할 raw local event boundary를 producer helper와 분리해 명시한 점, 그리고 root docs / `plandoc` next-step wording을 그 기준으로 바로잡은 점입니다.
- 여전히 남은 리스크는 current repo에 `applied_effect_id`와 `present_locally_at`를 truthful 하게 mint할 real local event source가 없어서 producer helper, event-source helper, source-consumer helper, target helper, handle helper, `rollback_source_ref`가 전부 계속 absence / unresolved라는 점입니다.
- 다음 slice는 `one internal same-aggregate local effect-presence event scaffold only`가 가장 작습니다. producer helper materialization, event-source helper materialization, target helper, basis, `unblocked_all_required`, enabled trigger, emitted transition record, reviewed-memory apply result보다 먼저 raw local event를 여는 편이 현재 repo 상태에 더 정직합니다.
