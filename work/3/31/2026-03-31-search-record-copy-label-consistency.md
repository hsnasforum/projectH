# 2026-03-31 search-record copy label consistency

## 변경 파일
- `app/templates/index.html`
- `README.md`
- `docs/PRODUCT_SPEC.md`
- `docs/ACCEPTANCE_CRITERIA.md`

## 사용 skill
- 없음

## 변경 이유
- 같은 search-record path copy인데 response row와 transcript에서는 `검색 기록 복사`, search history panel에서는 `검색 기록 경로 복사`로 불일치

## 핵심 변경

### code 변경
- response search-record row: `검색 기록 복사` → `검색 기록 경로 복사`
- transcript message action: `검색 기록 복사` → `검색 기록 경로 복사`

### docs 반영 (3개 파일)
- `README.md` / `docs/PRODUCT_SPEC.md` / `docs/ACCEPTANCE_CRITERIA.md`: `검색 기록 복사` 제거, 4개 label로 통일 (`응답 복사`, `저장 경로 복사`, `승인 경로 복사`, `검색 기록 경로 복사`)

## 검증
- `make e2e-test` — `12 passed (2.7m)`
- `git diff --check` — 통과

## 남은 리스크
- dirty worktree는 여전히 넓음 (이번 라운드에서 unrelated 변경을 건드리지 않음)
