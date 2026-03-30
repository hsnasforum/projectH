## 변경 파일
- `docs/PRODUCT_SPEC.md`
- `docs/ARCHITECTURE.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`
- `docs/NEXT_STEPS.md`
- `plandoc/2026-03-28-post-aggregate-promotion-boundary.md`

## 사용 skill
- `mvp-scope`
- `approval-flow-audit`
- `doc-sync`
- `release-check`
- `work-log-closeout`

## 변경 이유
- 직전 closeout에서 same-session `recurrence_aggregate_candidates`는 이미 shipped 되었지만, 그 aggregate 위에서 어디까지를 promotion candidate로 볼지와 future reviewed-memory와의 경계가 아직 문서로 닫혀 있지 않았습니다.
- 이 경계가 없으면 repeated-signal promotion, broader durable promotion, cross-session counting을 구현된 것처럼 과장해서 여는 위험이 컸습니다.
- current repo는 여전히 로컬 퍼스트 문서 비서 웹 MVP이므로, aggregate 이후 경계를 reviewed-memory / rollback / audit 전제보다 앞서 넓히지 않는 보수 계약이 필요했습니다.

## 핵심 변경
- current same-session `recurrence_aggregate_candidates`는 모두 promotion-ineligible이라는 `Option A`를 문서로 고정했습니다.
- post-aggregate boundary는 현재 emitted object가 없는 eligibility-only contract로 정리했고, future first slice는 `promotion_basis = same_session_exact_recurrence_aggregate`, `promotion_eligibility = blocked_pending_reviewed_memory_boundary`, `reviewed_memory_boundary = not_open`를 갖는 read-only aggregate-level marker only로 추천했습니다.
- `candidate_review_record`, `durable_candidate`, `candidate_recurrence_key`, `recurrence_aggregate_candidates`, future reviewed memory의 경계를 다시 분리했습니다.
- review acceptance, approval-backed save, `session_local_memory_signal`, `superseded_reject_signal`, `historical_save_identity_signal`, queue presence, fixed statement, task-log replay는 post-aggregate promotion identity basis가 아니라는 점을 다시 고정했습니다.
- next implementation priority를 “aggregate-level promotion-eligibility marker only”로 좁혀서 repeated-signal promotion, reviewed-memory store, cross-session counting보다 먼저 오도록 문서를 맞췄습니다.

## 검증
- `git diff --check`
- `rg -n "post-aggregate promotion|reviewed-memory|repeated-signal promotion|recurrence_aggregate_candidates|candidate_review_record|confidence_marker|cross-session" docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md README.md plandoc/2026-03-28-post-aggregate-promotion-boundary.md`

## 남은 리스크
- 이전 closeout에서 이어받은 리스크:
  - same-session aggregate는 shipped 되었지만 aggregate 위 promotion / reviewed-memory boundary가 없어 repeated-signal promotion이나 broader durable promotion을 과장해서 열 위험이 있었습니다.
- 이번 라운드에서 해소한 리스크:
  - current aggregate가 promotion-ineligible이라는 점과 reviewed-memory / cross-session counting이 아직 닫혀 있다는 점을 문서 계약으로 고정했습니다.
  - future first post-aggregate slice를 read-only marker only로 좁혀 next implementation order를 정직하게 맞췄습니다.
- 여전히 남은 리스크:
  - rollback / disable / conflict / operator-audit precondition의 정확한 shape는 아직 미정입니다.
  - cross-session counting을 열 local store / reviewed-memory precondition도 아직 미정입니다.
  - `confidence_marker = same_session_exact_key_match` 위에 later second conservative level이 필요한지 여부는 여전히 open question입니다.
