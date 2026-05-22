# 2026-05-22 Claude wrapper signal finish stream

## 변경 파일
- `pipeline_runtime/cli.py`
- `tests/test_pipeline_runtime_cli.py`
- `work/5/22/2026-05-22-claude-wrapper-signal-finish-stream.md`

## 사용 skill
- `security-gate`: lane wrapper의 SIGTERM/SIGINT 전달과 셸 실행 종료 경로가 영향을 받는지 확인하기 위해 사용했습니다.
- `work-log-closeout`: 실제 변경 파일, 실행한 검증, 남은 리스크를 한국어 `/work` 기록으로 남기기 위해 사용했습니다.
- `finalize-lite`: 구현 마무리 단계에서 검증 정직성, 문서 동기화 필요 여부, `/work` closeout 준비 상태를 좁게 확인하기 위해 사용했습니다.

## 변경 이유
- CONTROL_SEQ 2131 handoff에 따라 `_lane_wrapper()`가 SIGTERM 또는 SIGINT로 종료 요청을 받을 때 `_WrapperEmitter.finish_stream()`을 호출하도록 보장했습니다.
- 이전 trigger-4 재관찰은 Claude lane dispatch 선행조건 미충족으로 막혔고, 이번 slice는 같은 wrapper completion 계열에서 신호 중단 시 stream finish 호출 누락 위험을 줄이는 작은 런타임 수정입니다.

## 핵심 변경
- `pipeline_runtime/cli.py`의 `_lane_wrapper()`에 `_finish_stream_once()` helper를 추가해 stream finish 호출을 한 번으로 제한했습니다.
- 기존 PTY EOF, child exit, child exit 중 `OSError` 경로의 `finish_stream()` 호출을 같은 helper로 통합했습니다.
- SIGTERM/SIGINT forwarding 후 `stop_requested`로 루프를 빠져나가기 전에 `_finish_stream_once()`를 호출하도록 했습니다.
- `tests/test_pipeline_runtime_cli.py`에 신호 요청 경로에서 `finish_stream()`이 정확히 한 번 호출되는 focused unit test를 추가했습니다.
- 보안 경계: 새 셸 명령, 외부 네트워크, 파일 삭제/덮어쓰기, 승인 우회는 추가하지 않았고 기존 wrapper event logging 경로만 유지했습니다.
- 문서 동기화: 제품/UI/승인 정책/운영자 규칙 변경이 아니라 런타임 내부 신호 종료 경로 보정이므로 별도 제품 문서는 수정하지 않았습니다.

## 검증
- 통과: `python3 -m py_compile pipeline_runtime/cli.py tests/test_pipeline_runtime_cli.py`
- 통과: `python3 -m unittest tests.test_pipeline_runtime_cli.WrapperEmitterTest.test_lane_wrapper_initializes_all_lanes_in_text_mode -v`
  - 결과: `Ran 1 test`, `OK`
- 통과: `python3 -m unittest tests.test_pipeline_runtime_cli.WrapperEmitterTest.test_lane_wrapper_finishes_stream_once_when_signal_requests_stop -v`
  - 결과: `Ran 1 test`, `OK`
- 통과: `git diff --check -- pipeline_runtime/cli.py tests/test_pipeline_runtime_cli.py work/5/22/2026-05-22-claude-wrapper-signal-finish-stream.md`
  - 결과: PASS, 출력 없음.

## 남은 리스크
- 이번 변경은 신호 중단 경로의 `finish_stream()` 호출 보장과 중복 방지에 한정됩니다. Claude lane이 실제 enabled/active 상태에서 trigger를 수신하는지 여부는 별도 verify/운영 관찰 범위입니다.
- `_WrapperEmitter.finish_stream()`의 텍스트 모드 완료 이벤트 의미 자체는 이번 slice에서 변경하지 않았습니다.
- 기존 working tree에는 CONTROL_SEQ 2129 관련 변경과 여러 untracked `work/`, `verify/` 파일이 남아 있으며, 이번 slice에서 되돌리지 않았습니다.
- commit, push, branch/PR publish, merge, release, publication은 실행하지 않았습니다.
