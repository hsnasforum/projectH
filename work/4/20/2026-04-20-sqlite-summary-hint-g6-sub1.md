# 2026-04-20 sqlite summary hint G6-sub1

## 변경 파일
- storage/sqlite_store.py
- tests/test_web_app.py

## 사용 skill
- work-log-closeout: `work/4/20/` 아래 표준 섹션 순서로 이번 bounded slice의 변경, 실제 검증, 남은 리스크를 closeout으로 남겼습니다.

## 변경 이유
- `SQLiteSessionStore`는 `SessionStore.record_correction_for_message`를 이미 adoption하고 있었지만, 그 경로가 내부에서 호출하는 `_compact_summary_hint_for_persist`를 adopt하지 않아 SQLite-backed `tests.test_web_app` 27건이 `AttributeError`로 깨지고 있었습니다.
- 같은 family 안에서 `tests/test_web_app.py:14994`는 seq 441 이후 실제 shipped wording이 `"한 가지 출처의 정보로만 확인됩니다"`로 바뀌었는데도 `"단일 출처 상태"`를 계속 기대하고 있어 truth-sync 1줄이 더 필요했습니다.

## 핵심 변경
- `storage/sqlite_store.py:343`에 `SQLiteSessionStore` adoption line을 추가해 `_compact_summary_hint_for_persist`를 `SessionStore`에서 재사용하도록 맞췄습니다. 실제 동작 parity를 위해 `staticmethod(_SS._compact_summary_hint_for_persist)` 형태로 넣었고, `# Public session-data methods` divider는 바로 다음 줄 `:344`에 그대로 유지했습니다.
- `tests/test_web_app.py:14994`는 이제 `self.assertIn("한 가지 출처의 정보로만 확인됩니다", summary)`를 검사합니다. 기존 `"재조사했지만"`, `"이용 형태"`, `"아직"`, `assertNotIn("보강")`, `assertNotIn("미확인에서")` 주변 assertion은 그대로 두고 stale wording 1줄만 truth-sync했습니다.
- 결과적으로 `SQLiteSessionStore` correction 경로의 27개 SQLite-backed red cell은 더 이상 `_compact_summary_hint_for_persist` missing/binding 문제로 깨지지 않습니다. direct sanity로 `tests.test_web_app.WebAppServiceTest.test_submit_candidate_review_accept_persists_local_preference_candidate_with_sqlite_backend`를 따로 재실행했고 green이었습니다.
- step 6 grep 결과상 `한 가지 출처의 정보로만 확인됩니다`는 `tests/test_web_app.py`에서 2건(`8595`, `14994`)이 되었고, `_compact_summary_hint_for_persist`는 `storage/session_store.py:790`, `:830`, `:1027` plus `storage/sqlite_store.py:343` 총 4건이 맞았습니다.
- seq 408/411/414/417/420/423/427/430/438/441/444/447/450/453/456 shipped surface는 의도적으로 수정하지 않았습니다. `storage/session_store.py`, `core/*`, `app/*`, `tests/test_smoke.py`, client/serializer/Playwright, `status_label` literal set과 legend는 모두 미편집입니다. G3 / G5 / G7 / G8 / G9 / G10도 계속 deferred 상태입니다.

## 검증
- `rg -n "_compact_summary_hint_for_persist" storage/ tests/`
  - 결과: 4건 hit
  - `storage/session_store.py:790`
  - `storage/session_store.py:830`
  - `storage/session_store.py:1027`
  - `storage/sqlite_store.py:343`
- `rg -n '단일 출처 상태' tests/test_web_app.py`
  - 결과: 14건 hit
  - residual line: `15009`, `15068`, `15080`, `15102`, `15187`, `15270`, `15370`, `15567`, `15771`, `17981`, `18139`, `18158`, `18296`, `18301`
  - handoff의 expected zero와 달리 legacy fixture/assert text가 다른 구간에 남아 있었지만, 이번 slice에서는 `14994` 한 줄만 truth-sync했습니다.
- `rg -n '한 가지 출처의 정보로만 확인됩니다' tests/test_web_app.py`
  - 결과: 2건 hit
  - `8595`
  - `14994`
