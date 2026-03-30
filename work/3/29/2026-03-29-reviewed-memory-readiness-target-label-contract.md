# 2026-03-29 reviewed-memory readiness-target label contract

## 변경 파일
- `docs/PRODUCT_SPEC.md`
- `docs/ARCHITECTURE.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`
- `docs/NEXT_STEPS.md`
- `plandoc/2026-03-29-reviewed-memory-readiness-target-label-contract.md`
- `work/3/29/2026-03-29-reviewed-memory-readiness-target-label-contract.md`

## 사용 skill
- `mvp-scope`
- `approval-flow-audit`
- `doc-sync`
- `release-check`
- `work-log-closeout`

## 변경 이유
- 직전 closeout에서 current payload와 docs는 `eligible_for_reviewed_memory_draft`를 planning-only로 해석하고 있었지만, shipped label을 그대로 유지할지 아니면 더 좁힐지 exact contract가 아직 없다는 리스크를 이어받았습니다.
- `future_transition_target`, unblock `readiness_target`, capability-status `readiness_target`가 같은 label을 공유하는 만큼, 여기서 meaning drift가 생기면 blocked threshold / capability outcome / emitted transition / apply 경계가 다시 흐려질 수 있었습니다.

## 핵심 변경
- current shipped truth는 유지하기로 고정했습니다:
  - `reviewed_memory_precondition_status.future_transition_target = eligible_for_reviewed_memory_draft`
  - `reviewed_memory_unblock_contract.readiness_target = eligible_for_reviewed_memory_draft`
  - `reviewed_memory_capability_status.readiness_target = eligible_for_reviewed_memory_draft`
- 위 current shipped label의 exact meaning은 reviewed-memory draft planning only로 다시 고정했습니다.
- later narrowing이 reopen 되면 exact future narrowed label은 `eligible_for_reviewed_memory_draft_planning_only`로 정리했습니다.
- future narrowing은 rename-only pass여야 하고, 위 세 target field를 반드시 한 번에 함께 바꿔야 하며, 그 same pass에서 satisfaction / emitted transition / apply semantics를 열면 안 된다고 문서에 고정했습니다.
- approval-backed save / historical adjunct / review acceptance / `task_log`는 계속 support 또는 mirror only로 두고, label meaning이나 capability satisfaction shortcut으로 해석하지 않도록 유지했습니다.
- `docs/`, `plandoc/`, `/work`를 current shipped truth와 future narrowing contract에 맞춰 동기화했습니다.

## 검증
- `git diff --check`
- `rg -n 'eligible_for_reviewed_memory_draft|eligible_for_reviewed_memory_draft_planning_only|reviewed_memory_unblock_contract|reviewed_memory_capability_status|future_transition_target|readiness_target|blocked_all_required|unblocked_all_required' docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md README.md plandoc/2026-03-29-reviewed-memory-readiness-target-label-contract.md`

## 남은 리스크
- 이전 closeout에서 이어받은 리스크:
  - shipped `eligible_for_reviewed_memory_draft` label이 planning-only 의미를 담고는 있었지만, exact keep-or-narrow contract가 없어 later widening에서 meaning drift가 생길 수 있었습니다.
- 이번 라운드에서 해소한 리스크:
  - current shipped truth와 future narrowed label을 분리해 문서로 고정했고, 세 target field가 같은 의미를 공유한다는 coupling rule도 닫았습니다.
  - future rename-only pass가 semantic widening을 숨기는 경로가 되지 않도록 막았습니다.
- 여전히 남은 리스크:
  - current payload는 여전히 shipped label `eligible_for_reviewed_memory_draft`를 그대로 사용하므로, planning-only 의미를 더 직접적으로 드러내는 rename은 later implementation slice로 남아 있습니다.
  - later synchronized rename 이후에도 세 target field가 계속 같은 label을 중복 노출할지, 아니면 shared planning-target ref로 normalize할지는 아직 open question입니다.
  - reviewed-memory store / apply / emitted transition record / repeated-signal promotion / cross-session counting / user-level memory는 계속 later layer입니다.
