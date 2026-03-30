# 2026-03-29 reviewed-memory apply trigger-source contract

## 변경 파일
- `docs/PRODUCT_SPEC.md`
- `docs/ARCHITECTURE.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`
- `docs/NEXT_STEPS.md`
- `plandoc/2026-03-29-reviewed-memory-apply-trigger-source-contract.md`
- `work/3/29/2026-03-29-reviewed-memory-apply-trigger-source-contract.md`

## 사용 skill
- `mvp-scope`: current shipped contract, next phase design target, later reviewed-memory/apply/user-memory 층위를 다시 분리했습니다.
- `approval-flow-audit`: approval-backed save, historical adjunct, review acceptance, `task_log`가 trigger-source나 canonical transition state로 오해되지 않도록 경계를 점검했습니다.
- `doc-sync`: root docs와 새 `plandoc`를 current implementation truth와 같은 wording으로 맞췄습니다.
- `release-check`: 실제 실행한 `git diff --check`와 `rg` 결과만 기준으로 문서 라운드를 닫았습니다.
- `work-log-closeout`: 저장소 규칙에 맞는 `/work` closeout 형식으로 이번 계약 정리와 남은 리스크를 기록했습니다.

## 변경 이유
- 직전 closeout에서 absence-preserving `reviewed_memory_transition_record` helper는 이미 들어갔지만, first operator-visible `future_reviewed_memory_apply` trigger source가 정확히 어디에 어떤 UX/API/payload 경계로 존재해야 하는지는 아직 exact contract가 없었습니다.
- 이 질문이 열린 채로 다음 구현을 진행하면 `review_queue_items`와 aggregate-level reviewed-memory transition, `candidate_review_record`와 emitted transition record, `task_log` mirror와 canonical state를 섞을 위험이 남아 있었습니다.

## 핵심 변경
- first operator-visible `future_reviewed_memory_apply` trigger source 위치를 `Option A`로 고정했습니다:
  - `review_queue_items`가 아니라 `recurrence_aggregate_candidates` 전용 separate aggregate-level surface
  - existing shell session stack 안에서 `검토 후보`와 분리된 section/card
  - source-message review와 aggregate-level transition initiation을 명시적으로 분리
- blocked 표현은 `hidden`이 아니라 `operator-visible but disabled`로 고정했습니다:
  - future aggregate card에 `검토 메모 적용 시작` action label을 두되
  - current `blocked_all_required` / `contract_only_not_emitted` truth가 유지되는 동안은 disabled
  - blocked 상태에서는 `operator_reason_or_note`, `canonical_transition_id`, `emitted_at`를 만들지 않음
- current layer boundary를 네 단계로 다시 고정했습니다:
  - `transition-audit contract exists`
  - `operator-visible trigger-source layer exists`
  - `transition record emitted`
  - `reviewed-memory apply result`
- `review_queue_items` / `candidate_review_record` / approval-backed save / historical adjunct / `task_log` 역할을 다시 분리했습니다:
  - `review_queue_items`와 `candidate_review_record`는 여전히 source-message review only
  - approval-backed save와 historical adjunct는 supporting evidence only
  - `task_log`는 mirror / appendix only이며 canonical state source가 아님
- next slice를 하나로 좁혔습니다:
  - one separate aggregate-level blocked-but-visible disabled trigger affordance only
  - current repo에 truthful `unblocked_all_required` path가 아직 없으므로 enabled trigger나 emitted record 구현보다 먼저 UI boundary를 드러내는 편이 더 정직하다고 문서로 고정

## 검증
- `git diff --check`
- `rg -n "future_reviewed_memory_apply|reviewed_memory_transition_record|reviewed_memory_transition_audit_contract|review_queue_items|candidate_review_record|operator_reason_or_note|canonical_transition_id" docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md app/templates/index.html app/web.py plandoc/2026-03-29-reviewed-memory-apply-trigger-source-contract.md plandoc/2026-03-29-reviewed-memory-transition-record-materialization-contract.md`

## 남은 리스크
- 이전 closeout에서 이어받은 핵심 리스크:
  - absence-preserving helper와 회귀는 들어갔지만, operator-visible `future_reviewed_memory_apply` trigger source의 exact boundary가 없어서 다음 구현이 `review_queue_items`와 aggregate-level transition을 섞을 수 있었습니다.
- 이번 라운드에서 해소한 리스크:
  - trigger source를 separate aggregate-level surface로 고정했고, blocked 상태에서는 visible-but-disabled로 보여야 한다는 점을 문서로 닫았습니다.
  - `review_queue_items`, `candidate_review_record`, approval-backed save, historical adjunct, `task_log`가 trigger source나 emitted record basis처럼 읽히는 경로를 줄였습니다.
- 여전히 남은 리스크:
  - current shell에는 아직 aggregate-level section/card 자체가 없습니다.
  - truthful `unblocked_all_required` path가 아직 없어 enabled trigger, emitted transition record, reviewed-memory apply result는 계속 미구현입니다.
  - cross-session counting, repeated-signal promotion, reviewed-memory store, user-level memory는 계속 later layer입니다.
