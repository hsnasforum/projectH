# 2026-03-31 transcript timestamp compact format

## 변경 파일
- `app/templates/index.html`

## 사용 skill
- 없음

## 변경 이유
- 이전 라운드에서 추가한 transcript 타임스탬프가 같은 날 메시지에도 full locale date-time을 표시하여 약간 장황했음

## 핵심 변경

### 추가된 함수
- `formatMessageWhen(value)`: transcript 전용 compact timestamp formatter
  - same-day 메시지: time-only 표시 (`오후 02:30` 등)
  - older-day / cross-day 메시지: full date-time 표시 (기존 `formatWhen`과 동일)
  - `toLocaleTimeString("ko-KR", { hour: "2-digit", minute: "2-digit" })` 사용

### 변경하지 않은 것
- 기존 `formatWhen()`: session list, approval card 등에서 사용 — 변경 없음
- smoke assertion: `.message-when`이 비어 있지 않음 확인 — compact format에서도 동일하게 통과
- docs: 이전 라운드에서 이미 "per-message timestamps" 반영 완료

## 검증
- `make e2e-test` — `12 passed (2.3m)`
- `git diff --check` — 통과

## 남은 리스크
- dirty worktree는 여전히 넓음 (이번 라운드에서 unrelated 변경을 건드리지 않음)
