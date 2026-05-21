# 2026-05-20 controller send-input non-object JSON guard

## 변경 파일
- `tests/test_controller_server.py`
- `work/5/20/2026-05-20-controller-send-input-non-object-json-guard.md`

## 사용 skill
- `work-log-closeout`: 구현 라운드 종료 후 변경 파일, 실제 검증, 남은 리스크를 한국어 `/work` 기록으로 남기기 위해 사용했다.

## 변경 이유
- `.pipeline/implement_handoff.md#2061`가 `/api/runtime/send-input` POST에서 syntactically valid but non-object JSON payload를 기존 invalid JSON 계약과 같은 JSON 400으로 거부하는 동작을 socket-free test로 고정하라고 지시했다.
- 생산 코드에는 `if not isinstance(payload, dict)` branch가 있었지만, `ControllerAssetResolutionTests`에서 해당 branch가 직접 검증되지 않았다.

## 핵심 변경
- `test_do_post_send_input_rejects_non_object_json_payload`를 추가해 JSON array payload가 `HTTPStatus.BAD_REQUEST`와 `{"ok": False, "error": "invalid json"}`를 반환하는지 확인했다.
- 새 테스트는 기존 `_json_post_response`와 `_assert_json_response` helper path를 사용해 JSON headers, `Content-Length`, CORS header, body bytes, end-header count를 함께 검증한다.
- `runtime_send_input`이 non-object JSON payload에서는 호출되지 않는지 `assert_not_called()`로 고정했다.
- 기존 valid dict JSON, malformed JSON body, invalid `Content-Length`, unknown POST, route, asset, header, body, dispatch assertions는 유지했다.
- 생산 코드(`controller/server.py`)는 이번 라운드에서 수정하지 않았다.

## 검증
- `python3 -m py_compile tests/test_controller_server.py`
  - 통과.
- `python3 -m unittest -v tests.test_controller_server`
  - 52 tests 통과.
- `git diff --check -- tests/test_controller_server.py work/5/20/`
  - 통과.

## 남은 리스크
- 이번 라운드는 socket-free controller POST payload-shape test guard만 수행했다. Playwright, full controller smoke, broad e2e, long soak, runtime start/stop, `status --json`, `doctor --json`, `tmux` 확인은 handoff 범위 밖이라 실행하지 않았다.
- 같은 controller Queue/controller route family의 앞선 기록에는 focused Playwright가 local socket 권한 문제로 보류된 상태가 남아 있다. 이번 라운드는 controller-smoke pass나 release readiness를 주장하지 않는다.
- worktree에는 이전 라운드부터 이어진 많은 수정/미추적 파일이 남아 있으며, 이번 라운드에서는 `tests/test_controller_server.py`와 이 `/work` 기록 외에는 의도적으로 건드리지 않았다.
