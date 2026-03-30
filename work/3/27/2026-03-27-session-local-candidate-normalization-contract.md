# 2026-03-27 session_local_candidate normalization contract

## 변경 파일
- `docs/PRODUCT_SPEC.md`
- `docs/ARCHITECTURE.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`
- `docs/NEXT_STEPS.md`
- `plandoc/2026-03-27-session-local-candidate-normalization-contract.md`
- `work/3/27/2026-03-27-session-local-candidate-normalization-contract.md`

## 사용 skill
- `mvp-scope`: current shipped signal / next normalized candidate / later durable candidate / long-term user-level memory를 다시 분리해 현재 MVP 범위를 좁게 고정했습니다.
- `approval-flow-audit`: approval-backed save를 first candidate의 primary basis로 과장하지 않고 supporting evidence only로 남기는 경계를 점검했습니다.
- `doc-sync`: shipped signal/adjunct reality와 next candidate contract가 spec / architecture / acceptance / roadmap / plandoc에 같은 경계로 반영되도록 맞췄습니다.
- `release-check`: 실제 실행한 `git diff --check`와 키워드 검색 결과만 기준으로 closeout 내용을 정리했습니다.
- `work-log-closeout`: 이번 문서 round의 변경 파일, 검증, 남은 리스크를 `/work` 형식으로 남겼습니다.

## 변경 이유
- 직전 closeout 기준으로 `historical_save_identity_signal`의 `write_note`-only 경계까지는 고정됐지만, 다음 단계로 무엇을 normalization할지 자체는 아직 열려 있었습니다.
- broad save-history나 추가 replay helper를 더 늘리기 전에, 현재 shipped source-message memory signal들 위에서 어떤 first normalized `session_local_candidate`를 만들 수 있는지 먼저 좁힐 필요가 있었습니다.

## 핵심 변경
- first normalized `session_local_candidate` envelope를 문서로 고정했습니다.
  - `candidate_id`
  - `candidate_scope = session_local`
  - `candidate_family`
  - `statement`
  - `supporting_artifact_ids`
  - `supporting_source_message_ids`
  - `supporting_signal_refs`
  - `evidence_strength`
  - `status = session_local_candidate`
  - timestamps
- current signal / historical adjunct / candidate / durable candidate 경계를 명시했습니다.
  - `session_local_memory_signal`은 current-state-only summary
  - `superseded_reject_signal`, `historical_save_identity_signal`은 narrow historical adjunct
  - `session_local_candidate`는 그 위의 normalized reusable unit
  - `durable_candidate`와 reviewed memory는 여전히 future scope
- first candidate family를 하나만 고정했습니다.
  - `correction_rewrite_preference`
  - primary basis는 same source message의 explicit original-vs-corrected pair
  - approval friction, content reject, broad save history는 primary basis로 쓰지 않습니다
- approval-backed save의 역할도 다시 좁혔습니다.
  - first candidate에서 supporting evidence only
  - sole basis 금지
  - implicit content confirmation 금지
  - broader scope justification 금지
- next implementation slice 추천을 하나로 고정했습니다.
  - same source-message serialization에 optional computed `session_local_candidate` draft를 additively 붙이는 작은 slice

## 검증
- `git diff --check`
- `rg -n "session_local_candidate|candidate_family|supporting_artifact_ids|supporting_source_message_ids|evidence_strength|durable_candidate|approval-backed save|session_local_memory_signal|historical_save_identity_signal|superseded_reject_signal" docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md README.md plandoc/2026-03-27-session-local-candidate-normalization-contract.md`

## 남은 리스크
- 이전 closeout에서 남아 있던 “next internal step이 replay helper 추가인지 candidate normalization인지 아직 분명하지 않다”는 리스크는 이번 라운드에서 candidate normalization 우선으로 정리했지만, first candidate statement를 어떤 수준의 deterministic helper로 만들지 자체는 여전히 open question입니다.
- first family를 `correction_rewrite_preference`로 좁혔기 때문에, save-path acceptability나 content-reject pattern 계열 후보는 later scope로 남아 있습니다.
- `session_local_candidate`는 아직 미구현이므로, future implementation slice에서는 current signal과 candidate를 flatten 하지 않는 regression이 먼저 필요합니다.
