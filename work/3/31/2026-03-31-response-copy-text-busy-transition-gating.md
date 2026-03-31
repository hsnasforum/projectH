# 2026-03-31 response copy text button busy-transition gating fix

## 변경 파일
- `app/templates/index.html`
- `e2e/tests/web-smoke.spec.mjs`

## 사용 skill
- 없음

## 변경 이유
- 기존 응답이 있던 상태에서 새 요청을 시작하면 `responseText`가 비워지지만 "응답 복사" 버튼이 visible/enabled로 남아있는 hole

## 핵심 변경

### busy-transition gating
- `responseText.textContent = ""` 이 실행되는 7개 경로 모두에 `showElement(responseCopyTextButton, false)` 추가:
  - follow-up prompt 시작
  - stream request 시작
  - corrected-save 요청 시작
  - approve 시작
  - reissue 시작
  - reject 시작
  - general request 시작

### smoke assertion 추가
- 시나리오 1에서 2번째 요청 추가:
  - 첫 응답 후 `response-copy-text` visible 확인 (기존)
  - 2번째 요청 클릭 직후 `response-copy-text` hidden 확인
  - 2번째 응답 도착 후 `response-copy-text` visible 확인

## 검증
- `make e2e-test` — `12 passed (2.4m)`
- `git diff --check` — 통과

## 남은 리스크
- dirty worktree는 여전히 넓음 (이번 라운드에서 unrelated 변경을 건드리지 않음)
