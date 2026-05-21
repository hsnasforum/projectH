# 2026-05-20 controller send-input empty body guard

## 변경 파일
- `tests/test_controller_server.py`
- `work/5/20/2026-05-20-controller-send-input-empty-body-guard.md`

## 사용 skill
- `work-log-closeout`: 구현 라운드 종료 후 변경 파일, 실제 검증, 남은 리스크를 한국어 `/work` 기록으로 남기기 위해 사용했다.

## 변경 이유
- `.pipeline/implement_handoff.md#2066`이 `/api/runtime/send-input` route에서 empty body 및 `Content-Length: 0` 분기가 기존 JSON 400 `lane is required` 응답으로 닫히고 `backend_runtime_send_input`을 호출하지 않는지 socket-free 테스트로 고정하라고 지시했다.
- 서버 parsing은 `content_length > 0`일 때만 body를 읽고 그 외에는 `b"{}"`를 payload로 사용하므로, empty body가 wrapper validation을 거쳐 backend send 없이 닫히는 계약을 직접 고정할 필요가 있었다.

## 핵심 변경
- `test_do_post_send_input_rejects_empty_body_payload`를 추가했다.
- `_json_post_response("/api/runtime/send-input")` 기본 body 경로로 empty body / `Content-Length: 0` 요청을 실행했다.
- 응답이 `HTTPStatus.BAD_REQUEST`와 `{"ok": False, "error": "lane is required"}`인지 확인했다.
- empty body 요청에서는 `backend_runtime_send_input`이 호출되지 않는다는 점을 검증했다.
- production code는 변경하지 않았다. 기존 parser/wrapper validation 경로를 route-level 테스트로 고정한 변경이다.

## 검증
- `python3 -m py_compile tests/test_controller_server.py`
  - 통과.
- `python3 -m unittest -v tests.test_controller_server`
  - 58 tests 통과.
- `git diff --check -- tests/test_controller_server.py work/5/20/`
  - 통과.

## 남은 리스크
- 이번 라운드는 socket-free controller POST empty-body fail-closed route 테스트 추가에 한정했다. Playwright, full controller smoke, broad e2e, long soak, runtime start/stop, `status --json`, `doctor --json`, `tmux` 확인은 handoff 범위 밖이라 실행하지 않았다.
- 같은 controller route family의 앞선 기록에는 local socket guard 환경 제약으로 controller smoke가 보류된 상태가 남아 있다. 이번 라운드는 controller-smoke pass나 release readiness를 주장하지 않는다.
- 작업 트리는 이전 controller/test/work/verify 라운드의 누적 변경을 포함한다. 이번 라운드에서는 handoff 범위인 `tests/test_controller_server.py`와 이 `/work` 기록만 의도적으로 변경했다.
