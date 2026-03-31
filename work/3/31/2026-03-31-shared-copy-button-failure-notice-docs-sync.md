# 2026-03-31 shared copy-button failure-notice docs sync

## 변경 파일
- `README.md`
- `docs/PRODUCT_SPEC.md`
- `docs/ACCEPTANCE_CRITERIA.md`

## 사용 skill
- 없음

## 변경 이유
- `copyTextValue()` helper는 response text, approval path, saved-note path, search-record path 4개 copy 버튼에 공유되지만, root docs가 "response copy-to-clipboard button" 중심으로만 적혀 있어 misleading

## 핵심 변경

### docs 반영 (3개 파일)
- `README.md`: "response copy-to-clipboard button" → "copy-to-clipboard buttons for response text, approval path, saved-note path, and search-record path (shared helper...)"
- `docs/PRODUCT_SPEC.md`: 동일
- `docs/ACCEPTANCE_CRITERIA.md`: 4개 copy surface와 shared helper truth를 정직하게 반영, coverage 범위 유지

### 변경하지 않은 것
- 코드 변경 없음
- 테스트 변경 없음

## 검증
- `git diff --check` — 통과
- `make e2e-test` — docs-only 라운드이므로 생략. 이전 라운드의 verify에서 12/12 green 확인 완료.

## 남은 리스크
- dirty worktree는 여전히 넓음 (이번 라운드에서 unrelated 변경을 건드리지 않음)
