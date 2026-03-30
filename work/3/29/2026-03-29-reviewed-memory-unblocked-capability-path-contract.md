# 2026-03-29 reviewed-memory unblocked capability-path contract

## 변경 파일
- `docs/PRODUCT_SPEC.md`
- `docs/ARCHITECTURE.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`
- `docs/NEXT_STEPS.md`
- `plandoc/2026-03-29-reviewed-memory-unblocked-capability-path-contract.md`
- `work/3/29/2026-03-29-reviewed-memory-unblocked-capability-path-contract.md`

## 사용 skill
- `mvp-scope`: current shipped contract, next capability-path target, later emitted/apply layer를 다시 분리했습니다.
- `approval-flow-audit`: approval-backed save, historical adjunct, review acceptance, `task_log`가 capability basis처럼 읽히지 않도록 경계를 점검했습니다.
- `doc-sync`: root docs와 새 `plandoc`를 current implementation truth와 같은 wording으로 맞췄습니다.
- `release-check`: 실제 실행한 `git diff --check`와 `rg`만 기준으로 문서 라운드를 닫았습니다.
- `work-log-closeout`: 저장소 규칙에 맞는 `/work` closeout 형식으로 이번 계약 정리와 남은 리스크를 기록했습니다.

## 변경 이유
- 직전 closeout에서 existing shell에는 one separate aggregate-level blocked trigger affordance가 이미 들어갔지만, 무엇이 exact same-session aggregate를 truthfully `unblocked_all_required`로 올릴 수 있는지는 아직 exact contract가 없었습니다.
- 이 질문이 열린 채로 다음 구현을 진행하면 enabled trigger, note input, emitted transition record, reviewed-memory apply result를 한 번에 섞어 과장할 위험이 남아 있었습니다.

## 핵심 변경
- first truthful `unblocked_all_required`는 current contract-object existence가 아니라 one separate later read-only `reviewed_memory_capability_basis`를 요구하도록 고정했습니다.
- `reviewed_memory_capability_basis`는 same-session exact aggregate scope, exact supporting refs, exact required preconditions, `basis_status = all_required_capabilities_present`, `satisfaction_basis_boundary = canonical_reviewed_memory_layer_capabilities_only`, `evaluated_at`만 갖는 최소 future basis object로 정의했습니다.
- current blocked trigger affordance와 future capability-path layer를 분리했습니다:
  - current card는 visible-but-disabled truth 유지
  - future capability-path opening alone은 note input, `canonical_transition_id`, `operator_reason_or_note`, `emitted_at`, emitted transition record를 만들지 않음
  - enabled submit / emitted-record trigger는 adjacent later round로 분리
- source-message candidate / durable projection / review trace / recurrence key / same-session aggregate / blocked marker / precondition status / contract chain / blocked trigger affordance / future capability-path layer 경계를 root docs와 새 `plandoc`에 다시 고정했습니다.
- next slice를 one separate capability materialization pass only로 좁혔습니다.

## 검증
- 실행: `git diff --check`
- 실행: `rg -n "unblocked_all_required|blocked_all_required|reviewed_memory_capability_status|reviewed_memory_transition_record|검토 메모 적용 시작|review_queue_items|candidate_review_record" docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md app/templates/index.html app/web.py plandoc/2026-03-29-reviewed-memory-unblocked-capability-path-contract.md plandoc/2026-03-29-reviewed-memory-apply-trigger-source-contract.md`

## 남은 리스크
- 이전 closeout에서 이어받은 핵심 리스크:
  - aggregate-level blocked trigger affordance는 now visible하지만, 무엇이 exact same-session aggregate를 truthfully `unblocked_all_required`로 올리는지 아직 exact contract가 없었습니다.
- 이번 라운드에서 해소한 리스크:
  - capability-path basis를 current contract existence와 분리했고, capability-path opening alone이 emitted record나 apply result처럼 읽히지 않도록 5단 층위를 고정했습니다.
  - approval-backed save, historical adjunct, source-message review acceptance, `task_log` replay가 unblocked basis처럼 오해될 여지를 줄였습니다.
- 여전히 남은 리스크:
  - `reviewed_memory_capability_basis`와 truthful `unblocked_all_required`는 아직 미구현입니다.
  - current blocked aggregate card를 언제 어떤 UI round에서 실제 enabled state로 소비할지는 아직 구현되지 않았습니다.
  - emitted transition record, reviewed-memory apply result, repeated-signal promotion, cross-session counting, user-level memory는 계속 later layer입니다.
