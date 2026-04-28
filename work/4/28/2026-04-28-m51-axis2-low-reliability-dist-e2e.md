# 2026-04-28 M51 Axis 2 low-reliability dist 및 E2E

## 변경 파일

- `app/static/dist/assets/index.js`
- `e2e/tests/web-smoke.spec.mjs`
- `work/4/28/2026-04-28-m51-axis2-low-reliability-dist-e2e.md`

## 사용 skill

- `e2e-smoke-triage`: 신규 browser-visible badge 계약을 isolated Playwright 시나리오로 검증했습니다.
- `work-log-closeout`: 구현 종료 기록과 실제 검증 결과를 남겼습니다.

## 변경 이유

M51 Axis 1에서 `low_reliability_active_count`와 `PreferencePanel`의 `low-reliability-count` 배지 소스가 추가되었지만, `app/static/dist/` 산출물에는 아직 반영되지 않았습니다. 이번 slice는 dist 재빌드와 해당 배지 표시 브라우저 계약 검증에만 한정했습니다.

## 핵심 변경

- `cd app/frontend && node_modules/.bin/vite build`로 frontend dist를 재빌드했습니다.
- build 결과 `app/static/dist/assets/index.js`에 `low-reliability-count`가 반영되었습니다.
- `e2e/tests/web-smoke.spec.mjs`에 `reviewed-memory loop: low-reliability-count 배지가 신뢰도 저하 활성 선호 존재 시 표시됩니다` 시나리오를 추가했습니다.
- 신규 시나리오는 `/api/preferences` mock에 `low_reliability_active_count: 1`과 `applied_count: 5`, `corrected_count: 2`, `is_highly_reliable: false`인 ACTIVE 선호를 반환하게 하고, `선호 기억` 로드 후 배지 표시와 텍스트 패턴을 확인합니다.
- `app/static/dist/assets/index.css`는 build 및 diff-check 대상이었지만 내용 변경은 없었습니다.

## 검증

- `cd app/frontend && node_modules/.bin/vite build`
  - 통과
  - `../static/dist/assets/index.css 32.91 kB`
  - `../static/dist/assets/index.js 313.44 kB`
  - Vite CJS API deprecation warning이 있었지만 build 실패는 아니었습니다.
- `ls -la app/static/dist/assets/index.js`
  - 파일 존재 확인, 크기 `315621`
- `grep -c "low-reliability-count" app/static/dist/assets/index.js`
  - `1`
- `git diff --check -- app/static/dist/assets/index.js app/static/dist/assets/index.css e2e/tests/web-smoke.spec.mjs`
  - 통과
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "reviewed-memory loop: low-reliability-count 배지가 신뢰도 저하 활성 선호 존재 시 표시됩니다" --reporter=line`
  - 통과, `1 passed (8.3s)`
  - `FORCE_COLOR`로 인해 `NO_COLOR`가 무시된다는 경고만 있었고 실패는 없었습니다.

## 남은 리스크

- 전체 Playwright smoke나 전체 unittest는 실행하지 않았습니다. 이번 handoff는 dist 반영과 신규 isolated E2E 시나리오만 요구했습니다.
- backend, TypeScript 소스, docs, approval, storage는 변경하지 않았습니다.
