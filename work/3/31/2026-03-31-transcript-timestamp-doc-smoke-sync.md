# 2026-03-31 transcript timestamp doc and smoke sync

## 변경 파일
- `README.md`
- `docs/PRODUCT_SPEC.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `e2e/tests/web-smoke.spec.mjs`

## 사용 skill
- 없음

## 변경 이유
- 이전 라운드에서 추가한 transcript message timestamp UI surface가 root docs와 dedicated smoke에 고정되지 않은 상태
- verify에서 "이 surface를 shipped contract로 굳힐 것이라면 doc sync와 smoke assertion이 더 정직하다"는 지적

## 핵심 변경

### docs 반영 (3개 파일)
- `README.md`: "conversation timeline" → "conversation timeline with per-message timestamps"
- `docs/PRODUCT_SPEC.md`: 동일
- `docs/ACCEPTANCE_CRITERIA.md`: "current conversation timeline" → "current conversation timeline with per-message timestamps"
- `README.md` smoke 목록 시나리오 1: evidence/summary-range panels → "+ per-message timestamps in the transcript"

### smoke assertion 추가 (1개)
- 시나리오 1 "파일 요약 후 근거와 요약 구간이 보입니다"에 추가:
  - `#transcript .message-when` 요소가 2개 존재 (user 1 + assistant 1)
  - 첫 번째 `.message-when`이 비어 있지 않음

### 변경하지 않은 것
- timestamp formatting 자체 변경 없음
- transcript UI 추가 확장 없음
- handler-level latency 작업 재개 없음

## 검증
- `make e2e-test` — `12 passed (2.3m)`
- `git diff --check` — 통과

## 남은 리스크
- `formatWhen`은 full locale date-time을 표시하므로 같은 날 메시지에서는 시간만 표시하는 compact format이 더 깔끔할 수 있음 (later refinement)
- dirty worktree는 여전히 넓음 (이번 라운드에서 unrelated 변경을 건드리지 않음)
