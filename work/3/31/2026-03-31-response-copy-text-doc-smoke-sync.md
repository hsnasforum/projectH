# 2026-03-31 response copy text button doc and smoke sync

## 변경 파일
- `README.md`
- `docs/PRODUCT_SPEC.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `e2e/tests/web-smoke.spec.mjs`

## 사용 skill
- 없음

## 변경 이유
- 이전 라운드에서 추가한 response copy text 버튼이 root docs와 smoke에 고정되지 않아 verify에서 `not_ready` 판정

## 핵심 변경

### docs 반영 (3개 파일)
- `README.md`: "response origin badge" 아래에 "response copy-to-clipboard button" 추가
- `docs/PRODUCT_SPEC.md`: 동일 위치에 동일 항목 추가
- `docs/ACCEPTANCE_CRITERIA.md`: "The response panel header includes a copy-to-clipboard button for the response text." 추가

### smoke assertion 추가 (1개)
- 시나리오 1 "파일 요약 후 근거와 요약 구간이 보입니다"에 추가:
  - `response-copy-text` 버튼이 visible인지 확인
- clipboard write 성공/실패는 headless 환경 보안 정책 때문에 검증하지 않음

## 검증
- `make e2e-test` — `12 passed (2.3m)`
- `git diff --check` — 통과

## 남은 리스크
- dirty worktree는 여전히 넓음 (이번 라운드에서 unrelated 변경을 건드리지 않음)
