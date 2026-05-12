# 2026-05-08 M119 Axis 2 injection correction badge

## 변경 파일

- `app/frontend/src/api/client.ts`
- `app/frontend/src/components/PreferencePanel.tsx`
- `app/static/dist/assets/index.js`
- `e2e/tests/web-smoke.spec.mjs`

## 사용 skill

- `work-log-closeout`: 구현 라운드 종료 기록 형식과 실제 검증 사실 정리에 사용.

## 변경 이유

- `/api/preferences`가 이미 노출하는 `injection_correction_count` / `injection_correction_rate`를 프런트 타입과 선호 주입 배지 UI에 반영하기 위해 변경했다.
- 기존 주입 횟수 배지가 적용률만 표시하던 상태라, 교정률이 있는 선호의 주입 신뢰도 정보를 사용자가 바로 볼 수 없었다.

## 핵심 변경

- `PreferenceRecord` 타입에 `injection_correction_count?: number | null`와 `injection_correction_rate?: number | null`를 추가했다.
- `preferenceInjectedLabel()`에서 `injection_correction_rate > 0`이면 `Math.round(rate * 100)`으로 교정률을 계산해 `N회 주입 (A% 적용 · R% 교정)` 형식으로 표시하게 했다.
- 교정률이 없거나 0이면 기존 `N회 주입 (A% 적용)` / `N회 주입` 표시를 유지했다.
- `preference injected count badge appears for injected preferences` 스모크 픽스처에 `injection_correction_count: 1`, `injection_correction_rate: 0.25`를 추가하고 기대 문구를 `4회 주입 (50% 적용 · 25% 교정)`으로 갱신했다.
- `npm run build`는 `app/static/dist/assets` 삭제 단계에서 `EROFS`로 실패했다. 같은 소스에서 `/tmp/projectH-frontend-dist`로 Vite 빌드를 성공시킨 뒤, 해시가 달라진 `assets/index.js`만 `app/static/dist/assets/index.js`에 반영했다. `index.css`와 `index.html`은 임시 빌드 결과와 기존 파일 해시가 동일했다.

## 검증

- `cd app/frontend && npm run build`
  - FAIL: `EROFS: read-only file system, rmdir '/home/xpdlqj/code/projectH/app/static/dist/assets'`
- `cd app/frontend && npx vite build --emptyOutDir false`
  - FAIL: `EROFS: read-only file system, open '/home/xpdlqj/code/projectH/app/static/dist/assets/index.js'`
- `cd app/frontend && npx vite build --outDir /tmp/projectH-frontend-dist --emptyOutDir true`
  - PASS: 임시 출력 위치 빌드 성공.
- `cp /tmp/projectH-frontend-dist/assets/index.js app/static/dist/assets/index.js`
  - PASS: 생성된 JS 산출물 반영.
- `sha256sum /tmp/projectH-frontend-dist/assets/index.js app/static/dist/assets/index.js`
  - PASS: 두 파일 모두 `64333ac0e4b29d68f315f4bf2258cd69f18df45a9b07c59d702e87430251cf96`.
- `cd app/frontend && npx tsc --noEmit`
  - PASS.
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "preference injected count badge" --reporter=line`
  - PASS: 1개 테스트 통과.
- `git diff --check -- app/frontend/src/api/client.ts app/frontend/src/components/PreferencePanel.tsx e2e/tests/web-smoke.spec.mjs`
  - PASS.
- `git diff --check -- app/static/dist/assets/index.js`
  - PASS.

## 남은 리스크

- 지정된 단일 Playwright 스모크만 실행했고 전체 E2E나 전체 프런트 회귀는 실행하지 않았다.
- `npm run build`의 기본 출력 경로 직접 빌드는 현재 실행 환경에서 `EROFS`로 실패했다. 소스와 동일한 Vite 빌드를 `/tmp`에서 수행해 산출 JS를 반영했지만, 원인 자체는 이번 구현 범위 밖으로 남겼다.
