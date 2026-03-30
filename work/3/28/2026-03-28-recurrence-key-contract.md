# 2026-03-28 recurrence-key-contract

## 변경 파일
- `docs/PRODUCT_SPEC.md`
- `docs/ARCHITECTURE.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`
- `docs/NEXT_STEPS.md`
- `plandoc/2026-03-28-recurrence-key-contract.md`
- `work/3/28/2026-03-28-recurrence-key-contract.md`

## 사용 skill
- `mvp-scope`: current shipped memory/review boundary와 next-phase recurrence 방향을 섞지 않도록 MVP 범위를 다시 고정했습니다.
- `approval-flow-audit`: approval-backed save가 recurrence basis나 promotion shortcut으로 오해되지 않도록 경계를 점검했습니다.
- `doc-sync`: root docs와 `plandoc`에서 같은 recurrence 계약을 구현 사실에 맞춰 동기화했습니다.
- `release-check`: 실행한 문서 검증과 미실행 항목을 분리해 handoff 상태를 정리했습니다.
- `work-log-closeout`: 오늘 closeout 형식과 남은 리스크를 저장소 규칙에 맞춰 남겼습니다.

## 변경 이유
- 직전 closeout에서 `accept` only review slice는 닫혔지만, repeated-signal promotion의 truthful recurrence key가 아직 없어서 same-family merge나 broader durable promotion을 정직하게 열 수 없는 상태였습니다.
- 현재 구현은 explicit original-vs-corrected pair, explicit confirmation, reviewed-but-not-applied trace까지는 갖췄지만, cross-source identity는 아직 정의되지 않았습니다.
- 그래서 current source-message candidate / durable projection / review trace / later repeated-signal promotion 사이 경계를 문서로 먼저 고정할 필요가 있었습니다.

## 핵심 변경
- first truthful recurrence key를 future source-message-anchored `candidate_recurrence_key`로 고정했습니다.
- recurrence key의 의미를 “same family”나 fixed statement가 아니라, explicit original-vs-corrected pair에서 locally derivable 한 deterministic rewrite-transformation class의 identity로 좁혔습니다.
- allowed basis / supporting context / never basis를 다시 분리했습니다:
  - basis: explicit pair, later reviewed trace as strengthening evidence only
  - context only: `session_local_memory_signal`, `superseded_reject_signal`, `historical_save_identity_signal`, approval-backed save
  - never basis: `candidate_family` alone, fixed statement alone, queue presence alone, review acceptance alone, task-log replay alone
- repeated-signal threshold를 current family 기준 최소 2개의 distinct grounded briefs로 고정했고, same source message의 repeated edit는 multi-brief recurrence로 세지 않도록 명시했습니다.
- next implementation slice를 multi-source aggregation이 아니라 one source-message `candidate_recurrence_key` draft projection으로 추천하도록 `NEXT_STEPS`, `MILESTONES`, `TASK_BACKLOG`를 맞췄습니다.

## 검증
- 실행:
  - `git diff --check`
  - `rg -n "recurrence key|candidate_family|durable_candidate|candidate_review_record|review_queue|approval-backed save|repeated-signal promotion" docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md README.md plandoc/2026-03-28-recurrence-key-contract.md`
- 미실행:
  - 제품 코드 테스트
  - 브라우저 smoke
  - 이번 라운드는 문서 작업이라 실행하지 않았습니다.

## 남은 리스크
- 이전 closeout에서 이어받은 리스크:
  - repeated-signal promotion에 쓸 truthful recurrence key가 없어서 same-family merge와 broader durable promotion이 과장될 수 있었습니다.
- 이번 라운드에서 해소한 리스크:
  - recurrence key의 의미, basis boundary, 최소 envelope, distinctness threshold, review layer와의 관계를 문서로 고정했습니다.
- 여전히 남은 리스크:
  - `candidate_recurrence_key`의 실제 deterministic derivation helper는 아직 구현되지 않았습니다.
  - first aggregation을 same-session only로 시작할지, cross-session counting을 바로 열지는 아직 구현 전 open question입니다.
  - `rewrite_dimensions`를 어디까지 노출해야 semantic overclaim 없이 설명 가능한지도 아직 남아 있습니다.
