# 2026-04-30 M103 preference reliability toggle

## 변경 파일

- `app/handlers/preferences.py` - `toggle_preference_reliability(preference_id)` handler 추가
- `app/web.py` - `POST /api/preferences/<preference_id>/toggle-reliability` same-origin route 추가
- `storage/preference_store.py` - JSON preference store 최소 `update()` 추가
- `storage/sqlite/preference.py` - SQLite preference store 최소 `update()` 추가
- `storage/preference_utils.py` - 저장된 명시적 `is_highly_reliable` 값을 reliability projection에서 존중
- `app/frontend/src/api/client.ts` - `togglePreferenceReliability()` client 추가
- `app/frontend/src/components/PreferencePanel.tsx` - `data-testid="toggle-reliability-btn"` UI와 상태 갱신 연결
- `tests/test_web_app.py` - toggle 성공/404 테스트 2개 추가
- `work/4/30/2026-04-30-m103-preference-reliability-toggle.md` - 이번 closeout

## 사용 skill

- `finalize-lite` - 구현 종료 전 실행 사실, 미실행 범위, 문서 동기화 필요 여부를 점검하기 위해 사용
- `work-log-closeout` - `/work` closeout 필수 섹션과 실제 검증/잔여 리스크 기록 형식을 맞추기 위해 사용

## 변경 이유

- `.pipeline/implement_handoff.md` CONTROL_SEQ 1460이 M103 Axis 1 preference reliability toggle 구현을 지시했다.
- M94에서 `is_highly_reliable` 표시가 이미 추가됐고, M102에서 preference delete가 완료된 상태에서 명시적 신뢰도 토글을 추가하는 범위다.

## 핵심 변경

- backend handler가 현재 enriched `is_highly_reliable` 값을 기준으로 신뢰도 값을 반전하고 `preference_reliability_toggled` task log를 남긴다.
- JSON/SQLite preference store에 기존 record를 보존하면서 일부 field를 갱신하는 최소 `update()`를 추가했다.
- `enrich_preference_reliability()`와 `is_highly_reliable_preference()`가 저장된 boolean `is_highly_reliable` 값을 우선 존중해 토글 상태가 reload 후에도 유지되게 했다.
- React client와 `PreferencePanel`에 `togglePreferenceReliability()` 호출 및 `toggle-reliability-btn` 버튼을 추가했다.
- 신규 unittest는 JSON과 SQLite 백엔드 모두에서 true→false→true flip을 확인하고, unknown id 404를 확인한다.
- handoff 제약에 따라 dist 재빌드는 수행하지 않았다.

## 검증

- `sha256sum .pipeline/implement_handoff.md` - PASS, `c3b7bae3eb074c140e3e7daf1e1d92e9c1d9b3b0c224bd3c37d02384fd1443ee`
- `python3 -m py_compile app/handlers/preferences.py app/web.py storage/preference_store.py storage/sqlite/preference.py storage/preference_utils.py` - PASS
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_toggle_preference_reliability_flips_flag tests.test_web_app.WebAppServiceTest.test_toggle_preference_reliability_returns_404_for_unknown_id` - PASS, 2 tests
- `app/frontend/node_modules/.bin/tsc --noEmit -p app/frontend/tsconfig.json` - PASS
- `python3 -m unittest -v tests.test_preference_handler tests.test_correction_summary` - PASS, 29 tests
- `git diff --check -- app/handlers/preferences.py app/web.py storage/preference_store.py storage/sqlite/preference.py storage/preference_utils.py app/frontend/src/api/client.ts app/frontend/src/components/PreferencePanel.tsx tests/test_web_app.py` - PASS
- `rg -n "toggle_preference_reliability|toggle-reliability|togglePreferenceReliability|toggle-reliability-btn|def update\\(" app/handlers/preferences.py app/web.py storage/preference_store.py storage/sqlite/preference.py app/frontend/src/api/client.ts app/frontend/src/components/PreferencePanel.tsx tests/test_web_app.py` - PASS

## 남은 리스크

- dist rebuild는 handoff가 제외했으므로 `app/static/dist/assets/`에는 M103 toggle UI가 아직 반영되지 않았다.
- product docs는 이번 Axis 1 code-only handoff 범위 밖이라 갱신하지 않았다. `is_highly_reliable`가 계산값뿐 아니라 명시 저장값도 존중하게 된 점은 후속 doc-sync가 필요하다.
- browser/E2E는 이번 handoff 검증 목록에 없고 dist rebuild도 제외되어 실행하지 않았다.
- commit, push, branch/PR publish는 implement role 제약에 따라 수행하지 않았다.
