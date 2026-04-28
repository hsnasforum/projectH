# 2026-04-28 M62 Axis 2 Correction Summary dist/E2E

## 변경 파일
- `app/frontend/src/components/PreferencePanel.tsx`
- `app/static/dist/assets/index.js`
- `docs/MILESTONES.md`
- `e2e/tests/web-smoke.spec.mjs`
- `work/4/28/2026-04-28-m62-axis2-correction-summary-dist-e2e.md`

## 사용 skill
- `e2e-smoke-triage`: correction summary compact display의 selector와 격리 Playwright 시나리오를 추가하고 해당 시나리오를 실행했습니다.
- `doc-sync`: M62 Axis 2 진행 사실을 `docs/MILESTONES.md`에 반영했습니다.
- `work-log-closeout`: 변경 파일, 실행 검증, 남은 리스크를 구현 closeout으로 정리했습니다.

## 변경 이유
- M62 Axis 1에서 correction summary frontend 표시가 추가되었고, 이번 slice는 그 표시를 dist에 반영하고 E2E에서 확인 가능한 selector를 고정하는 범위였습니다.
- `PreferencePanel`의 `교정 전체 N개 · 활성 N개` compact line을 smoke test에서 안정적으로 찾을 수 있게 했습니다.

## 핵심 변경
- `PreferencePanel.tsx`의 correction summary compact `<p>`에 `data-testid="correction-summary-compact"`를 추가했습니다.
- `e2e/tests/web-smoke.spec.mjs`에 `correction summary compact display shows total and active count` 격리 시나리오를 추가했습니다.
- 신규 E2E는 preferences, preference audit, correction summary endpoint를 route mock으로 고정하고 compact line의 `교정 전체 5개`, `활성 3개` 표시를 검증합니다.
- `npx vite build`로 `app/static/dist/assets/index.js`를 갱신했습니다.
- `docs/MILESTONES.md`에 M62 Axis 2 항목을 추가했습니다.

## 검증
- 통과: `app/frontend/node_modules/.bin/tsc --noEmit --project app/frontend/tsconfig.json`
- 통과: `git diff --check -- app/frontend/src/components/PreferencePanel.tsx e2e/tests/web-smoke.spec.mjs docs/MILESTONES.md`
- 통과: `npx vite build` (`../static/dist/assets/index.js` 314.12 kB, build 2.12s)
- 통과: `git diff --check -- app/frontend/src/components/PreferencePanel.tsx e2e/tests/web-smoke.spec.mjs docs/MILESTONES.md app/static/dist/index.html app/static/dist/assets/index.js app/static/dist/assets/index.css`
- 통과: `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "correction summary compact display" --reporter=line` (1 passed, 9.7s)

## 남은 리스크
- handoff에 적힌 `npm run build`는 `app/frontend/package.json`에 build script가 없어 npm error를 출력했습니다. repo 문서의 기존 상태처럼 Vite 직접 호출이 필요해 `npx vite build`로 dist를 갱신했습니다.
- 이번 변경은 M62 Axis 2 지정 범위에 한정되어 backend 테스트, 전체 Playwright, 전체 unittest는 실행하지 않았습니다.
- commit, push, branch/PR publish는 수행하지 않았습니다.
