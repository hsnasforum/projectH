# 2026-03-31 feedback and content handler post-refresh dependency check

## 변경 파일
- `app/templates/index.html`

## 사용 skill
- 없음

## 변경 이유
- 이전 라운드에서 correction / candidate handler의 trailing `fetchSessions()` 제거가 safe하게 통과
- 동일 패턴을 feedback / content-verdict / content-reason-note handler로 확장 가능한지 dependency check 수행

## 핵심 변경

### dependency 분석

| handler | 새 메시지 추가 | `pending_approval_count` 변경 | `last_message_preview` 변경 | sidebar 즉시 갱신 E2E contract |
|---|---|---|---|---|
| `submitFeedback` | 아니오 | 아니오 | 아니오 | 없음 |
| `submitContentVerdict` | 아니오 | 아니오 | 아니오 | 없음 |
| `submitContentReasonNote` | 아니오 | 아니오 | 아니오 | 없음 |

- `updated_at`만 기술적으로 변경되지만 sidebar에서 "방금"→"방금"으로 무의미
- E2E에서 `session-item`, `session-list` 관련 assertion 전무
- feedback submit 자체를 테스트하는 E2E 시나리오 없음

### 수정 내용
3개 handler에서 `await fetchSessions()` 제거:
1. `submitFeedback` (피드백 기록)
2. `submitContentVerdict` (내용 거절)
3. `submitContentReasonNote` (거절 메모)

`renderSession(data.session)` 및 후속 render 호출은 모두 유지.

### 결과
- content-verdict 사용 시나리오에서 개선:
  - test 6 (늦은 내용 거절): 13.1s → 11.3s
  - test 7 (내용 거절 + supersede): 16.4s → 12.9s
  - test 9 (corrected-save + 내용 거절): 17.4s → 14.5s
- full suite: 2.4분 → 2.3분
- aggregate 시나리오: 유지 (22~23초, 이번 handler는 aggregate 흐름에서 미사용)

## 검증
- `cd e2e && npx playwright test -g "same-session recurrence aggregate"` — `1 passed (24.5s)`, 시나리오 22.8s
- `make e2e-test` — `12 passed (2.3m)`
- `git diff --check` — 통과

## 남은 리스크
- 모든 non-streaming action handler에서 trailing `fetchSessions()` 제거가 완료됨
- streaming action handler(`submitStreamPayload` 기반)와 `loadSession` 내부의 `fetchSessions()`는 별도 맥락이므로 이번 범위 밖
- `renderSession()` 자체의 full re-render 비용은 여전히 남아 있음
- dirty worktree는 여전히 넓음 (이번 라운드에서 unrelated 변경을 건드리지 않음)
