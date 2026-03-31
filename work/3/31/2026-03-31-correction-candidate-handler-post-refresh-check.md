# 2026-03-31 correction and candidate handler post-refresh dependency check

## 변경 파일
- `app/templates/index.html`

## 사용 skill
- 없음

## 변경 이유
- 이전 라운드에서 aggregate handler 6개의 `fetchSessions()` 제거가 safe하게 통과
- 동일 패턴을 correction / candidate-confirmation / candidate-review handler로 확장 가능한지 dependency check 수행

## 핵심 변경

### dependency 분석

**sidebar 표시 항목과 각 handler 후 변경 여부:**

| sidebar 필드 | correction 후 | candidate-confirmation 후 | candidate-review 후 |
|---|---|---|---|
| `title` | 변경 없음 | 변경 없음 | 변경 없음 |
| `updated_at` | 기술적으로 변경 (하지만 "방금"→"방금") | 동일 | 동일 |
| `pending_approval_count` | 변경 없음 | 변경 없음 | 변경 없음 |
| `last_message_preview` | 변경 없음 (`corrected_text` 수정, `text`는 유지) | 변경 없음 | 변경 없음 |

**E2E contract 확인:**
- E2E 테스트에서 sidebar(`session-item`, `session-list`) 관련 assertion이 전혀 없음
- sidebar 즉시 갱신은 current shipped contract에 해당하지 않음

### 수정 내용
3개 handler에서 `await fetchSessions()` 제거:
1. `submitCorrection` (correction 기록)
2. `submitCandidateConfirmation` (수정 방향 확인)
3. `submitCandidateReviewAccept` (검토 후보 수락)

`renderSession(data.session)` 및 후속 render 호출은 모두 유지.

### 결과
- aggregate 시나리오: 27~28초 → 22~23초 (약 5초 감소, correction 2회 + confirmation 1회 분)
- full suite: 2.5분 → 2.4분
- correction/confirmation을 사용하는 다른 시나리오도 개선:
  - test 9 (corrected-save long path): 20.0s → 17.4s
  - test 10 (candidate confirmation path): 23.0s → 16.4s
- 전체 누적 (원래 60초 기준): 60초 → 22초 (63% 감소)

## 검증
- `cd e2e && npx playwright test -g "same-session recurrence aggregate"` — `1 passed (23.5s)`, 시나리오 22.1s
- `make e2e-test` — `12 passed (2.4m)`
- `git diff --check` — 통과

## 남은 리스크
- feedback / content-verdict / content-reason-note handler에도 동일 패턴이 남아 있으나 이번 범위 밖
- `renderSession()` 자체의 full re-render 비용은 여전히 남아 있음
- dirty worktree는 여전히 넓음 (이번 라운드에서 unrelated 변경을 건드리지 않음)
