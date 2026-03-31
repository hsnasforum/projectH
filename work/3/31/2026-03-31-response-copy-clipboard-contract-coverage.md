# 2026-03-31 response copy clipboard contract coverage

## 변경 파일
- `e2e/tests/web-smoke.spec.mjs`

## 사용 skill
- 없음

## 변경 이유
- response copy-to-clipboard 버튼의 hidden/visible gating은 이미 smoke로 고정되었으나, 실제 clipboard write behavior는 아직 직접 검증되지 않았음

## 핵심 변경

### E2E smoke assertion 추가
- 시나리오 1 끝에 clipboard write contract 검증 추가:
  1. `page.context().grantPermissions(["clipboard-read", "clipboard-write"])` — Playwright에 clipboard 권한 부여
  2. `response-copy-text` 버튼 클릭
  3. `#notice-box`에 "응답 텍스트를 복사했습니다." 확인
  4. `navigator.clipboard.readText()`로 실제 clipboard 내용 읽기
  5. clipboard 내용에 `middleSignal` 포함 확인

### 변경하지 않은 것
- 코드 변경 없음
- docs 변경 없음 (button 자체는 이미 docs에 반영 완료)

## 검증
- `make e2e-test` — `12 passed (2.6m)`
- `git diff --check` — 통과

## 남은 리스크
- dirty worktree는 여전히 넓음 (이번 라운드에서 unrelated 변경을 건드리지 않음)
