# 2026-04-28 M62 Axis 1 Correction Summary Frontend 표시

## 변경 파일
- `app/frontend/src/api/client.ts`
- `app/frontend/src/components/PreferencePanel.tsx`
- `docs/MILESTONES.md`
- `work/4/28/2026-04-28-m62-axis1-correction-summary-frontend.md`

## 사용 skill
- `doc-sync`: M62 Axis 1 진행 사실을 `docs/MILESTONES.md`에만 반영했습니다.
- `e2e-smoke-triage`: browser-visible 표시 변경이지만 이번 handoff가 dist 재빌드와 E2E를 Axis 2로 분리하므로 TypeScript와 diff 검증까지만 수행했습니다.
- `work-log-closeout`: 변경 파일, 실행 검증, 남은 리스크를 구현 closeout으로 정리했습니다.

## 변경 이유
- M61에서 `GET /api/corrections/summary` backend endpoint와 E2E 응답 shape가 고정되었고, 이번 slice는 해당 요약을 선호 패널에 조용히 표시하는 frontend 연결이었습니다.
- preference audit와 함께 correction summary를 불러와 사용자가 교정 전체 개수와 활성 교정 개수를 볼 수 있도록 했습니다.

## 핵심 변경
- `app/frontend/src/api/client.ts`에 `CorrectionSummary` 타입과 `fetchCorrectionSummary()`를 추가했습니다.
- `PreferencePanel.tsx`의 `load()`에서 `fetchPreferences()`, `fetchPreferenceAudit()`, `fetchCorrectionSummary()`를 병렬 호출하도록 확장했습니다.
- correction summary fetch 실패는 `catch(() => null)`로 처리해 기존 선호/감사 데이터 로딩을 막지 않도록 했습니다.
- 선호 패널 header의 적용/교정 누적 라인 아래에 `교정 전체 N개 · 활성 N개` 컴팩트 텍스트를 표시하도록 했습니다.
- `docs/MILESTONES.md`에 M62 Correction Analytics Visibility / Axis 1 항목을 추가했습니다.

## 검증
- 통과: `app/frontend/node_modules/.bin/tsc --noEmit --project app/frontend/tsconfig.json`
- 통과: `git diff --check -- app/frontend/src/api/client.ts app/frontend/src/components/PreferencePanel.tsx docs/MILESTONES.md`

## 남은 리스크
- handoff 경계에 따라 `app/static/dist/` 재빌드, Playwright/E2E, backend 테스트는 실행하지 않았습니다.
- `data-testid`와 browser smoke 고정은 Axis 2 대상으로 남겼습니다.
- `top_recurring_fingerprints`는 타입과 fetch payload에 포함되지만, 이번 Axis 1 화면 표시는 handoff 지정 문구인 total/active 컴팩트 표시로 제한했습니다.
