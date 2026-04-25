STATUS: verified
CONTROL_SEQ: 173
BASED_ON_WORK: work/4/25/2026-04-25-m34-reviewed-memory-loop-visibility.md
VERIFIED_BY: Claude
NEXT_CONTROL: .pipeline/advisory_request.md CONTROL_SEQ 173 (M34 Axis 2 direction)

---

## M34 Axis 1: reviewed-memory loop 가시성 (applied_preferences badge)

### Verdict

PASS (환경 재설정 후). 구버전 서버로 실행한 첫 시도는 실패했으나 — M34 코드로 서버 재기동 후 reviewed-memory loop 시나리오 **1 passed (5.7s)** 확인.

### Root Cause of Initial Failure

E2E 서버(PID 82567)가 M34 변경 전 코드(M31 시점 기동)로 실행 중이었음. 신규 `_serialize_session` 복원 로직이 적용되지 않아 `session.messages`에 `applied_preferences` 미포함 → badge 미표시. 서버 재기동 후 정상.

### Checks Run

- `python3 -m py_compile app/serializers.py` → compile OK
- `python3 -m unittest tests/test_preference_handler.py -v 2>&1 | tail -5` → `Ran 13 tests` `OK`
- `cd app/frontend && npx vite build` → `✓ built in 1.81s`
- `node --check e2e/tests/web-smoke.spec.mjs` → OK
- `git diff --check -- app/serializers.py app/frontend/src/components/MessageBubble.tsx e2e/tests/web-smoke.spec.mjs` → exit 0
- (구버전 서버) `npx playwright test -g "reviewed-memory loop"` → **FAIL** (badge not found)
- **서버 재기동 (M34 코드):** `npx playwright test -g "reviewed-memory loop"` → **1 passed (5.7s)**

### Implementation Review

- `app/serializers.py:85,222–266` — `preference_by_fingerprint` None 초기화 + `applied_preference_ids` → `applied_preferences` 복원 로직 (lazy load, 세션당 1회 preference store 조회)
- `app/frontend/src/components/MessageBubble.tsx:403` — `data-testid="applied-preferences-badge"` 추가
- `e2e/tests/web-smoke.spec.mjs:12068` — `page.getByTestId("applied-preferences-badge").first()).toBeVisible()` 추가
- `app/static/dist/assets/index.js` — 프론트엔드 bundle 재빌드

### Why Badge Works After Fix

1. Chat response → `update_last_message(session_id, {"applied_preference_ids": [fp, ...]})` 저장
2. `get_session(session_id)` → 마지막 메시지에 `applied_preference_ids` 포함
3. `_serialize_session` 복원 로직 → `preference_store.list_all()` 에서 fp 매핑 → `applied_preferences` 설정
4. Frontend `session.messages[last].applied_preferences` → badge 렌더링

### Next

M34 Axis 1 완료. Axis 2 방향 — advisory 판단 필요.
