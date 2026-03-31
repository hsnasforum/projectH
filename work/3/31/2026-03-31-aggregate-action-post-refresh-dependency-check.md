# 2026-03-31 aggregate action post-refresh dependency check

## 변경 파일
- `app/templates/index.html`

## 사용 skill
- 없음

## 변경 이유
- 이전 라운드의 timing attribution에서 aggregate transition handler 6개의 `fetchSessions()` round trip이 각 ~600ms씩 불필요하게 소비되는 것을 확인
- 각 handler의 `renderSession(data.session)`과 `fetchSessions()`가 현재 UI contract에 실제로 필요한지 dependency check 수행

## 핵심 변경

### dependency 분석 결과

| 호출 | 필요 여부 | 근거 |
|---|---|---|
| `renderSession(data.session)` | **필수** | aggregate trigger box의 버튼/라벨 상태가 transition마다 변경되므로 re-render 필요 |
| `await fetchSessions()` | **불필요** | session list sidebar는 `title`, `updated_at`, `pending_approval_count`, `last_message_preview`만 표시. aggregate transition은 이 중 어떤 것도 사용자에게 의미 있게 변경하지 않음 |

### 수정 내용
6개 aggregate transition handler에서 `await fetchSessions()` 제거:
1. `/api/aggregate-transition` (emit)
2. `/api/aggregate-transition-apply`
3. `/api/aggregate-transition-result`
4. `/api/aggregate-transition-stop`
5. `/api/aggregate-transition-reverse`
6. `/api/aggregate-transition-conflict-check`

`renderSession(data.session)`은 모두 유지.

### 결과
- aggregate 시나리오: 32~34초 → 27~28초 (약 5~6초 감소)
- full suite: 2.7분 → 2.5분
- 전체 최적화 누적 (원래 60초 기준): 60초 → 27초 (55% 감소)

## 검증
- `cd e2e && npx playwright test -g "same-session recurrence aggregate"` — `1 passed (29.8s)`, 시나리오 27.1s
- `make e2e-test` — `12 passed (2.5m)`
- `git diff --check` — 통과

## 남은 리스크
- correction/confirmation handler에도 동일한 `fetchSessions()` 패턴이 있으나, 이번 라운드는 aggregate handler 범위만 다룸
- `renderSession()` 자체의 full re-render 비용(~500-1500ms per call)은 여전히 남아 있으나, 이는 partial rendering 등 구조적 변경이 필요
- dirty worktree는 여전히 넓음 (이번 라운드에서 unrelated 변경을 건드리지 않음)
