# 2026-04-30 M109 preference list pagination

## 변경 파일

- `storage/preference_store.py`
- `storage/sqlite/preference.py`
- `app/handlers/preferences.py`
- `app/web.py`
- `app/frontend/src/api/client.ts`
- `app/frontend/src/components/PreferencePanel.tsx`
- `tests/test_web_app.py`
- `work/4/30/2026-04-30-m109-preference-pagination.md`

## 사용 skill

- `e2e-smoke-triage`: `preference-show-more-btn` UI selector 추가와 브라우저 흐름 리스크 확인
- `finalize-lite`: 구현 후 실행 검증, 미실행 검증, doc-sync 범위 확인
- `work-log-closeout`: 변경 파일, 실행 명령, 잔여 리스크를 `/work` 형식으로 기록

## 변경 이유

- `.pipeline/implement_handoff.md` CONTROL_SEQ 1485의 `m109_axis1_preference_list_pagination` 실행.
- M107 correction history offset pagination과 대칭으로 preference 목록도 `limit`/`offset` 기반 batch 조회와 “더 보기” UI를 지원해야 했다.

## 핵심 변경

- JSON `PreferenceStore.list_all()`과 SQLite `SQLitePreferenceStore.list_all()`에 `limit`, `offset` 파라미터를 추가했다.
- `list_preferences_payload(limit=20, offset=0)`가 페이지 목록은 offset batch로 반환하되, header/count 집계는 visible 전체 preference 기준으로 유지하도록 분리했다.
- `GET /api/preferences?limit=N&offset=N`에서 쿼리 파라미터를 파싱해 handler로 전달하도록 했다.
- `fetchPreferences({ limit, offset })` API를 추가하고, `PreferencePanel`이 초기 20개 로드 후 `preference-show-more-btn`으로 다음 batch를 append하도록 했다.
- `preferenceListHasMore` 상태와 loaded-count offset을 추가해, M108 `preference-search-input` 필터가 로드된 preference 목록 위에서 계속 동작하게 했다.
- `test_preference_list_respects_limit_and_offset`를 추가해 `offset=2`가 전체 정렬 결과의 세 번째 preference를 반환하는지 확인했다.

## 검증

- `python3 -m py_compile app/handlers/preferences.py app/web.py storage/preference_store.py storage/sqlite/preference.py` 통과.
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_preference_list_respects_limit_and_offset` 통과.
- `app/frontend/node_modules/.bin/tsc --noEmit -p app/frontend/tsconfig.json` 통과.
- `git diff --check -- storage/preference_store.py storage/sqlite/preference.py app/handlers/preferences.py app/web.py app/frontend/src/api/client.ts app/frontend/src/components/PreferencePanel.tsx tests/test_web_app.py` 통과.
- `grep -n "preference-show-more-btn\|preferenceListHasMore" app/frontend/src/components/PreferencePanel.tsx` 확인: `159`, `1253`, `1256`.
- `python3 -m unittest -v tests.test_preference_handler` 통과.

## 남은 리스크

- handoff가 Axis 1 code-only 범위라 `app/static/dist` 재빌드는 실행하지 않았다.
- Playwright는 실행하지 않았다. 새 `preference-show-more-btn` 브라우저 흐름은 후속 dist/E2E 라운드 또는 CI에서 확인해야 한다.
- UI/API 동작 변경에 따른 문서 동기화는 이번 handoff 범위 밖이며 후속 번들에서 처리되어야 한다.
- commit, push, branch/PR publish, next-slice 선택은 수행하지 않았다.
