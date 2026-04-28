# 2026-04-28 M61 Axis 2 Correction Summary E2E Smoke

## 변경 파일
- `e2e/tests/web-smoke.spec.mjs`
- `work/4/28/2026-04-28-m61-axis2-correction-summary-e2e-smoke.md`

## 사용 skill
- `e2e-smoke-triage`: `/api/corrections/summary` HTTP 응답 shape를 격리 Playwright 시나리오로 고정했습니다.
- `work-log-closeout`: 변경 파일, 실행 검증, 남은 리스크를 구현 closeout으로 정리했습니다.

## 변경 이유
- M61 Axis 1에서 `GET /api/corrections/summary` backend endpoint와 단위 테스트가 추가되었고, 이번 handoff는 HTTP 계약을 E2E smoke 격리 시나리오로 고정하는 것이었습니다.
- backend, frontend, dist를 변경하지 않고 Playwright route mock 기반으로 응답 shape만 검증했습니다.

## 핵심 변경
- `e2e/tests/web-smoke.spec.mjs`에 신규 시나리오를 추가했습니다.
- 시나리오 이름: `corrections: GET /api/corrections/summary 응답이 ok, total, by_status, top_recurring_fingerprints를 포함합니다`
- `page.route(/\/api\/corrections\/summary$/, ...)`로 `{ ok, total, by_status, top_recurring_fingerprints }` 응답을 mock 처리했습니다.
- `/app-preview` 이동 후 브라우저 `fetch("/api/corrections/summary")`로 응답 status와 필드 존재를 확인했습니다.
- 기존 E2E 시나리오, backend, frontend, dist는 변경하지 않았습니다.

## 검증
- 통과: `git diff --check -- e2e/tests/web-smoke.spec.mjs`
- 통과: `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "corrections: GET /api/corrections/summary 응답이 ok, total, by_status, top_recurring_fingerprints를 포함합니다" --reporter=line` (1 passed, 12.4s)

## 남은 리스크
- 이번 변경은 격리 smoke 시나리오 1개 추가에 한정되어 전체 `make e2e-test`는 실행하지 않았습니다.
- 실제 backend 데이터 경로는 M61 Axis 1 단위 테스트와 verify 기록에 의존하며, 이번 시나리오는 mock 응답 shape 계약을 고정합니다.
