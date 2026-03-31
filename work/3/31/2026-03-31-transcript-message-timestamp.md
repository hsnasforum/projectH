# 2026-03-31 transcript message timestamp

## 변경 파일
- `app/templates/index.html`

## 사용 skill
- 없음

## 변경 이유
- E2E latency 미세최적화 축에서 벗어나, user-visible 가치 항목으로 전환
- transcript의 각 메시지에 타임스탬프가 없어 다중 메시지 세션에서 대화 흐름 파악이 어려웠음
- 모든 메시지에 `created_at`이 이미 저장되어 있으나 UI에서 미표시

## 핵심 변경

### 추가된 UI surface
- `renderTranscript`의 각 메시지 헤더에 `created_at` 타임스탬프 표시
- 기존 `formatWhen()` 함수 재사용 (한국어 locale 날짜/시간)
- `.message-when` 스타일: 11px, muted color, opacity 0.7로 역할 라벨 옆에 표시
- role 라벨과 status badge 사이에 위치

### 변경하지 않은 것
- 메시지 데이터 구조 변경 없음
- 기존 `formatWhen` 로직 변경 없음
- response-box, evidence, summary-chunks 등 기존 패널 영향 없음

## 검증
- `make e2e-test` — `12 passed (2.2m)`
- `git diff --check` — 통과

## 남은 리스크
- `formatWhen`은 `toLocaleString("ko-KR")`로 전체 날짜+시간을 표시하므로, 같은 날 메시지라면 시간만 표시하는 것이 더 깔끔할 수 있음 (later refinement)
- dirty worktree는 여전히 넓음 (이번 라운드에서 unrelated 변경을 건드리지 않음)
