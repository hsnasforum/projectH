# 2026-03-27 save identity corroboration contract

## 변경 파일
- `docs/PRODUCT_SPEC.md`
- `docs/ARCHITECTURE.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`
- `docs/NEXT_STEPS.md`
- `plandoc/2026-03-27-save-identity-corroboration-contract.md`
- `work/3/27/2026-03-27-save-identity-corroboration-contract.md`

## 사용 skill
- `approval-flow-audit`: `historical_save_identity_signal`이 approval-backed persisted save identity만 다루는지, `approval_granted`를 standalone replay source로 승격시키지 않는 경계를 점검했습니다.
- `doc-sync`: shipped `write_note`-only rule, future corroboration boundary, roadmap/backlog wording을 현재 구현과 맞게 동기화했습니다.
- `release-check`: 실제 실행한 `git diff --check`와 키워드 검색 결과만 기준으로 closeout 내용을 정리했습니다.
- `work-log-closeout`: 이번 문서 round의 결정, 검증, 남은 리스크를 `/work` 형식으로 남겼습니다.

## 변경 이유
- 직전 closeout에서 `historical_save_identity_signal`은 shipped 되었지만, same-anchor `write_note`-only replay가 현재 MVP에 충분한지와 future `approval_granted` corroboration을 열지 여부는 open question으로 남아 있었습니다.
- 이 질문을 broad save-history viewer나 pending-approval replay로 넓히지 않고, current shipped helper의 경계만 좁게 문서로 고정할 필요가 있었습니다.

## 핵심 변경
- current MVP 권고를 `Option A`로 고정했습니다.
  - shipped `write_note`-only replay를 현재로서는 충분한 규칙으로 유지합니다.
  - `approval_granted` corroboration은 immediate next slice로 열지 않습니다.
- future corroboration이 reopen 되더라도 boundary를 좁게 고정했습니다.
  - `approval_granted`는 standalone replay source가 아니라 same-anchor, same-`approval_id` `write_note` candidate에 대한 corroboration-only 규칙으로만 허용합니다.
  - `approval_granted`만 있고 matching persisted `write_note`가 없으면 `historical_save_identity_signal`을 만들지 않습니다.
- current `save_signal`과 historical adjunct의 분리도 더 명확히 문서화했습니다.
  - `save_signal`은 계속 current-state-only summary입니다.
  - `historical_save_identity_signal`은 계속 source-message-anchored historical adjunct입니다.
  - broader save history, pending approval replay, content verdict replay, approval-friction relabeling은 계속 금지입니다.
- roadmap/backlog/next-steps는 now/next/later를 분리했습니다.
  - now: shipped `write_note`-only helper 유지
  - next if reopened: same-approval corroboration-only
  - later: broad save history나 durable candidate는 아직 아님

## 검증
- `git diff --check`
- `rg -n "historical_save_identity_signal|write_note|approval_granted|latest_approval_id|save_signal|save_content_source|saved_note_path|approval_id" docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md README.md plandoc/2026-03-27-save-identity-corroboration-contract.md`

## 남은 리스크
- 이전 closeout에서 남아 있던 `approval_granted` corroboration open question은 이번 라운드에서 “지금은 열지 않는다”로 경계를 고정했지만, 실제 operator ambiguity가 생기면 later same-approval corroboration-only slice를 다시 검토해야 합니다.
- `historical_save_identity_signal`은 여전히 at-most-one latest historical save identity만 다루므로, broader save history viewer나 cross-artifact aggregate는 future scope로 남아 있습니다.
- content-side `superseded_reject_signal`과 save-axis helper를 한 surface나 한 flattened field로 합치지 않는 현재 분리 원칙은 계속 유지되어야 합니다.
