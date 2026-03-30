# 2026-03-28 post-key-aggregation-boundary-contract

## 변경 파일
- `docs/PRODUCT_SPEC.md`
- `docs/ARCHITECTURE.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`
- `docs/NEXT_STEPS.md`
- `plandoc/2026-03-28-recurrence-key-contract.md`
- `plandoc/2026-03-28-post-key-aggregation-boundary.md`
- `work/3/28/2026-03-28-post-key-aggregation-boundary-contract.md`

## 사용 skill
- `mvp-scope`: shipped recurrence key 다음에 올 first aggregation boundary를 현재 MVP/다음 단계/장기 북극성 구분 안에서 다시 좁혔습니다.
- `approval-flow-audit`: approval-backed save와 review acceptance를 aggregation identity basis에서 제외하고 supporting-only 경계를 문서로 고정했습니다.
- `doc-sync`: root docs와 `plandoc`에서 source-message candidate, durable projection, review trace, recurrence key, future aggregation layer 경계를 같은 문장으로 맞췄습니다.
- `release-check`: 실제 실행한 `git diff --check`와 `rg` 결과만 기준으로 handoff 상태를 정리합니다.
- `work-log-closeout`: 저장소 규칙에 맞는 `/work` closeout 형식으로 이번 라운드 결정과 남은 리스크를 남깁니다.

## 변경 이유
- 직전 closeout `2026-03-28-candidate-recurrence-key-draft-implementation.md`에서 이어받은 핵심 리스크는 truthful recurrence primitive는 생겼지만, post-key aggregation boundary가 아직 없어서 same-family merge, repeated-signal promotion, broader durable promotion을 과장해서 열 수 있다는 점이었습니다.
- 이번 라운드에서는 제품 코드를 건드리지 않고, first aggregation이 무엇을 basis로 삼고 무엇을 basis로 삼지 말아야 하는지 문서 계약으로 먼저 닫을 필요가 있었습니다.

## 핵심 변경
- first post-key aggregation boundary를 same-session only로 고정했습니다.
  - first aggregation unit은 같은 세션 안의 서로 다른 grounded-brief source-message anchors가 같은 exact `candidate_recurrence_key` identity를 보일 때만 성립합니다.
  - first materialization surface는 future top-level read-only `recurrence_aggregate_candidates` projection으로 정리했습니다.
- current source-message candidate / durable projection / review trace / recurrence key / future aggregation layer 경계를 다시 분리했습니다.
  - `session_local_candidate`, `durable_candidate`, `candidate_review_record`, `review_queue_items`, `candidate_recurrence_key`는 current truth로 유지됩니다.
  - future aggregation layer는 source-message fields를 덮어쓰지 않고, second canonical store도 만들지 않는 later computed projection으로 고정했습니다.
- basis / supporting / never-basis 경계를 문서로 고정했습니다.
  - basis는 same exact recurrence key identity + distinct source-message anchors입니다.
  - `candidate_review_record`와 `durable_candidate`는 같은 candidate version에 매달릴 때만 confidence support로만 쓸 수 있게 했습니다.
  - approval-backed save, `session_local_memory_signal`, `superseded_reject_signal`, `historical_save_identity_signal`, queue presence, fixed statement, `candidate_family` alone, task-log replay alone은 basis에서 제외했습니다.
- next implementation slice를 1개로 추천했습니다.
  - same-session-only read-only `recurrence_aggregate_candidates` projection with no promotion
  - `edit` / `reject` / `defer`, reviewed-history hint, repeated-signal promotion, cross-session counting은 그 뒤로 미뤘습니다.
- 기존 `plandoc/2026-03-28-recurrence-key-contract.md`의 same-session vs cross-session open question도 새 boundary 결정에 맞게 최소 동기화했습니다.

## 검증
- 실행:
  - `git diff --check`
  - `rg -n "candidate_recurrence_key|post-key aggregation|aggregation boundary|repeated-signal promotion|candidate_review_record|review_queue_items|approval-backed save" docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md README.md plandoc/2026-03-28-post-key-aggregation-boundary.md`
- 결과:
  - `git diff --check`: 통과
  - `rg`: 관련 문구가 수정 대상 문서에 반영된 것을 확인

## 남은 리스크
- 이전 closeout에서 이어받은 리스크:
  - truthful recurrence primitive는 생겼지만, first aggregation unit과 session/cross-session boundary가 열려 있어서 후속 promotion work를 과장할 수 있었습니다.
- 이번 라운드에서 해소한 리스크:
  - first aggregation boundary를 same-session-only read-only projection으로 고정했고, basis/supporting/never-basis 경계를 문서로 닫았습니다.
  - approval-backed save, historical adjunct, review acceptance가 recurrence aggregation identity를 대체하지 못하도록 문서 계약을 정리했습니다.
- 여전히 남은 리스크:
  - `recurrence_aggregate_candidates` 자체는 아직 미구현입니다.
  - cross-session aggregation을 열기 위한 local store / rollback / conflict / reviewed-memory precondition은 아직 후속 설계가 필요합니다.
  - first aggregate `confidence_marker` vocabulary와 category별 threshold tuning은 아직 open question입니다.
