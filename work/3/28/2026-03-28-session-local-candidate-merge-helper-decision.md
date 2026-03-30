## 변경 파일
- `docs/PRODUCT_SPEC.md`
- `docs/ARCHITECTURE.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`
- `docs/NEXT_STEPS.md`
- `plandoc/2026-03-28-session-local-candidate-merge-helper-contract.md`
- `work/3/28/2026-03-28-session-local-candidate-merge-helper-decision.md`

## 사용 skill
- `mvp-scope`
- `approval-flow-audit`
- `doc-sync`
- `release-check`
- `work-log-closeout`

## 변경 이유
- `2026-03-28-session-local-candidate-draft-implementation` closeout에서 남긴 핵심 리스크는 repeated same-session `correction_rewrite_preference` drafts를 계속 source-message 단위로 둘지, 작은 merge helper를 열지 미정이라는 점이었습니다.
- 이번 라운드의 목적은 shipped `session_local_candidate` semantics를 흔들지 않으면서, same-session merge helper 필요 여부와 최소 계약을 문서로만 고정하는 것이었습니다.
- 현재 shipped candidate envelope는 `candidate_family`, 고정 문장, 보수적 support refs까지만 담고 있어서, family alone 기준 merge는 과장된 결론이 될 수 있습니다.

## 핵심 변경
- 최종 권고를 `Option A`로 고정했습니다.
  - repeated same-session `correction_rewrite_preference` drafts는 당분간 per-source-message `session_local_candidate`로 유지합니다.
  - current MVP에서는 same-session merge helper를 열지 않습니다.
- 이유를 현재 구현 계약과 연결해 명시했습니다.
  - shipped `session_local_candidate`는 explicit original-vs-corrected pair를 primary basis로 갖지만, 어떤 rewrite preference가 반복되었는지 식별할 truthful merge key는 아직 없습니다.
  - 따라서 `candidate_family`, 고정 statement, `supporting_signal_refs`만으로 merge하면 source-message candidate와 future durable candidate의 경계가 흐려집니다.
- future reopen 조건도 가장 좁게 고정했습니다.
  - 나중에 다시 연다면 one optional top-level session-local read-only projection 하나만 허용합니다.
  - 이름은 `session_candidate_family_signal`로 문서화했습니다.
  - same session only, same family only, 최소 2개의 distinct source-message candidates, explicit corrected pair에서 온 future merge key가 있을 때만 허용하도록 정리했습니다.
  - source-message `session_local_candidate` overwrite, durable/review/user-level semantics, broad history/feed viewer는 모두 금지로 유지했습니다.
- 역할 분리도 다시 못 박았습니다.
  - `session_local_candidate`는 current explicit pair draft입니다.
  - `superseded_reject_signal`, `historical_save_identity_signal`은 historical adjunct로만 남습니다.
  - approval-backed save는 계속 supporting evidence only이며 merge basis나 promotion shortcut이 아닙니다.
- next slice 권고를 바꿨습니다.
  - merge helper 구현보다 먼저, shipped `session_local_candidate`에서 future `durable_candidate`로 가는 minimum promotion guardrail을 정의하는 쪽이 현재 MVP와 audit 경계에 더 맞는다고 정리했습니다.

## 검증
- 실행함: `git diff --check`
- 실행함: `rg -n "session_local_candidate|merge helper|correction_rewrite_preference|supporting_signal_refs|durable_candidate|historical_save_identity_signal|superseded_reject_signal|approval-backed save" docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md README.md plandoc/2026-03-28-session-local-candidate-merge-helper-contract.md`
- 미실행: 제품 코드 테스트

## 남은 리스크
- 이전 closeout에서 이어받은 리스크였던 repeated same-session draft merge 여부는 이번 라운드에서 "아직 열지 않는다"로 정리했지만, 장기적으로는 truthful merge key를 어디서 최소한으로 뽑을지 여전히 남아 있습니다.
- 이번 라운드에서 해소한 리스크는 source-message candidate, historical adjunct, approval-backed save support, future durable candidate 사이의 경계를 다시 좁게 고정했다는 점입니다.
- 여전히 남은 리스크는 future `durable_candidate` promotion guardrail이 아직 문서/구현으로 닫히지 않았다는 점과, merge helper를 다시 열 경우 rewrite-summary helper 없이도 truthful key를 만들 수 있는 최소 계약이 아직 확정되지 않았다는 점입니다.
