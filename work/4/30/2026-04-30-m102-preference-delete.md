# 2026-04-30 M102 preference delete

## 변경 파일

- `app/handlers/preferences.py` — `delete_preference(preference_id)` 추가, active 선호 삭제 전 stop-apply 성격의 pause 전환 및 `preference_deleted` task log 기록
- `app/web.py` — `DELETE /api/preferences/<preference_id>` same-origin 라우트 추가
- `storage/preference_store.py` — JSON preference store `delete(preference_id)` 추가
- `storage/sqlite/preference.py` — SQLite preference store `delete(preference_id)` 추가
- `app/frontend/src/api/client.ts` — `deletePreference(preferenceId)` 추가
- `app/frontend/src/components/PreferencePanel.tsx` — preference 카드별 `data-testid="delete-preference-btn"` 삭제 버튼 및 목록 갱신 처리 추가
- `tests/test_web_app.py` — preference delete 성공/404 단위 테스트 2개 추가
- `work/4/30/2026-04-30-m102-preference-delete.md` — 이번 closeout

## 사용 skill

- `security-gate` — 저장된 로컬 선호 레코드 삭제(write-capable/delete) 동작의 same-origin, audit log, 복구 리스크를 확인하기 위해 사용
- `work-log-closeout` — `/work` closeout 필수 섹션, 실제 검증 기록, 남은 리스크 형식을 맞추기 위해 사용

## 변경 이유

- `.pipeline/implement_handoff.md` CONTROL_SEQ 1455가 M102 Axis 1 선호 삭제 기능을 코드 범위로 구현하도록 지시했다.
- 기존 preference handler 위치는 `app/handlers/preferences.py`로 확인됐고, store 계층에는 아직 `delete(preference_id)`가 없어 JSON/SQLite 양쪽 store에 최소 삭제 메서드를 추가했다.

## 핵심 변경

- backend service는 존재하지 않는 선호 삭제 요청에 `WebApiError(404)`를 반환한다.
- active 선호 삭제 시 삭제 직전 `pause_preference()`를 호출해 이후 active preference 주입에서 빠지도록 한 뒤 레코드를 제거한다.
- 삭제는 로컬 `DELETE /api/preferences/<preference_id>` 라우트로 노출하며 기존 same-origin 검증을 통과해야 실행된다.
- frontend는 각 preference 카드에 명시적 `삭제` 버튼을 추가하고, 삭제 성공 후 로컬 목록 상태와 서버 목록을 갱신한다.
- 삭제 실행 시 `task_logger`에 `preference_deleted` action, `previous_status`, `stop_applied`를 남긴다.

## 검증

- `sha256sum .pipeline/implement_handoff.md` — PASS, `52b87cce22c8ef8cf9f151557561dda65f8b9dcac4f1dea57826d6e5bba2d34a`
- `python3 -m py_compile app/handlers/preferences.py app/web.py storage/preference_store.py storage/sqlite/preference.py` — PASS
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_delete_preference_removes_from_store tests.test_web_app.WebAppServiceTest.test_delete_preference_returns_404_for_unknown_id` — PASS, 2 tests
- `npx tsc --noEmit -p app/frontend/tsconfig.json` — FAIL, 루트에서 실행되어 registry `https://registry.npmjs.org/tsc` 조회를 시도했고 network 제한으로 `EAI_AGAIN` 발생
- `app/frontend/node_modules/.bin/tsc --noEmit -p app/frontend/tsconfig.json` — PASS
- `git diff --check -- app/handlers/preferences.py app/web.py storage/preference_store.py storage/sqlite/preference.py app/frontend/src/api/client.ts app/frontend/src/components/PreferencePanel.tsx tests/test_web_app.py` — PASS

## 남은 리스크

- dist 재빌드는 handoff 제약상 실행하지 않았다. 브라우저 반영은 Axis 2 dist rebuild가 별도로 필요하다.
- 광범위 unittest, Playwright E2E, 장시간 soak는 이번 Axis 1 handoff 범위가 아니어서 실행하지 않았다.
- 삭제는 명시 버튼/API로만 실행되지만 별도 확인 dialog는 handoff 지시에 따라 추가하지 않았다. 삭제 후 자동 undo는 없다.
- product docs 동기화는 코드-only handoff 범위 밖이라 수행하지 않았다.
- commit, push, PR publish는 implement role 제약에 따라 수행하지 않았다.