- `rg -n '_SS\.' storage/sqlite_store.py`
  - 결과: 29건 hit
  - 기존 adoption/import pattern에 새 line `343`이 1건 추가된 상태였습니다.
- `python3 -m unittest tests.test_web_app.WebAppServiceTest.test_submit_candidate_review_accept_persists_local_preference_candidate_with_sqlite_backend`
  - 결과: `Ran 1 test in 0.119s`, `OK`
  - 처음 plain adoption으로 보였던 `TypeError`가 staticmethod parity 수정 후 사라졌는지 direct sanity로 확인했습니다.
- `python3 -m unittest tests.test_web_app`
  - 결과: `Ran 313 tests in 158.590s`, `FAILED (errors=10)`
  - verify handoff baseline은 `failures=1, errors=27`이었고, 이번 구현 후 그 28건은 해소됐습니다.
  - 최종 잔여 10건은 모두 `LocalOnlyHTTPServer(("127.0.0.1", 0), service)` bind에서 발생한 `PermissionError: [Errno 1] Operation not permitted`였습니다.
  - residual test names:
    - `test_handler_dispatches_aggregate_transition_conflict_check_returns_ok`
    - `test_handler_dispatches_aggregate_transition_conflict_check_to_service`
    - `test_handler_dispatches_aggregate_transition_reverse_returns_ok`
    - `test_handler_dispatches_aggregate_transition_reverse_to_service`
    - `test_handler_dispatches_aggregate_transition_stop_returns_ok`
    - `test_handler_dispatches_aggregate_transition_stop_to_service`
    - `test_handler_returns_400_for_empty_request_body`
    - `test_handler_returns_400_for_malformed_json_syntax_request_body`
    - `test_handler_returns_400_for_malformed_utf8_request_body`
    - `test_handler_returns_400_for_non_object_json_request_body`
- `python3 -m unittest tests.test_smoke -k progress_summary`
  - 결과: `Ran 11 tests in 0.030s`, `OK`
  - seq 453 baseline 유지
- `python3 -m unittest tests.test_smoke -k coverage`
  - 결과: `Ran 27 tests in 0.078s`, `OK`
  - seq 453 baseline 유지
- `python3 -m unittest tests.test_smoke -k claims`
  - 결과: `Ran 7 tests in 0.001s`, `OK`
  - seq 453 baseline 유지
- `python3 -m unittest tests.test_smoke -k reinvestigation`
  - 결과: `Ran 6 tests in 0.074s`, `OK`
  - seq 453 baseline 유지
- `python3 -m py_compile storage/sqlite_store.py tests/test_web_app.py`
  - 결과: 출력 없음, 통과
- `git diff --check -- storage/sqlite_store.py tests/test_web_app.py`
  - 결과: 출력 없음, 통과
- `node --check`, Playwright, `make e2e-test`, `tests.test_pipeline_gui_backend`는 이번 라운드가 storage + test wording slice이고 client/browser/runtime-status family를 건드리지 않아 실행하지 않았습니다.

## 남은 리스크
- `SQLiteSessionStore` adoption list는 여전히 수동 유지입니다. 앞으로 `SessionStore` private helper가 더 추가되면 같은 drift가 다시 생길 수 있어, property-style parity check나 shared adoption helper 같은 meta-slice를 검토할 수 있습니다.
- `tests.test_web_app`는 post-edit에도 `errors=10`이 남았습니다. 모두 `LocalOnlyHTTPServer` bind 시 `PermissionError: [Errno 1] Operation not permitted`로, 이번 slice의 storage parity / wording drift와는 별개의 handler/socket 환경 이슈로 보입니다.
- unrelated `tests.test_pipeline_gui_backend::TestRuntimeStatusRead` dirty-state family는 그대로 열려 있습니다. G5 candidate입니다.
- G3 threshold tuning, G7 vocabulary enforcement, G8 memory foundation, G9 naming-collision cleanup, G10 COMMUNITY explicit key는 모두 future arbitration 대상으로 남아 있습니다.
- 오늘(2026-04-20) docs-only round count는 계속 0입니다. 이번 라운드는 storage + test slice였고 docs는 건드리지 않았습니다.
- dirty worktree의 다른 파일들은 이번 라운드에서 건드리지 않았습니다.
