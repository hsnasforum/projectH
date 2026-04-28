# 2026-04-28 M50 Axis 3 명시적 선호도 교정 엔드포인트 backend

## 변경 파일

- `storage/session_store.py`
- `app/handlers/preferences.py`
- `app/web.py`
- `tests/test_session_store.py`
- `docs/MILESTONES.md`
- `work/4/28/2026-04-28-m50-axis3-explicit-preference-correction-backend.md`

## 사용 skill

- `security-gate`: 신규 POST endpoint와 session message event 기록이 local-first 저장 경계를 넘지 않는지 확인.
- `doc-sync`: 구현 사실을 `docs/MILESTONES.md`의 M50 Axis 3 항목에 제한적으로 반영.
- `work-log-closeout`: 구현 종료 기록을 표준 `/work` 형식으로 작성.

## 변경 이유

- M50 Axis 2까지는 `corrected_text`가 저장된 응답만 `corrected_count`에 반영됐다.
- 사용자가 교정 텍스트 없이 “이 선호는 반영되지 않았다”를 명시적으로 남길 수 있는 backend 기록 경로가 필요했다.

## 핵심 변경

- `SessionStore.record_preference_explicit_correction()`을 추가해 assistant 메시지의 `applied_preference_ids`에 포함된 fingerprint만 `preference_correction_events`로 기록한다.
- `get_global_audit_summary()`가 `preference_correction_events[].fingerprint`를 읽어 해당 preference의 `corrected_count`에 추가 산입하도록 했다.
- `PreferenceHandlerMixin.record_explicit_preference_correction()`과 `POST /api/preferences/record-correction` route를 추가했다.
- `tests/test_session_store.py`에 명시적 correction event가 `corrected_count`를 올리는 케이스와 적용되지 않은 fingerprint 거부 케이스를 추가했다.
- security boundary: same-origin POST route 안에서 session-local message event만 기록한다. approval flow, preference lifecycle store, overwrite/delete, frontend/dist는 변경하지 않았다.

## 검증

- `python3 -m py_compile storage/session_store.py app/handlers/preferences.py app/web.py tests/test_session_store.py`
  - 통과.
- `python3 -m unittest -v tests.test_session_store`
  - 통과. `Ran 20 tests ... OK`.
- `git diff --check -- storage/session_store.py app/handlers/preferences.py app/web.py tests/test_session_store.py docs/MILESTONES.md`
  - 통과.

## 남은 리스크

- backend-only handoff라 frontend button, API client, dist rebuild, Playwright는 실행하지 않았다. 다음 Axis 3b에서 UI 연결과 브라우저 검증이 필요하다.
- 신규 endpoint는 현재 `{ok: false}`로 실패를 표현한다. 프론트엔드 연결 시 사용자 표시 문구와 retry 동작을 별도 UX 계약으로 고정해야 한다.
