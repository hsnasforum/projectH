# 2026-05-08 M120 Axis 2 injection demotion badge

## 변경 파일

- `app/frontend/src/components/PreferencePanel.tsx`
- `app/static/dist/assets/index.js`
- `e2e/tests/web-smoke.spec.mjs`
- `work/5/8/2026-05-08-m120-axis2-injection-demotion-badge.md`

## 사용 skill

- `work-log-closeout`: 구현 라운드 종료 기록 형식과 실제 검증 사실 정리에 사용했다.

## 변경 이유

- M120 Axis 1에서 확정된 `injected_count >= 3` 및 `injection_correction_rate > 0.25` 강등 기준을 사용자가 선호 주입 배지에서 바로 식별할 수 있게 하기 위해 변경했다.
- API와 타입은 이미 완비되어 있어 `PreferencePanel.tsx`, targeted E2E, dist JS만 갱신했다.

## 핵심 변경

- `PreferencePanel.tsx`에 `INJECTION_CORRECTION_DEMOTION_RATE = 0.25`와 `isDemotedByInjectionCorrection()` 헬퍼를 추가했다.
- 주입 배지가 M120 강등 조건에 해당하면 amber 계열 스타일을 사용하고, `title`에 `신뢰도 자동 강등됨` 안내를 표시하게 했다.
- 기존 `preference injected count badge appears for injected preferences` E2E 픽스처를 `injection_correction_rate: 0.4`로 조정해 강등 조건을 검증했다.
- E2E 기대값에 배지 텍스트 `4회 주입 (50% 적용 · 40% 교정)`, title, amber class 검증을 추가했다.
- `/tmp/projectH-frontend-dist` 빌드 산출물의 `assets/index.js`를 `app/static/dist/assets/index.js`에 반영했고 sha256 일치를 확인했다.

## 검증

- `cd app/frontend && npx vite build --outDir /tmp/projectH-frontend-dist --emptyOutDir true`
  - PASS.
- `cp /tmp/projectH-frontend-dist/assets/index.js app/static/dist/assets/index.js && sha256sum /tmp/projectH-frontend-dist/assets/index.js app/static/dist/assets/index.js`
  - PASS: 두 파일 모두 `bc2d7078155f67350153cc0e76389918e62eb82eb1a0783b0cabce45be0af60b`.
- `cd app/frontend && npx tsc --noEmit`
  - PASS.
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "preference injected count badge" --reporter=line`
  - PASS: 1개 테스트 통과.
- `git diff --check -- app/frontend/src/components/PreferencePanel.tsx e2e/tests/web-smoke.spec.mjs app/static/dist/assets/index.js`
  - PASS.
- `rg -n "신뢰도 자동 강등됨|bg-amber-500|INJECTION_CORRECTION_DEMOTION|injection_correction_rate" app/frontend/src/components/PreferencePanel.tsx e2e/tests/web-smoke.spec.mjs app/static/dist/assets/index.js`
  - PASS: 소스, E2E, dist JS 반영 확인.

## 남은 리스크

- 이번 라운드는 지정된 단일 Playwright 스모크만 실행했고 전체 E2E는 실행하지 않았다.
- `MILESTONES` / `TASK_BACKLOG` doc-sync는 handoff 금지 범위라 수행하지 않았다.
- `PR #113`, `PR #114`, `PR #115` draft merge gate와 M121 방향 결정은 이번 implement handoff 범위 밖이다.
