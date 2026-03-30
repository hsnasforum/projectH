# 2026-03-29 reviewed-memory duplicated-target cleanup contract

## 변경 파일
- `docs/PRODUCT_SPEC.md`
- `docs/ARCHITECTURE.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`
- `docs/NEXT_STEPS.md`
- `plandoc/2026-03-29-reviewed-memory-planning-target-normalization-contract.md`
- `plandoc/2026-03-29-reviewed-memory-duplicated-target-cleanup-contract.md`
- `work/3/29/2026-03-29-reviewed-memory-duplicated-target-cleanup-contract.md`

## 사용 skill
- `mvp-scope`: current shipped shared ref와 later cleanup-only pass를 apply/store와 섞지 않도록 MVP 경계를 다시 좁혔습니다.
- `approval-flow-audit`: approval-backed save, historical adjunct, review acceptance, `task_log` replay가 cleanup basis처럼 읽히지 않는 safety boundary를 다시 확인했습니다.
- `doc-sync`: current shipped payload truth와 new cleanup contract를 root docs / both planning-target `plandoc` files / `/work`에 함께 반영했습니다.
- `release-check`: 실제 실행한 `git diff --check`와 `rg` 결과만 기준으로 이번 문서 round를 닫았습니다.
- `work-log-closeout`: 저장소 규칙에 맞는 `/work` closeout 형식으로 이번 계약 정리와 남은 리스크를 기록했습니다.

## 변경 이유
- 직전 closeout에서 current payload는 shared planning-target ref와 duplicated echo fields를 함께 노출하고 있었고, cleanup timing과 exact migration rule 없이 field removal을 열면 hidden semantic drift나 partial cleanup이 생길 수 있다는 리스크를 이어받았습니다.
- 지금 단계에서 필요한 것은 readiness widening이 아니라 cleanup timing contract였기 때문에, structural-only decision을 먼저 닫는 편이 더 정직했습니다.

## 핵심 변경
- duplicated target cleanup은 `Option A`로 고정했습니다:
  - shared ref가 먼저 shipped 된 현재 truth를 유지
  - duplicated echo fields는 one compatibility release window 동안 유지
  - 그 다음 later cleanup-only pass에서 세 field를 함께 제거
- one compatibility release window도 문서로 고정했습니다:
  - shared ref implementation round 다음의 explicit shipped round에서 docs, payload, tests가 still shared ref plus all three echoes를 unchanged로 노출하는 window
- later cleanup pass의 exact removal boundary를 닫았습니다:
  - 제거 대상은 아래 세 field only
    - `reviewed_memory_precondition_status.future_transition_target`
    - `reviewed_memory_unblock_contract.readiness_target`
    - `reviewed_memory_capability_status.readiness_target`
  - docs / payload / tests는 same round에 함께 변경
  - one-field removal, staggered removal, hidden fallback은 금지
- shared ref와 cleanup semantics가 blocked/satisfied outcome, emitted transition, reviewed-memory apply, repeated-signal promotion, cross-session counting으로 읽히지 않도록 root docs와 both planning-target `plandoc` files wording을 current truth에 맞춰 다시 정리했습니다.

## 검증
- `git diff --check`
- `rg -n "reviewed_memory_planning_target_ref|eligible_for_reviewed_memory_draft_planning_only|future_transition_target|readiness_target|duplicated target|cleanup pass|compatibility echo|compatibility window" docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md README.md plandoc/2026-03-29-reviewed-memory-planning-target-normalization-contract.md plandoc/2026-03-29-reviewed-memory-duplicated-target-cleanup-contract.md`

## 남은 리스크
- 이전 closeout에서 이어받은 리스크:
  - shared ref는 shipped 되었지만 duplicated echo fields cleanup timing과 migration rule이 아직 명시적으로 닫히지 않았습니다.
- 이번 라운드에서 해소한 리스크:
  - compatibility window, all-or-nothing removal, docs/payload/tests same-round sync rule을 문서로 고정했습니다.
  - cleanup-only pass가 readiness, satisfaction, emitted transition, apply widening처럼 읽히는 경로를 막았습니다.
- 여전히 남은 리스크:
  - actual cleanup implementation은 아직 later slice입니다.
  - one compatibility release window가 지난 뒤 removal round에서 external or local consumer가 shared ref를 already 읽고 있는지 확인하는 operator discipline은 여전히 필요합니다.
  - reviewed-memory store / apply / emitted transition record / repeated-signal promotion / cross-session counting / user-level memory는 계속 later layer입니다.
