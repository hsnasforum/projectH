# 2026-03-27 truthful-correction-surface-contract

## 변경 파일
- `docs/PRODUCT_SPEC.md`
- `docs/ARCHITECTURE.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`
- `docs/NEXT_STEPS.md`
- `plandoc/2026-03-27-truthful-correction-surface-contract.md`
- `work/3/27/2026-03-27-truthful-correction-surface-contract.md`

## 사용 skill
- `mvp-scope`: current shipped contract, next truthful surface, long-term memory layer를 섞지 않도록 문서 경계를 다시 고정했습니다.
- `doc-sync`: 구현 truth와 root docs / plandoc 문구를 맞췄습니다.
- `release-check`: 실제 실행한 검증만 남기고 미실행 검증을 분리했습니다.
- `work-log-closeout`: 오늘 문서 라운드 closeout을 표준 섹션으로 남겼습니다.

## 변경 이유
- 이전 closeout에서 이어받은 리스크:
  - `approval_reason_record` 최소 contract는 구현됐지만, `corrected` / `rejected` content outcome을 truthfully 기록하려면 어떤 사용자 surface가 필요한지 아직 문서로 고정되지 않았습니다.
  - approval rejection과 content rejection을 다시 섞을 위험이 남아 있었습니다.
  - 다음 slice에서 무엇을 먼저 도입해야 local-first, approval-safe, auditable 방향을 유지하는지 정리가 필요했습니다.
- 이번 라운드에서 해소한 리스크:
  - `corrected`는 explicit corrected text submission이 있어야만 truthfully 기록할 수 있다는 계약을 고정했습니다.
  - `rejected`는 approval reject와 분리된 explicit content-verdict control이 있어야만 truthfully 기록할 수 있다는 계약을 고정했습니다.
  - 다음 실제 UI/flow 도입 순서를 `corrected` first, `rejected` later로 문서에 통일했습니다.
- 여전히 남은 리스크:
  - correction submit과 optional save approval를 같은 response card에서 어떻게 분리 배치할지 세부 UI 결정은 남아 있습니다.
  - `rejected` surface는 아직 product/UI에 없기 때문에 content verdict를 실제로 수집하지 않습니다.
  - corrected text persistence, review queue, user-level memory는 계속 future work입니다.

## 핵심 변경
- `plandoc/2026-03-27-truthful-correction-surface-contract.md`
  - current implementation truth와 next-phase truthful surface contract를 분리해 새 설계 문서로 정리했습니다.
  - `corrected` 최소 surface를 “grounded-brief response에 미리 채워진 multiline correction editor”로 고정했습니다.
  - `rejected` 최소 surface를 “approval controls와 분리된 explicit content-verdict control”로 고정했습니다.
- root docs 동기화
  - `docs/PRODUCT_SPEC.md`
  - `docs/ARCHITECTURE.md`
  - `docs/ACCEPTANCE_CRITERIA.md`
  - `docs/MILESTONES.md`
  - `docs/TASK_BACKLOG.md`
  - `docs/NEXT_STEPS.md`
  - 모두 같은 방향으로 아래를 반영했습니다:
    - current shipped truth는 여전히 `accepted_as_is`와 approval-linked `approval_reason_record`까지만 구현
    - `corrected`는 explicit edited text 없이는 기록하지 않음
    - `rejected`는 approval reject, no-save, retry, feedback와 분리된 explicit content verdict 없이는 기록하지 않음
    - 다음 실제 MVP 도입은 `corrected` surface 먼저, `rejected`는 later

## 검증
- 실행함:
  - `git diff --check`
  - `rg -n "corrected_outcome|accepted_as_is|approval_reason_record|rejected|corrected|truthful" docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md README.md plandoc/2026-03-27-truthful-correction-surface-contract.md`
- 미실행:
  - `python3 -m py_compile ...`
  - `python3 -m unittest -v ...`
  - `make e2e-test`

## 남은 리스크
- 이전 closeout에서 남아 있던 “truthful corrected/rejected surface 부재” 리스크는 문서 계약 수준에서 정리했습니다.
- 이번 라운드에서 일부러 해소하지 않은 리스크:
  - corrected text persistence 미구현
  - content-level `rejected` capture 미구현
  - richer reject / reissue labels를 위한 explicit input surface 미구현
  - review queue, reviewed scope, rollback trace, user-level memory 미구현
- 다음 slice 후보:
  - grounded-brief response에 작은 correction editor를 추가하는 실제 UI/flow 구현
  - correction submit과 optional save approval의 배치/명칭을 혼동 없이 분리하는 focused UX 정리
