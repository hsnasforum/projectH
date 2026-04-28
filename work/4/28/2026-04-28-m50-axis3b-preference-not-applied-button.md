# 2026-04-28 M50 Axis 3b preference-not-applied button 구현

## 변경 파일

- `app/frontend/src/api/client.ts`
- `app/frontend/src/components/MessageBubble.tsx`
- `app/frontend/src/components/ChatArea.tsx`
- `app/frontend/src/App.tsx`
- `app/static/dist/assets/index.js`
- `app/static/dist/assets/index.css`
- `e2e/tests/web-smoke.spec.mjs`
- `work/4/28/2026-04-28-m50-axis3b-preference-not-applied-button.md`

## 사용 skill

- `security-gate`: 로컬 세션 기준 교정 기록 엔드포인트 호출이 추가되어 write-capable 경계를 확인했습니다.
- `e2e-smoke-triage`: 새 브라우저 계약을 단일 Playwright smoke 시나리오로 고정했습니다.
- `work-log-closeout`: 구현 종료 기록을 남겼습니다.

## 변경 이유

M50 Axis 3 백엔드에서 `/api/preferences/record-correction` 경로가 준비된 상태였지만, 사용자가 응답에 적용된 선호가 실제로 반영되지 않았음을 프론트엔드에서 명시적으로 기록할 방법이 없었습니다. 이번 slice는 적용 선호 popover 안에 `반영 안 됨` 버튼을 추가하고, 해당 클릭이 현재 세션, 응답 메시지, preference fingerprint를 그대로 백엔드에 전달하는 데만 한정했습니다.

## 핵심 변경

- `postPreferenceExplicitCorrection()` API 클라이언트를 추가해 `session_id`, `message_id`, `fingerprint`를 `/api/preferences/record-correction`으로 전송하게 했습니다.
- `App.tsx`에 선호 교정 핸들러를 추가하고 실패 시 기존 toast 경로로 오류를 노출하게 했습니다.
- `ChatArea`와 `MessageBubble`에 `onPrefCorrection` prop을 연결했습니다.
- 적용 선호 popover의 각 선호 항목에 `data-testid="preference-not-applied-btn"` 버튼을 추가했습니다.
- Vite build 산출물 `app/static/dist/assets/index.js`, `app/static/dist/assets/index.css`를 갱신했습니다.
- Playwright smoke에 버튼 클릭 시 `/api/preferences/record-correction` 요청 본문이 기대한 `session_id`, `message_id`, `fingerprint`를 포함하는지 검증하는 시나리오를 추가했습니다.

## 검증

- `app/frontend/node_modules/.bin/tsc --noEmit --project app/frontend/tsconfig.json`
  - 통과
- `cd app/frontend && node_modules/.bin/vite build`
  - 통과
  - `../static/dist/index.html 0.35 kB`
  - `../static/dist/assets/index.css 32.91 kB`
  - `../static/dist/assets/index.js 312.86 kB`
- `grep -c "preference-not-applied-btn" app/static/dist/assets/index.js`
  - `1`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "reviewed-memory loop: preference-not-applied-btn 클릭 시 record-correction이 호출됩니다" --reporter=line`
  - 통과, `1 passed (9.2s)`
  - `FORCE_COLOR`로 인해 `NO_COLOR`가 무시된다는 경고만 있었고 실패는 없었습니다.
- `git diff --check -- app/frontend/src/api/client.ts app/frontend/src/components/MessageBubble.tsx app/frontend/src/components/ChatArea.tsx app/frontend/src/App.tsx app/static/dist/assets/index.js app/static/dist/assets/index.css e2e/tests/web-smoke.spec.mjs`
  - 통과

## 남은 리스크

- 버튼 클릭 성공 toast나 즉시 통계 refresh는 이번 handoff 범위에 포함하지 않았습니다.
- 전체 Playwright smoke나 전체 unittest는 실행하지 않았습니다. 이번 변경은 단일 프론트엔드 경로와 해당 신규 E2E 계약에 한정되어 isolated scenario로 검증했습니다.
- `docs/MILESTONES.md`와 백엔드/storage 파일은 handoff 경계에 따라 수정하지 않았습니다.
