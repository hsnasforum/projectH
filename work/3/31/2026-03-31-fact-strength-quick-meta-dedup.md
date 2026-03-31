# 2026-03-31 fact-strength quick-meta duplication cleanup

## 변경 파일
- `app/templates/index.html`

## 사용 skill
- 없음

## 변경 이유
- fact-strength summary bar가 response 본문 위에서 교차 확인/단일 출처/미확인 count를 color-coded pill로 보여주는데, quick-meta에 같은 정보가 `사실 검증 교차 확인 X · 단일 출처 Y · 미확인 Z` 텍스트로 중복 표시

## 핵심 변경

### 제거
- `renderResponseSummary`에서 `사실 검증 ${claimSummary}` parts.push 제거

### 유지
- `#fact-strength-bar`: primary fact-strength summary surface (color-coded, response 본문 직전)
- transcript meta의 `사실 검증 ...`: 개별 메시지 맥락으로 유지 (bar가 없는 transcript에서 필요)
- search history detail의 `사실 검증 ...`: history card 맥락으로 유지

### docs
- docs 추가 변경 불필요. fact-strength bar가 primary surface임이 이미 반영되어 있고, quick-meta에서 중복 제거는 구현 세부사항

## 검증
- `make e2e-test` — `12 passed (2.7m)`
- `git diff --check` (변경 파일) — 통과

## 남은 리스크
- dirty worktree는 여전히 넓음 (이번 라운드에서 unrelated 변경을 건드리지 않음)
