# 2026-03-31 note-path default directory placeholder docs sync

## 변경 파일
- `README.md`
- `docs/PRODUCT_SPEC.md`

## 사용 skill
- 없음

## 변경 이유
- 이전 라운드에서 note-path placeholder 구현 + `docs/ACCEPTANCE_CRITERIA.md`는 반영 완료했으나, `README.md`와 `docs/PRODUCT_SPEC.md`가 아직 current shipped contract를 반영하지 않아 verify에서 `not_ready`

## 핵심 변경

### docs 반영 (2개 파일)
- `README.md`: "approval-based save" → "approval-based save with default notes directory shown in the save-path placeholder"
- `docs/PRODUCT_SPEC.md`: "approval-gated save of summary notes" → "approval-gated save of summary notes with default notes directory shown in the save-path placeholder"

### 변경하지 않은 것
- 코드 변경 없음
- smoke 변경 없음
- `docs/ACCEPTANCE_CRITERIA.md`: 이전 라운드에서 이미 반영 완료

## 검증
- `git diff --check` — 통과
- `make e2e-test` — docs-only 라운드이므로 생략. 이전 라운드에서 code 변경과 함께 12/12 green 확인 완료이며, 이번 라운드는 문서 문구만 변경했으므로 `git diff --check`만으로 충분합니다.

## 남은 리스크
- dirty worktree는 여전히 넓음 (이번 라운드에서 unrelated 변경을 건드리지 않음)
