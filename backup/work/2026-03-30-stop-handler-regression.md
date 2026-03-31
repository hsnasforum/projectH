# 2026-03-30 aggregate-transition-stop HTTP handler-level regression

## 변경 파일
- `tests/test_web_app.py`

## 사용 skill
- 없음

## 변경 이유
- `.pipeline/codex_feedback.md`와 `verify/3/30/2026-03-30-reverse-handler-regression-verification.md`에서 `/api/aggregate-transition-stop`의 HTTP handler dispatch를 직접 고정하는 handler-level regression이 없다고 지적되었습니다.
- behavior widening 없이 handler dispatch 연결만 고정하는 focused regression 2개를 추가했습니다.

## 핵심 변경
- `test_handler_dispatches_aggregate_transition_stop_to_service`:
  - 실제 `LocalOnlyHTTPServer`를 `127.0.0.1:0`에 바인드하고 `http.client`로 POST 요청 전송
  - transition record가 없는 세션에 요청 시 handler가 service의 `stop_apply_aggregate_transition`으로 dispatch하고 404 에러 응답을 올바르게 반환하는지 확인
  - `resp.status == 404`, `ok == False`, `error` 키 존재 검증

- `test_handler_dispatches_aggregate_transition_stop_returns_ok`:
  - service-level로 전체 흐름(emit → apply → confirm result) 실행 후 applied_with_result 상태 준비
  - 실제 `LocalOnlyHTTPServer`를 바인드하고 HTTP POST로 `/api/aggregate-transition-stop` 호출
  - handler가 service를 통해 성공 응답을 반환하는지 확인:
    - `resp.status == 200`
    - `ok == true`
    - `canonical_transition_id` 존재
    - `transition_record.record_stage == stopped`

## 검증
- `python3 -m py_compile app/web.py tests/test_web_app.py` — 통과
- `python3 -m unittest -v tests.test_web_app` — 97 tests OK (기존 95 + 신규 2)
- `git diff --check` — 통과

## 남은 리스크
- app code는 변경하지 않았습니다. 테스트만 추가했으므로 doc churn 없습니다.
- e2e는 건드리지 않았습니다.
- `emit/apply` route의 handler-level regression은 아직 없습니다.
- dirty worktree가 여전히 넓으므로 다음 라운드도 unrelated 변경을 건드리지 않아야 합니다.
