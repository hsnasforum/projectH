# 2026-03-31 quick-meta source filename docs sync

## 변경 파일
- `README.md`
- `docs/PRODUCT_SPEC.md`

## 사용 skill
- 없음

## 변경 이유
- 이전 라운드에서 구현 + smoke는 완료했으나, `README.md`와 `docs/PRODUCT_SPEC.md`가 아직 source filename 표시를 반영하지 않아 verify에서 `not_ready`

## 핵심 변경

### docs 반영 (2개 파일)
- `README.md`: evidence / source panel 아래에 "source filename in quick-meta bar and transcript meta when a single source document is used" 추가
- `docs/PRODUCT_SPEC.md`: 동일 위치에 동일 항목 추가

### 변경하지 않은 것
- 코드 변경 없음
- smoke 변경 없음
- `docs/ACCEPTANCE_CRITERIA.md`: 이전 라운드에서 이미 반영 완료

## 검증
- `git diff --check` — 통과

## 남은 리스크
- dirty worktree는 여전히 넓음 (이번 라운드에서 unrelated 변경을 건드리지 않음)
