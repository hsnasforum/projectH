# 2026-03-31 aggregate E2E latency triage

## 변경 파일
- `e2e/playwright.config.mjs`
- `e2e/tests/web-smoke.spec.mjs`

## 사용 skill
- 없음

## 변경 이유
- `same-session recurrence aggregate` Playwright 시나리오가 약 60초 소요되어, 원인 분리 후 timing-only 범위로 개선 요청

## 핵심 변경

### 원인 분석
1. **mock stream delay (80ms)**: 각 28-char chunk마다 80ms 대기. 12-chunk 요약 × 4회 요청 = ~29초 streaming overhead
2. **불필요한 대형 fixture**: aggregate 테스트가 724줄 fixture를 사용하여 12-chunk 요약 파이프라인을 매 요청마다 실행 (테스트에 chunking 검증이 필요하지 않음에도)

### 수정 내용
1. `LOCAL_AI_MOCK_STREAM_DELAY_MS`: `80` → `10` (streaming 동작은 유지하면서 불필요 대기 제거)
2. aggregate 테스트 전용 `shortFixturePath` 추가 (17줄, chunk threshold 미만 → single summarize call)
3. aggregate 테스트 per-test timeout: `120_000` → `60_000`
4. 기존 `longFixturePath`와 다른 테스트는 변경 없음

### 결과
- aggregate 시나리오: ~60초 → ~33초 (약 45% 감소)
- full suite: ~4.4분 → ~2.7분 (약 39% 감소)
- behavior 변경 없음, reviewed-memory semantics 영향 없음

## 검증
- `cd e2e && npx playwright test -g "same-session recurrence aggregate"` — `1 passed (34.2s)`
- `make e2e-test` — `12 passed (2.7m)`
- `git diff --check` — 통과

## 남은 리스크
- 33초는 27+ 인터랙션 단계와 4회 파일 요청 + AgentLoop 처리 오버헤드가 주 원인. 더 줄이려면 AgentLoop 자체의 처리 경로 최적화(범위 밖)가 필요
- dirty worktree가 여전히 넓음 (이번 라운드에서 unrelated 변경을 건드리지 않음)
