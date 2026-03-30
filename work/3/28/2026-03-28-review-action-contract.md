# 2026-03-28 review action contract

## 변경 파일
- `docs/PRODUCT_SPEC.md`
- `docs/ARCHITECTURE.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`
- `docs/NEXT_STEPS.md`
- `plandoc/2026-03-28-review-action-contract.md`
- `work/3/28/2026-03-28-review-action-contract.md`

## 사용 skill
- `mvp-scope`: current shipped queue, next review-action layer, later reviewed memory / user-level memory를 다시 분리해 current MVP 범위로 좁혔습니다.
- `doc-sync`: root docs 6개와 새 plandoc을 같은 review-action contract wording으로 맞췄습니다.
- `release-check`: `git diff --check`, `rg`, `git status --short`, targeted `git diff`만 실제 실행 결과 기준으로 정리했습니다.
- `work-log-closeout`: 이번 문서 round의 변경 파일, 검증, 남은 리스크를 `/work` 표준 형식으로 남겼습니다.

## 변경 이유
- 직전 closeout `2026-03-28-durable-candidate-review-queue-implementation.md`에서 이어받은 핵심 리스크는 shipped queue가 읽기 전용 inspection surface에 머물고 있고, first review action이 어떤 canonical source와 어떤 최소 trace를 써야 하는지 아직 문서로 닫히지 않았다는 점이었습니다.
- 특히 `durable_candidate` / `review_queue_items` / later reviewed outcome / later user-level memory 경계가 흐리면, current queue를 너무 빨리 wider operator surface처럼 읽게 되는 confusion risk가 컸습니다.
- 이번 라운드는 제품 코드를 건드리지 않고, shipped read-only queue 위의 first review-action contract만 가장 작은 source-message-anchored trace로 고정하는 문서 작업이었습니다.

## 핵심 변경
- root docs와 새 plandoc에 first review-outcome trace를 `candidate_review_record` 1개로 고정했습니다.
  - same source message anchor
  - same `artifact_id`
  - same `source_message_id`
  - same `candidate_id`
  - same `candidate_updated_at`
  - `review_scope = source_message_candidate_review`
  - `review_action = accept | edit | reject | defer`
  - `review_status = accepted | edited | rejected | deferred`
  - optional `reviewed_statement` only for later `edit`
- `accept`, `edit`, `reject`, `defer`의 의미를 current content verdict / approval reject / no-save / retry / feedback incorrect 와 섞이지 않게 다시 고정했습니다.
  - `accept` is reviewed-but-not-applied
  - `edit` is reviewed statement change, not source corrected-text rewrite
  - `reject` is review dismissal, not content reject
  - `defer` is later revisit, not candidate-basis invalidation
- queue transition contract를 좁게 고정했습니다.
  - pending `review_queue_items`는 current `durable_candidate` + `eligible_for_review` + no matching current `candidate_review_record`일 때만 남습니다
  - matching review record가 생기면 item은 current pending queue에서 빠집니다
  - accepted / edited / rejected / deferred 전용 새 탭이나 dashboard는 이번 contract에 넣지 않았습니다
- next implementation slice를 1개로 추천했습니다.
  - `accept` only
  - source-message `candidate_review_record` 기록
  - pending queue removal
  - reviewed-but-not-applied 유지
  - user-level memory / scope suggestion / second store는 계속 닫힘

## 검증
- `git diff --check`
- `rg -n "review_queue|durable_candidate|candidate_confirmation_record|reviewed memory|eligible_for_review|approval-backed save|candidate_family|candidate_review_record|review_action|review_status" docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md README.md plandoc/2026-03-28-review-action-contract.md`
- `git status --short`
- `git diff -- docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md plandoc/2026-03-28-review-action-contract.md`

## 남은 리스크
- 이전 closeout에서 남아 있던 “queue는 읽기만 가능하고 review action contract가 없다”는 리스크는 이번 라운드에서 줄였습니다.
- 이번 라운드에서 새로 해소한 리스크는 reviewed outcome이 곧 user-level memory apply처럼 읽히는 혼동입니다. 현재 contract는 reviewed-but-not-applied를 분리해 고정합니다.
- 여전히 남은 리스크는 actioned item을 current shell 어디까지 다시 보여 줄지 아직 open question이라는 점입니다. 지금 contract는 source-message anchor만 canonical로 남기고 별도 history surface는 later로 미뤘습니다.
- `durable_candidate`가 later source-message surface를 벗어날 때 `candidate_id` 경계를 어떻게 다시 잡을지도 여전히 open question입니다.
- repeated-signal promotion, rollback, reviewed-memory store, user-level memory, broader operator surface는 여전히 미구현이며 이번 라운드에서도 닫힌 상태를 유지해야 합니다.
