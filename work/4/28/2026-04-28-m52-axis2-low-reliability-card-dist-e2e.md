# 2026-04-28 M52 Axis 2 low-reliability card dist 및 E2E

## 변경 파일

- `app/static/dist/assets/index.js`
- `app/static/dist/assets/index.css`
- `e2e/tests/web-smoke.spec.mjs`
- `work/4/28/2026-04-28-m52-axis2-low-reliability-card-dist-e2e.md`

## 사용 skill

- `e2e-smoke-triage`: 신규 카드 배지 browser-visible 계약을 isolated Playwright 시나리오로 검증했습니다.
- `work-log-closeout`: 구현 종료 기록과 실제 검증 결과를 남겼습니다.

## 변경 이유

M52 Axis 1에서 `PreferencePanel` 개별 카드에 `data-testid="preference-low-reliability-badge"` 배지 소스가 추가되었지만, `app/static/dist/` 산출물에는 아직 반영되지 않았습니다. 이번 slice는 dist 재빌드와 해당 카드 배지 표시 브라우저 계약 검증에만 한정했습니다.

## 핵심 변경

- `cd app/frontend && node_modules/.bin/vite build`로 frontend dist를 재빌드했습니다.
- build 결과 `app/static/dist/assets/index.js`에 `preference-low-reliability-badge`가 반영되었습니다.
- build 결과 `app/static/dist/assets/index.css`도 갱신되었습니다.
- `e2e/tests/web-smoke.spec.mjs`에 `reviewed-memory loop: preference-low-reliability-badge가 신뢰도 저하 활성 선호 카드에 표시됩니다` 시나리오를 추가했습니다.
- 신규 시나리오는 저하 조건을 만족하는 ACTIVE 선호 1건과 `applied_count: 2`인 측정 중 ACTIVE 선호 1건을 함께 mock하고, 카드 배지가 1개만 표시되며 텍스트가 `신뢰도 저하`를 포함하는지 확인합니다.

## 검증

- `cd app/frontend && node_modules/.bin/vite build`
  - 통과
  - `../static/dist/assets/index.css 33.04 kB`
  - `../static/dist/assets/index.js 313.68 kB`
  - Vite CJS API deprecation warning이 있었지만 build 실패는 아니었습니다.
- `ls -la app/static/dist/assets/index.js`
  - 파일 존재 확인, 크기 `315871`
- `grep -c "preference-low-reliability-badge" app/static/dist/assets/index.js`
  - `1`
- `git diff --check -- app/static/dist/assets/index.js app/static/dist/assets/index.css e2e/tests/web-smoke.spec.mjs`
  - 통과
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "reviewed-memory loop: preference-low-reliability-badge가 신뢰도 저하 활성 선호 카드에 표시됩니다" --reporter=line`
  - 통과, `1 passed (7.3s)`
  - `FORCE_COLOR`로 인해 `NO_COLOR`가 무시된다는 경고만 있었고 실패는 없었습니다.

## 남은 리스크

- 전체 Playwright smoke나 전체 unittest는 실행하지 않았습니다. 이번 handoff는 dist 반영과 신규 isolated E2E 시나리오만 요구했습니다.
- docs, TypeScript 소스, backend, approval, storage는 변경하지 않았습니다.
