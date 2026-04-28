# 2026-04-28 M63 Axis 2 Top Pattern dist/E2E

## 변경 파일
- `app/static/dist/assets/index.js`
- `e2e/tests/web-smoke.spec.mjs`
- `docs/MILESTONES.md`
- `work/4/28/2026-04-28-m63-axis2-top-pattern-dist-e2e.md`

## 사용 skill
- `e2e-smoke-triage`: `correction-top-pattern` compact line을 검증하는 Playwright 격리 시나리오를 추가하고 해당 시나리오를 실행했습니다.
- `doc-sync`: M63 Axis 2 진행 사실을 `docs/MILESTONES.md`에 반영했습니다.
- `work-log-closeout`: 변경 파일, 실행 검증, 남은 리스크를 구현 closeout으로 정리했습니다.

## 변경 이유
- M63 Axis 1에서 correction summary top recurring pattern snippet이 backend payload와 frontend compact line에 추가되었습니다.
- 이번 slice는 해당 frontend 변경을 `app/static/dist/`에 반영하고, top pattern original snippet 표시를 E2E smoke 격리 시나리오로 고정하는 범위였습니다.

## 핵심 변경
- `npx vite build`로 `app/static/dist/assets/index.js`를 갱신했습니다.
- `e2e/tests/web-smoke.spec.mjs`에 `correction top pattern compact line shows original snippet` 시나리오를 추가했습니다.
- 신규 E2E는 preferences, preference audit, correction summary endpoint를 route mock으로 고정하고 `correction-top-pattern` line의 `반복 교정: original text one` 표시를 검증합니다.
- `docs/MILESTONES.md`에 M63 Axis 2 항목을 추가했습니다.
- backend와 `app/frontend/src/`는 변경하지 않았습니다.

## 검증
- 통과: `app/frontend/node_modules/.bin/tsc --noEmit --project app/frontend/tsconfig.json`
- 통과: `git diff --check -- e2e/tests/web-smoke.spec.mjs docs/MILESTONES.md`
- 통과: `cd app/frontend && set -o pipefail; npx vite build 2>&1 | tail -5` (`../static/dist/assets/index.js` 314.50 kB, build 1.93s)
- 통과: `git diff --check -- e2e/tests/web-smoke.spec.mjs docs/MILESTONES.md app/static/dist/index.html app/static/dist/assets/index.js app/static/dist/assets/index.css`
- 통과: `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "correction top pattern compact line" --reporter=line` (1 passed, 9.3s)

## 남은 리스크
- 이번 변경은 M63 Axis 2 지정 범위에 한정되어 전체 Playwright, 전체 unittest, backend 테스트는 실행하지 않았습니다.
- `app/static/dist/index.html`과 `app/static/dist/assets/index.css`는 재빌드 후 변경이 없었고, tracked diff는 `app/static/dist/assets/index.js`에만 남았습니다.
- commit, push, branch/PR publish는 수행하지 않았습니다.
