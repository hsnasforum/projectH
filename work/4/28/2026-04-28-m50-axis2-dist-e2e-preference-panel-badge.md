# 2026-04-28 M50 Axis 2 dist 재빌드 및 PreferencePanel 배지 E2E

## 변경 파일

- `app/static/dist/assets/index.js`
- `app/static/dist/assets/index.css`
- `e2e/tests/web-smoke.spec.mjs`
- `work/4/28/2026-04-28-m50-axis2-dist-e2e-preference-panel-badge.md`

## 사용 skill

- `e2e-smoke-triage`: 신규 브라우저 계약 시나리오의 selector, mock flow, 격리 실행 범위를 확인.
- `work-log-closeout`: 구현 종료 기록을 표준 `/work` 형식으로 작성.

## 변경 이유

- M50 Axis 1에서 source UI에 추가한 `preference-last-applied-badge`가 `app/static/dist/`에는 아직 반영되지 않았다.
- 마지막 assistant 응답의 `applied_preferences` fingerprint가 `PreferencePanel`의 ACTIVE 선호 카드 badge로 이어지는 브라우저 계약을 Playwright 격리 시나리오로 고정해야 했다.

## 핵심 변경

- `cd app/frontend && node_modules/.bin/vite build`로 dist를 재빌드했다.
- 빌드 결과 `app/static/dist/assets/index.js`에 `data-testid="preference-last-applied-badge"`와 "이번 응답 반영" 문구가 포함됨을 확인했다.
- Tailwind build 결과로 `app/static/dist/assets/index.css`도 함께 갱신됐다. `bg-violet-50`, `text-violet-500` 등 Axis 1 badge class 반영으로 인한 생성물 변경이다.
- `e2e/tests/web-smoke.spec.mjs`에 신규 시나리오 `"reviewed-memory loop: 활성화된 선호가 PreferencePanel 이번 응답 반영 배지에 표시됩니다"`를 추가했다.
- 신규 시나리오는 sync 버튼, 활성화 버튼, mock chat stream을 통해 ACTIVE + `is_highly_reliable === true` 선호와 `applied_preferences` fingerprint 일치를 만든 뒤 message bubble badge와 PreferencePanel badge를 순서대로 확인한다.
- `app/static/dist/index.html`은 빌드 후 변경되지 않았다.

## 검증

- `cd app/frontend && node_modules/.bin/vite build`
  - 통과. Vite build 완료.
- `ls -la app/static/dist/assets/index.js`
  - 통과. `Apr 28 11:17` mtime와 `314149` bytes 확인.
- `git diff --check -- app/static/dist/assets/index.js app/static/dist/index.html e2e/tests/web-smoke.spec.mjs`
  - 통과.
- `git diff --check -- app/static/dist/assets/index.js app/static/dist/assets/index.css app/static/dist/index.html e2e/tests/web-smoke.spec.mjs`
  - 통과. 생성된 CSS 변경까지 추가 확인.
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "reviewed-memory loop: 활성화된 선호가 PreferencePanel 이번 응답 반영 배지에 표시됩니다" --reporter=line`
  - 통과. `1 passed (16.4s)`.

## 남은 리스크

- 핸드오프 범위에 따라 신규 시나리오만 격리 실행했고 전체 `make e2e-test`는 실행하지 않았다.
- 신규 시나리오는 PreferencePanel 브라우저 계약을 안정적으로 고정하기 위해 관련 API와 chat stream을 test-local mock route로 제어한다. 실제 backend 주입 조건 자체는 M49/M50 Axis 1의 기존 단위 및 타입 검증에 의존한다.
