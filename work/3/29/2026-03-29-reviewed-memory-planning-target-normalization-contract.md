# 2026-03-29 reviewed-memory planning-target normalization contract

## 변경 파일
- `docs/PRODUCT_SPEC.md`
- `docs/ARCHITECTURE.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`
- `docs/NEXT_STEPS.md`
- `plandoc/2026-03-29-reviewed-memory-planning-target-normalization-contract.md`
- `work/3/29/2026-03-29-reviewed-memory-planning-target-normalization-contract.md`

## 사용 skill
- `mvp-scope`
- `approval-flow-audit`
- `doc-sync`
- `release-check`
- `work-log-closeout`

## 변경 이유
- 직전 closeout에서 current payload는 planning-only 의미를 정확히 담고 있었지만, 세 target field가 같은 label을 중복 노출하고 있어 later normalization 없이 두면 hidden drift나 partial migration이 다시 생길 수 있다는 리스크를 이어받았습니다.
- latest `plandoc`는 next smallest slice를 shared planning-target normalization으로 추천하고 있었지만, exact shared ref shape와 additive-vs-replacement migration rule이 아직 명시적으로 닫히지 않았습니다.

## 핵심 변경
- future normalization은 `Option B`로 고정했습니다:
  - one later additive read-only `reviewed_memory_planning_target_ref`
  - `planning_target_version = same_session_reviewed_memory_planning_target_ref_v1`
  - `target_label = eligible_for_reviewed_memory_draft_planning_only`
  - `target_scope = same_session_exact_recurrence_aggregate_only`
  - `target_boundary = reviewed_memory_draft_planning_only`
  - `defined_at = aggregate.last_seen_at`
- current shipped truth는 그대로 유지한다고 문서에 못 박았습니다:
  - 세 current target field는 계속 current payload truth
  - current blocked values(`overall_status`, `unblock_status`, `capability_outcome`)도 그대로
- first normalization pass의 exact migration rule을 닫았습니다:
  - additive-first only
  - one aggregate-level sibling shared ref 추가
  - 세 current target field는 같은 pass에서 유지
  - 세 field는 shared ref의 `target_label`을 exact derived echo로만 노출
  - one-off field normalization, partial replacement, partial removal 금지
  - duplicated field removal은 later separate cleanup contract로 분리
- approval-backed save / historical adjunct / review acceptance / `task_log` replay는 planning-target basis가 아니라는 점도 다시 고정했습니다.

## 검증
- `git diff --check`
- `rg -n "eligible_for_reviewed_memory_draft_planning_only|future_transition_target|readiness_target|shared planning-target ref|planning-target normalization|reviewed_memory_unblock_contract|reviewed_memory_capability_status" docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md README.md plandoc/2026-03-29-reviewed-memory-planning-target-normalization-contract.md`

## 남은 리스크
- 이전 closeout에서 이어받은 리스크:
  - current payload는 planning-only meaning을 정확히 담고 있지만, 세 field가 같은 label을 중복 노출해 later normalization 없이 두면 structure drift가 다시 생길 수 있었습니다.
- 이번 라운드에서 해소한 리스크:
  - shared planning-target normalization을 열지 말지 여부를 닫았고, exact shared ref shape와 additive-first migration contract도 문서로 고정했습니다.
  - future normalization이 blocked/satisfied, emitted transition, apply semantics를 몰래 넓히는 경로가 되지 않도록 막았습니다.
- 여전히 남은 리스크:
  - shared ref가 실제로 shipped 된 뒤 duplicated string fields를 얼마나 오래 compatibility echo로 유지할지는 아직 later cleanup question으로 남아 있습니다.
  - reviewed-memory store / apply / emitted transition record / repeated-signal promotion / cross-session counting / user-level memory는 계속 later layer입니다.
