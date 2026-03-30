# 2026-03-28 durable-candidate promotion guardrail

## 변경 파일
- `docs/PRODUCT_SPEC.md`
- `docs/ARCHITECTURE.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`
- `docs/NEXT_STEPS.md`
- `plandoc/2026-03-28-durable-candidate-promotion-guardrail.md`
- `work/3/28/2026-03-28-durable-candidate-promotion-guardrail.md`

## 사용 skill
- `mvp-scope`: shipped `session_local_candidate`, future `durable_candidate`, review queue, user-level memory 경계를 현재 MVP 기준으로 다시 좁혔습니다.
- `approval-flow-audit`: approval-backed save가 promotion basis로 오해되지 않도록 supporting-only 경계를 다시 고정했습니다.
- `doc-sync`: spec / architecture / acceptance / milestone / backlog / next steps / plandoc 문구를 같은 guardrail 계약으로 맞췄습니다.
- `release-check`: 실제 실행한 `git diff --check`와 키워드 검색만 기준으로 검증 상태를 정리했습니다.
- `work-log-closeout`: 이번 문서 round의 변경 파일, 검증, 남은 리스크를 `/work` 형식으로 남겼습니다.

## 변경 이유
- `2026-03-28-session-local-candidate-merge-helper-decision` closeout에서 merge helper는 닫혔지만, shipped `session_local_candidate`가 future `durable_candidate`로 언제부터 갈 수 있는지 최소 계약은 아직 남아 있었습니다.
- `2026-03-28-session-local-candidate-draft-implementation` closeout에서 current candidate semantics는 이미 shipped truth로 고정됐기 때문에, 이번 라운드는 그 semantics를 흔들지 않고 promotion guardrail만 문서로 닫아야 했습니다.
- current docs 일부는 repeated signal 또는 explicit confirmation을 later basis로 언급하면서도, current shipped draft가 아직 promotion-ineligible이라는 경계를 충분히 선명하게 못 박지 못하고 있었습니다.

## 핵심 변경
- `Option A`로 고정했습니다.
  - current shipped `correction_rewrite_preference` `session_local_candidate` drafts는 아직 promotion-ineligible입니다.
  - future explicit confirmation surface 또는 truthful recurrence key가 생기기 전에는 `durable_candidate`가 될 수 없다고 문서화했습니다.
- promotion basis boundary를 다시 좁혔습니다.
  - explicit original-vs-corrected pair는 same source message의 explicit pair로만 정의했습니다.
  - repeated signal은 future pair-derived recurrence key가 있을 때만 truthful basis가 될 수 있게 했습니다.
  - approval-backed save, `historical_save_identity_signal`, `superseded_reject_signal`, task-log replay는 supporting-only 또는 context-only로 못 박았습니다.
- future minimum `durable_candidate` contract를 1개 shape로 고정했습니다.
  - `promotion_basis`
  - `promotion_eligibility`
  - `has_explicit_confirmation`
  - supporting refs / timestamps
  - suggested scope는 review queue layer 전까지 열지 않도록 정리했습니다.
- roadmap과 next-step 권고를 바꿨습니다.
  - merge helper보다 먼저, candidate-linked explicit confirmation surface 또는 trace를 next implementation slice로 추천하도록 맞췄습니다.
  - repeated-signal promotion, review queue, user-level memory는 later layer로 남겼습니다.
- 새 설계 문서 `plandoc/2026-03-28-durable-candidate-promotion-guardrail.md`를 추가해 이유, boundary, risk, next slice를 한 장으로 정리했습니다.

## 검증
- `git diff --check`
- `rg -n "durable_candidate|promotion guardrail|promotion_basis|promotion_eligibility|has_explicit_confirmation|session_local_candidate|approval-backed save|historical_save_identity_signal|superseded_reject_signal" docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md README.md plandoc/2026-03-28-durable-candidate-promotion-guardrail.md`

## 남은 리스크
- 이전 closeout에서 이어받은 리스크는 truthful recurrence key가 아직 없어서 repeated same-session drafts를 merge helper나 repeated-signal basis로 열 수 없다는 점이었습니다.
- 이번 라운드에서 해소한 리스크는 current shipped source-message candidate와 future `durable_candidate` 사이의 promotion shortcut confusion, 특히 approval-backed save 과대해석 리스크입니다.
- 여전히 남은 리스크는 future explicit confirmation surface shape가 아직 미정이라는 점과, repeated-signal promotion에 필요한 truthful recurrence key가 여전히 open question이라는 점입니다.
- 이번 라운드는 문서 작업만 수행했으므로, later implementation 전에 focused service / web-app regression으로 이 guardrail이 실제 serialization과 분리 상태를 유지하는지 다시 확인해야 합니다.
