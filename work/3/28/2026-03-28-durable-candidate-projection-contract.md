# 2026-03-28 durable-candidate projection contract

## 변경 파일
- `docs/PRODUCT_SPEC.md`
- `docs/ARCHITECTURE.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`
- `docs/NEXT_STEPS.md`
- `plandoc/2026-03-28-durable-candidate-promotion-guardrail.md`
- `plandoc/2026-03-28-durable-candidate-projection-contract.md`
- `work/3/28/2026-03-28-durable-candidate-projection-contract.md`

## 사용 skill
- `mvp-scope`: shipped `session_local_candidate`, `candidate_confirmation_record`, future `durable_candidate`, review queue, user-level memory 경계를 현재 MVP 기준으로 다시 좁혔습니다.
- `approval-flow-audit`: approval-backed save가 future promotion basis로 오해되지 않도록 supporting-only 경계를 다시 고정했습니다.
- `doc-sync`: spec / architecture / acceptance / milestones / backlog / next-steps / plandoc 문구를 같은 projection 계약으로 동기화했습니다.
- `release-check`: 실제 실행한 `git diff --check`, `rg`, `git status --short` 결과만 기준으로 검증 상태를 정리했습니다.
- `work-log-closeout`: 이번 문서 round의 변경 파일, 검증, 남은 리스크를 `/work` 형식으로 남겼습니다.

## 변경 이유
- `2026-03-28-session-local-candidate-explicit-confirmation`과 `2026-03-28-durable-candidate-promotion-guardrail` closeout에서 이어받은 핵심 리스크는 shipped `candidate_confirmation_record`를 future `durable_candidate`가 어떤 최소 계약으로 소비할지, 그리고 그 projection의 canonical source / first materialization surface가 아직 문서로 닫히지 않았다는 점이었습니다.
- current repo는 이미 same-source-message `session_local_candidate`와 `candidate_confirmation_record`를 shipped truth로 갖고 있으므로, 이번 라운드에서는 제품 코드를 건드리지 않고 first future `durable_candidate` projection contract만 문서로 고정해야 했습니다.

## 핵심 변경
- first future `durable_candidate`를 same source message에서 계산되는 later optional projection으로 고정했습니다.
  - first materialization surface는 serialized grounded-brief source message only
  - review queue item이나 separate store를 먼저 열지 않음
  - canonical source는 current persisted session state이며 task-log는 audit-only
- minimum projection shape를 1개 contract로 고정했습니다.
  - `candidate_scope = durable_candidate`
  - `candidate_family`, `statement`, `supporting_artifact_ids`, `supporting_source_message_ids`, `supporting_signal_refs`
  - `supporting_confirmation_refs`
  - `evidence_strength`, `has_explicit_confirmation`, `promotion_basis`, `promotion_eligibility`
  - timestamps
- explicit pair / explicit confirmation / approval-backed save / historical adjunct 역할을 다시 분리했습니다.
  - explicit original-vs-corrected pair는 current source-message candidate draft basis only
  - `candidate_confirmation_record`는 first future promotion basis candidate
  - approval-backed save는 supporting evidence only
  - `session_local_memory_signal`, `superseded_reject_signal`, `historical_save_identity_signal`은 context only
- next implementation slice 권고를 갱신했습니다.
  - explicit confirmation surface를 더 만드는 대신
  - 이미 shipped 된 `candidate_confirmation_record`를 소비하는 source-message-anchored read-only `durable_candidate` projection 구현을 다음 한 조각으로 추천하도록 바꿨습니다.
- 이전 closeout에서 남아 있던 “projection contract와 source contract가 아직 흐리다”는 리스크는 이번 라운드에서 줄였습니다.
  - 반면 repeated-signal recurrence key와 future durable-scope `candidate_id` rule은 여전히 open question으로 남겼습니다.

## 검증
- 실행함: `git diff --check`
- 실행함: `rg -n "durable_candidate|candidate_confirmation_record|promotion_basis|promotion_eligibility|has_explicit_confirmation|session_local_candidate|historical_save_identity_signal|superseded_reject_signal|approval-backed save" docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md README.md plandoc/2026-03-28-durable-candidate-projection-contract.md`
- 실행함: `git status --short`
- 미실행: 제품 코드 테스트

## 남은 리스크
- 이전 closeout에서 이어받은 “future `durable_candidate` projection contract가 아직 미정” 리스크는 이번 라운드에서 minimum shape, basis boundary, source contract를 문서로 고정하면서 줄였습니다.
- 이번 라운드에서 새로 해소한 리스크는 approval-backed save, historical adjunct, same-family repetition이 promotion shortcut처럼 읽히는 혼동입니다.
- 여전히 남은 리스크는 first explicit-confirmation projection이 future durable-scope `candidate_id`를 어떻게 잡을지 아직 구현 규칙이 없다는 점입니다.
- repeated-signal promotion을 위한 truthful recurrence key도 여전히 open question이며, 그 전까지 merge helper reopen이나 repeated-signal durable promotion은 닫혀 있어야 합니다.
- 이번 라운드는 문서 작업만 수행했으므로, 다음 구현 라운드에서는 source-message-anchored projection helper와 focused service/web-app regression으로 계약을 실제 payload에 좁게 반영하는 검증이 필요합니다.
