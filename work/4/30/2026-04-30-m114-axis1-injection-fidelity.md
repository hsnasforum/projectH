# 2026-04-30 M114 Axis 1 사용자 활성화 선호 주입 신뢰도 보정

## 변경 파일

- `storage/preference_store.py`
- `storage/sqlite/preference.py`
- `tests/test_preference_store.py`
- `tests/test_sqlite_store.py`
- `work/4/30/2026-04-30-m114-axis1-injection-fidelity.md`

## 사용 skill

- `security-gate`: 선호 저장 레코드의 명시 신뢰도 플래그 변경이 승인/쓰기 경계를 넓히지 않는지 점검.
- `finalize-lite`: 구현 종료 전 검증, doc-sync 범위, `/work` closeout 필요 여부를 점검.
- `work-log-closeout`: closeout 형식과 필수 섹션을 맞추기 위해 사용.

## 변경 이유

- 사용자가 리뷰 큐에서 명시적으로 활성화한 ACTIVE 선호가 최초 런타임 신뢰도 통계 없이도 즉시 세션 주입 대상이 되도록 하기 위함.
- `AgentLoop._get_active_preferences()`가 `is_highly_reliable_preference()`를 기준으로 필터링하므로, 수동 활성화 경로에서 저장 레코드에 `is_highly_reliable == True`를 명시해야 한다.

## 핵심 변경

- `PreferenceStore.activate_preference()`가 `_transition()` 결과가 없으면 기존처럼 `None`을 반환하고, 결과가 있으면 `is_highly_reliable`를 `True`로 저장 및 반환한다.
- `SQLitePreferenceStore.activate_preference()`가 대상 row의 data blob에 `is_highly_reliable`, `status`, `activated_at`, `updated_at`을 반영해 저장하고 갱신 레코드를 반환한다.
- 파일 기반 선호 저장소의 `test_activate_preference`에 `is_highly_reliable == True` assertion을 추가했다.
- SQLite 선호 저장소의 수동 활성화 테스트에 같은 assertion을 추가했다.
- `_auto_activate_candidate_if_ready()`, `_get_active_preferences()`, `is_highly_reliable_preference()`는 수정하지 않았다.
- 진입 시점에 대상 네 파일의 diff가 이미 핸드오프 내용과 일치해 추가 코드 수정 없이 검증과 closeout을 수행했다.

## 검증

- `python3 -m py_compile storage/preference_store.py storage/sqlite/preference.py`
  - 통과.
- `python3 -m unittest -v tests.test_preference_store tests.test_sqlite_store`
  - 통과. 81개 테스트 실행.
- `git diff --check -- storage/preference_store.py storage/sqlite/preference.py tests/test_preference_store.py tests/test_sqlite_store.py`
  - 통과.

## 남은 리스크

- docs 변경은 핸드오프에서 금지된 Axis 2 범위라 수행하지 않았다.
- broader browser/E2E는 브라우저 계약 변경이 아니고 핸드오프 검증 범위 밖이라 실행하지 않았다.
