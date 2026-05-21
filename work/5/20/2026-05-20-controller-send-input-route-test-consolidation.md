# 2026-05-20 controller send-input route test consolidation

## 변경 파일
- `tests/test_controller_server.py`
- `work/5/20/2026-05-20-controller-send-input-route-test-consolidation.md`

## 사용 skill
- `work-log-closeout`: 구현 라운드 종료 후 변경 파일, 실제 검증, 남은 리스크를 한국어 `/work` 기록으로 남기기 위해 사용했다.

## 변경 이유
- `.pipeline/implement_handoff.md#2067`이 `/api/runtime/send-input` route test들의 반복 setup/assertion을 production behavior 변경 없이 줄이라고 지시했다.
- 앞선 send-input route guard 테스트들이 누적되면서 JSON request body encoding, invalid request JSON 응답 assertion, `HTTPStatus.BAD_REQUEST` payload 구성이 여러 테스트에 반복되어 향후 drift 위험이 있었다.

## 핵심 변경
- `ControllerAssetResolutionTests`에 `_send_input_body(...)` helper를 추가해 valid dict JSON request body encoding 반복을 줄였다.
- `ControllerAssetResolutionTests`에 `_assert_send_input_bad_request(...)` helper를 추가해 send-input invalid request의 공통 `400` JSON 응답 assertion을 한 곳으로 모았다.
- success, backend failure, empty body, missing `lane`, blank `text`, malformed JSON, malformed UTF-8, invalid/negative `Content-Length`, non-object JSON 테스트 이름과 covered cases는 유지했다.
- 각 테스트의 `runtime_send_input` / `backend_runtime_send_input` patch 대상과 call / non-call assertion은 그대로 남겨 scenario별 실패 지점을 유지했다.
- production code는 변경하지 않았다.

## 검증
- `python3 -m py_compile tests/test_controller_server.py`
  - 통과.
- `python3 -m unittest -v tests.test_controller_server`
  - 통과. `Ran 58 tests in 0.061s`, `OK`.
- `git diff --check -- tests/test_controller_server.py work/5/20/`
  - 통과.

## 남은 리스크
- 이번 라운드는 socket-free controller unit test 정리에 한정했다. Playwright, full controller smoke, broad e2e, long soak, runtime start/stop, `status --json`, `doctor --json`, `tmux` 확인은 handoff 범위 밖이라 실행하지 않았다.
- 이전 controller route family 기록의 local socket guard 환경 제약은 해소를 주장하지 않는다. controller-smoke pass나 release readiness도 주장하지 않는다.
- 작업 트리는 이전 controller/test/work/verify 라운드의 누적 변경과 새 `/verify` 기록을 포함한다. 이번 라운드에서 의도적으로 수정한 파일은 `tests/test_controller_server.py`와 이 `/work` closeout뿐이다.
