# 2026-03-31 response copy text button empty-state gating

## 변경 파일
- `app/templates/index.html`
- `e2e/tests/web-smoke.spec.mjs`

## 사용 skill
- 없음

## 변경 이유
- 빈 응답이나 placeholder 상태에서도 "응답 복사" 버튼이 보이고 클릭하면 빈 텍스트 복사 성공 notice가 뜨는 UX risk

## 핵심 변경

### 버튼 state gating
- HTML 초기 상태: `hidden` 속성 추가
- `renderSession`: 실제 assistant 응답이 있으면 `showElement(true)`, placeholder 상태면 `showElement(false)`
- `renderResult`: 응답 텍스트가 있으면 `showElement(true)`
- streaming `text_delta`: 첫 delta 도착 시 `showElement(true)`
- streaming `text_replace`: 텍스트가 있으면 `showElement(true)`, 없으면 `showElement(false)`

### smoke assertion 추가
- 시나리오 1에서:
  - `prepareSession` 직후: `response-copy-text` hidden 확인
  - 응답 도착 후: `response-copy-text` visible 확인 (기존)

### docs
- 이전 라운드에서 이미 "copy-to-clipboard button" 반영 완료, 추가 wording 변경 불필요

## 검증
- `make e2e-test` — `12 passed (2.4m)`
- `git diff --check` — 통과

## 남은 리스크
- dirty worktree는 여전히 넓음 (이번 라운드에서 unrelated 변경을 건드리지 않음)
