# 2026-03-31 aggregate E2E remaining latency attribution

## 변경 파일
- 없음 (이번 라운드는 병목 분리 결과만 기록)

## 사용 skill
- 없음

## 변경 이유
- 이전 라운드에서 aggregate 시나리오를 ~60초 → ~33초로 줄였으나, 남은 32~34초의 세부 병목 분리가 필요

## 핵심 결과: step별 timing breakdown

임시 timing probe 테스트를 작성하여 각 단계의 소요 시간을 측정했습니다.

### 측정 결과 (대표 1회)

| 단계 | 시간 | 비고 |
|---|---|---|
| page-load | 3.0s | goto + networkidle (500ms idle wait 포함) |
| prepare-session | 1.0s | new-session click + advanced settings + fill |
| **request-1-response** | 1.1s | 파일 읽기 + 요약 + streaming (cold path) |
| request-1-ui-checks | 0.1s | reviewQueue/aggregateTrigger hidden 확인 |
| **correction-1-submit** | 3.6s | POST /api/correction + renderSession + fetchSessions |
| **confirmation-1** | 2.2s | POST /api/candidate-confirmation + renderSession + fetchSessions |
| review-queue-1-check | 0.2s | |
| **request-2-response** | 0.4s | warm path, short fixture |
| **correction-2-submit** | 4.0s | 두 번째 correction, session이 더 큼 |
| aggregate-trigger-visible | 0.4s | |
| **emit-transition** | 1.4s | POST /api/aggregate-transition + renderSession + fetchSessions |
| emitted-payload-fetch | 0.7s | GET /api/session |
| **apply-transition** | 2.2s | POST /api/aggregate-transition-apply + renderSession + fetchSessions |
| **confirm-result** | 2.1s | POST /api/aggregate-transition-result + renderSession + fetchSessions |
| result-ui-check | 0.7s | |
| **request-3-response** | 0.5s | active memory prefix 포함 |
| **stop-transition** | 3.3s | POST /api/aggregate-transition-stop + renderSession + fetchSessions |
| **request-4-response** | 0.2s | |
| **reverse-transition** | 1.9s | POST /api/aggregate-transition-reverse + renderSession + fetchSessions |
| **conflict-check** | 2.6s | POST /api/aggregate-transition-conflict-check + renderSession + fetchSessions |

### 카테고리별 합산

| 카테고리 | 시간 | 비율 |
|---|---|---|
| 파일 요청 사이클 (4×) | ~2.2s | 6.9% |
| correction + confirmation (3×) | ~9.8s | 30.6% |
| transition API (6×: emit, apply, confirm, stop, reverse, conflict) | ~14.1s | 44.1% |
| page load + session prep | ~4.0s | 12.5% |
| 기타 UI 검증 | ~1.9s | 5.9% |

### 각 handler 내부 비용 분해

correction과 transition handler가 2~4초 걸리는 원인:
1. **POST API 호출**: ~100-300ms (서버 처리 자체는 빠름)
2. **`renderSession()` 전체 re-render**: ~500-1500ms (메시지, correction editor, candidate box, aggregate trigger, review queue 모두 재렌더링)
3. **`await fetchSessions()` 추가 round trip**: ~200-500ms (각 handler 마지막에 세션 목록 갱신)
4. **DOM 안정화 + Playwright 폴링**: ~100-300ms

`renderSession()`이 모든 handler에서 호출되며, aggregate 테스트 흐름에서 약 10회 이상 실행됩니다.

### 판정: 추가 test-level trimming 불가

- 파일 요청 사이클(2.2s)은 이전 라운드에서 이미 최적화 완료 (short fixture + delay 감소)
- `expect` timeout(15s)은 병목이 아님 — Playwright는 조건 충족 즉시 통과
- `networkidle` wait(~500ms)는 page load 1회에만 적용
- 남은 28~30초는 correction/transition handler의 `renderSession()` re-render + `fetchSessions()` round trip이 지배적
- 이 비용을 줄이려면 app의 render-after-every-action 패턴을 변경해야 하며, 이는 timing-only 범위를 벗어남

## 검증
- `cd e2e && npx playwright test -g "same-session recurrence aggregate"` — `1 passed (33.0s)`
- `make e2e-test` — `12 passed (2.7m)`
- `git diff --check` — 통과

## 남은 리스크
- aggregate 시나리오 32~34초는 현재 timing-only 범위에서 더 줄일 여지가 없음
- 추가 개선이 필요하면 app 레벨에서 `renderSession()` 경량화 또는 `fetchSessions()` 호출 감소를 검토해야 하며, 이는 별도 product decision이 필요
- dirty worktree는 여전히 넓음 (이번 라운드에서 unrelated 변경을 건드리지 않음)
