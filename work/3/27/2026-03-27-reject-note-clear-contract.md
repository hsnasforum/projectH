## 변경 파일
- `docs/PRODUCT_SPEC.md`
- `docs/ARCHITECTURE.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`
- `docs/NEXT_STEPS.md`
- `plandoc/2026-03-27-reject-note-clear-contract.md`
- `work/3/27/2026-03-27-reject-note-clear-contract.md`

## 사용 skill
- `frontend-skill`
- `doc-sync`
- `release-check`
- `work-log-closeout`

## 변경 이유
- 직전 closeout 기준으로 shipped reject-note surface와 long-history browser smoke는 이미 안정됐지만, manual blank-note clear UX는 아직 미구현이었고 실제로 필요한지조차 문서로 최종 고정되지 않았습니다.
- 이번 라운드 목표는 shipped reject-note semantics를 다시 열지 않은 채, manual clear를 next slice로 당길지 여부와 만약 나중에 열면 무엇을 지우고 어떻게 감사 추적할지를 문서 계약으로만 정리하는 것이었습니다.

## 핵심 변경
- 최종 권고를 `Option B`로 고정했습니다.
  - current disabled-blank-submit behavior를 더 유지합니다.
  - manual clear UX는 next refinement slice로 바로 올리지 않습니다.
- reject verdict와 optional note를 다른 층으로 문서에 못박았습니다.
  - future manual clear가 생겨도 `corrected_outcome.outcome = rejected`는 유지합니다.
  - fixed-label `explicit_content_rejection` baseline도 유지합니다.
  - clear 대상은 `content_reason_record.reason_note`뿐입니다.
- future clear contract도 최소 범위로만 적었습니다.
  - same response-card `내용 판정` box 안의 tiny secondary action
  - existing non-empty note가 있을 때만 노출
  - blank submit을 clear로 재해석하지 않음
  - `content_reason_record`는 유지하고 optional `reason_note` field만 제거
  - `content_reason_record.recorded_at`만 clear 시점으로 refresh
  - `corrected_outcome.recorded_at`는 reject verdict 시각 유지
  - future task-log event는 `content_reason_note_recorded`와 분리된 별도 clear event 예: `content_reason_note_cleared`
- root docs에는 current shipped truth와 deferred contract를 짧게 반영했고, 상세 rationale은 새 `plandoc`에 분리했습니다.
- `docs/TASK_BACKLOG.md`의 오래된 문구 하나도 정리했습니다.
  - reject-note records가 “나중에 추가될 것”처럼 적혀 있던 문장을, shipped same-card note surface의 반복 사용으로부터 더 쌓일 데이터라는 현재 truth에 맞게 바꿨습니다.

## 검증
- `rg -n "reason_note|content_reason_record|manual clear|blank submit|explicit_content_rejection|내용 거절" docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md README.md plandoc/2026-03-27-reject-note-clear-contract.md`
- `git diff --check`

## 남은 리스크
- 이전 closeout에서 이어받은 리스크였던 “manual clear UX가 정말 필요한지와, 필요하다면 smallest truthful contract가 무엇인지 불명확하다”는 점은 이번 라운드에서 문서 계약 수준으로 해소했습니다.
- 이번 라운드에서 의도적으로 남긴 범위 제한:
  - 제품 코드는 바꾸지 않았습니다.
  - actual manual clear UX는 구현하지 않았습니다.
  - richer reject label taxonomy도 열지 않았습니다.
- 여전히 남은 리스크:
  - operator usage가 더 쌓인 뒤에도 manual clear가 실제로 필요한지 추가 관찰이 필요합니다.
  - future clear를 정말 구현하게 되면, inline helper copy만으로 충분한지 tiny one-step confirm이 필요한지는 implementation slice에서 다시 좁혀야 합니다.
