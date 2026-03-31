# 2026-03-31 verification strength history docs sync

## 변경 파일
- `README.md`
- `docs/PRODUCT_SPEC.md`

## 사용 skill
- 없음

## 변경 이유
- 이전 라운드에서 verification strength tag UI 및 `docs/ACCEPTANCE_CRITERIA.md`는 반영 완료했으나, `README.md`와 `docs/PRODUCT_SPEC.md`가 web history detail의 verification strength tag를 아직 명시하지 않아 docs honesty gap이 남아 있었음

## 핵심 변경

### docs 반영 (2개 파일)
- `README.md`: web investigation history 항목에 "and verification strength tags" 추가
- `docs/PRODUCT_SPEC.md`: web search history panel 항목에 "and verification strength tags" 추가

### 변경하지 않은 것
- 코드 변경 없음
- smoke 변경 없음
- `docs/ACCEPTANCE_CRITERIA.md`: 이전 라운드에서 이미 반영 완료

## 검증
- `git diff --check` — 통과
- `make e2e-test` — docs-only 라운드이므로 생략

## 남은 리스크
- dirty worktree는 여전히 넓음 (이번 라운드에서 unrelated 변경을 건드리지 않음)
