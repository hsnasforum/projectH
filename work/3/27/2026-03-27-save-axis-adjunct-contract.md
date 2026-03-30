## 변경 파일
- `docs/PRODUCT_SPEC.md`
- `docs/ARCHITECTURE.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`
- `docs/NEXT_STEPS.md`
- `plandoc/2026-03-27-save-axis-adjunct-contract.md`

## 사용 skill
- `approval-flow-audit`
- `doc-sync`
- `release-check`
- `work-log-closeout`

## 변경 이유
- 최신 `session_local_memory_signal`과 `superseded_reject_signal`이 shipped 되면서, 남은 핵심 리스크가 save-axis의 `latest_approval_id` loss로 좁혀졌습니다.
- content-side replay helper에 save-axis 문제를 섞지 않고, 별도 narrow adjunct가 필요한지와 최소 계약을 먼저 문서로 고정할 필요가 있었습니다.

## 핵심 변경
- current-state `save_signal`은 그대로 유지하고, save identity loss만 다루는 별도 optional adjunct를 next slice로 여는 방향으로 권고를 고정했습니다.
- 권장 adjunct 이름을 `historical_save_identity_signal`로 정하고, source-message-anchored / read-only / at-most-one latest historical approval-backed save identity 계약을 문서화했습니다.
- replay 범위를 `approval_id`, `save_content_source`, `saved_note_path`, `recorded_at` 정도로 좁히고, saved body copy / approval preview body / content verdict replay / approval-friction relabeling / cross-artifact aggregate는 금지하도록 정리했습니다.
- content-side `superseded_reject_signal`과 save-axis adjunct를 분리하고, task-log를 canonical current-state source로 승격하지 않는 경계를 다시 명확히 했습니다.

## 검증
- `git diff --check`
- `rg -n "latest_approval_id|save_signal|save_content_source|saved_note_path|superseded_reject_signal|session_local_memory_signal|approval_id" docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md README.md plandoc/2026-03-27-save-axis-adjunct-contract.md`

## 남은 리스크
- first save-axis adjunct를 실제 구현할 때 `write_note` 단독 replay로 충분한지, 아니면 `approval_granted`와의 same-approval corroboration까지 요구할지 아직 남아 있습니다.
- `historical_save_identity_signal`까지 shipped 되더라도 broader save history나 durable-candidate / user-level memory는 여전히 future scope입니다.
