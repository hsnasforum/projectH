# 2026-03-31 copy button label clarity

## 변경 파일
- `app/templates/index.html`

## 사용 skill
- 없음

## 변경 이유
- 여러 copy 버튼이 모두 `경로 복사`로 표시되어 각 버튼의 목적이 불명확
- search history panel, response saved-path row, approval panel 3곳에서 동일 label 모호함

## 핵심 변경

### label 변경 (3곳)
- search history panel: `경로 복사` → `검색 기록 경로 복사`
- response saved-path row: `경로 복사` → `저장 경로 복사`
- approval panel: `경로 복사` → `승인 경로 복사`

### 변경하지 않은 것
- 기존 `검색 기록 복사` (response search-record row) — 이미 명확
- 기존 `응답 복사` — 이미 명확
- transcript 메시지의 `저장 경로 복사`/`검색 기록 복사` — 이미 명확 (line 2560, 2573)
- shared helper behavior / failure notice 변경 없음
- docs: label 수준 polish이므로 root docs 변경 불필요

## 검증
- `make e2e-test` — `12 passed (2.7m)`
- `git diff --check` — 통과

## 남은 리스크
- dirty worktree는 여전히 넓음 (이번 라운드에서 unrelated 변경을 건드리지 않음)
