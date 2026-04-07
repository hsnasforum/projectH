# same-session aggregate stop-apply rerender stabilization

날짜: 2026-04-06

## 변경 파일

- `app/static/app.js` (renderSession stale guard + aggregate action force render)

## 사용 skill

- 없음

## 변경 이유

- `make e2e-test` full suite에서 scenario 12 (`same-session recurrence aggregate`)가 `aggregate-trigger-stopped` missing으로 실패.
- stop API 응답의 session `updated_at`이 full suite order에서 동시에 실행된 다른 action의 더 최신 `updated_at`보다 이전이 되어, `renderSession`의 stale guard(`incomingUpdatedAt < state._lastRenderedSessionUpdatedAt`)에 걸려 aggregate card re-render가 건너뛰어짐.
- 결과: notice는 갱신됐지만 aggregate card가 `effect_active` helper + `적용 중단` 버튼 상태에 남아 있어 `aggregate-trigger-stopped` testid가 DOM에 나타나지 않음.

## 핵심 변경

1. `renderSession(session)` → `renderSession(session, opts)` 시그니처 확장
   - `opts.force === true`이면 stale guard를 건너뛰고 항상 re-render
   - 기존 호출은 `opts` 없이 호출하므로 기존 동작 유지

2. aggregate trigger 영역의 6개 action handler (emit, start-apply, apply-result, stop, reverse, conflict-check)에서 `renderSession(data.session, { force: true })` 사용
   - 이 action들은 사용자가 명시적으로 버튼을 눌러 실행한 것이므로, stale guard를 건너뛰고 항상 최신 session 상태를 반영해야 함

## 검증

- `git diff --check -- app/static/app.js`: clean
- `python3 -m unittest -v tests.test_web_app`: 187 passed
- `make e2e-test`: **17 passed (2.9m)**, 0 failed — 이전 실패했던 scenario 12 포함
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs:753`: 1 passed (42.1s)

## 남은 리스크

- `force: true`는 aggregate action 응답에서만 사용. polling이나 일반 session load에서는 기존 stale guard가 그대로 유지됨.
- 다른 비-aggregate action (feedback, correction, approval 등)에서도 같은 stale guard 문제가 이론적으로 가능하지만, 현재 e2e에서 재현되지 않음.
