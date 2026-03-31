# 2026-03-31 response copy text button

## 변경 파일
- `app/templates/index.html`

## 사용 skill
- 없음

## 변경 이유
- 사용자가 요약이나 답변을 다른 곳에 붙여넣으려면 `<pre>` 텍스트를 수동 선택해야 했음
- 경로 복사, 검색 기록 복사 버튼은 이미 있으나 응답 본문 복사 버튼이 없었음

## 핵심 변경

### 추가된 UI surface
- 응답 패널 헤더에 "응답 복사" 버튼 (`#response-copy-text`, `data-testid="response-copy-text"`)
- 기존 `copyTextValue()` 함수 재사용: `navigator.clipboard.writeText` 우선, fallback textarea 복사
- 복사 후 `renderNotice("응답 텍스트를 복사했습니다.")` 피드백
- 기존 `.copy-button.subtle` 스타일 재사용

### 변경하지 않은 것
- 응답 데이터 구조 변경 없음
- 기존 경로 복사, 검색 기록 복사 버튼 변경 없음
- transcript, timestamp, evidence, approval 패널 변경 없음

## 검증
- `make e2e-test` — `12 passed (2.3m)`
- `git diff --check` — 통과

## 남은 리스크
- Playwright headless 환경에서 `navigator.clipboard.writeText`는 보안 정책상 실패할 수 있어, 복사 동작 자체의 dedicated smoke assertion은 추가하지 않았음 (fallback textarea 경로가 있어 실제 사용에서는 동작)
- dirty worktree는 여전히 넓음 (이번 라운드에서 unrelated 변경을 건드리지 않음)
