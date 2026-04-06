# explicit same-session mutation rerender hardening outside aggregate

날짜: 2026-04-06

## 변경 파일

- `app/static/app.js` (rerenderAfterMutation helper 추가 + 12개 mutation handler 경로 통합)

## 사용 skill

- 없음

## 변경 이유

- 이전 라운드에서 aggregate action handler 6개에만 `renderSession(data.session, { force: true })`를 적용했으나, `submitFeedback`, `submitCorrection`, `submitCandidateConfirmation`, `submitCandidateReviewAccept`, `submitContentVerdict`, `submitContentReasonNote` 6개는 여전히 raw `renderSession(data.session)`를 사용하고 있었습니다.
- `fetchJson()` 경로는 global busy/progress를 올리지 않으므로, 동일 세션에서 더 최신 `updated_at`이 먼저 렌더되면 stale-guard skip이 feedback/correction/review/content-verdict UI에서도 발생할 수 있는 same-family current-risk가 있었습니다.
- aggregate 전용 예외를 늘리는 대신, shared rerender path를 하나 도입하여 12개 explicit mutation handler를 모두 통합했습니다.

## 핵심 변경

1. `rerenderAfterMutation(session)` helper 함수 추가 (line 1872)
   - `renderSession(session, { force: true })`를 호출하여 stale guard를 우회
   - explicit user mutation 응답 전용 single entry point

2. 6개 submit handler의 `renderSession(data.session)` → `rerenderAfterMutation(data.session)` 변경
   - submitFeedback, submitCorrection, submitCandidateConfirmation, submitCandidateReviewAccept, submitContentVerdict, submitContentReasonNote

3. 6개 aggregate handler의 `renderSession(data.session, { force: true })` → `rerenderAfterMutation(data.session)` 변경
   - conflict-check, reverse, stop, result, apply, emit(start)
   - 기존 동작 동일, 중복 제거

4. read-path caller (`loadSession`, `renderResult`)는 기존 `renderSession(data.session)` 유지 — stale guard semantics 보존

## 검증

- `git diff --check -- app/static/app.js`: clean
- `python3 -m unittest -v tests.test_web_app`: 187 passed (59.2s)
- `make e2e-test`: 17 passed (2.8m), 0 failed
- scenario 12 (same-session recurrence aggregate) 포함 전체 통과

## 남은 리스크

- `rerenderAfterMutation`는 explicit mutation 응답에서만 사용. polling이나 일반 session load의 stale guard는 그대로 유지됨.
- 향후 새 mutation handler 추가 시 `rerenderAfterMutation`를 사용해야 한다는 점을 인지해야 함.
