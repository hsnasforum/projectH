# 2026-05-22 wrapper child-exit real emitter replay

## 변경 파일
- `tests/test_pipeline_runtime_cli.py`
- `work/5/22/2026-05-22-wrapper-child-exit-real-emitter-replay.md`

## 사용 skill
- `security-gate`: lane wrapper의 child-exit/PTY EOF 경로, shell wrapper 감시, wrapper event log 검증을 건드리는 테스트 변경이라 로컬/로그/실행 경계를 확인했습니다.
- `finalize-lite`: 구현 마무리에서 실행한 검사, 문서 동기화 필요 여부, 남은 리스크를 좁게 점검했습니다.
- `work-log-closeout`: 실제 변경 파일과 실행한 검증만 한국어 `/work` 기록으로 남기기 위해 사용했습니다.

## 변경 이유
- CONTROL_SEQ 2140 handoff에 따라 real `_WrapperEmitter` lane-wrapper completion replay를 child-exit/PTY EOF 경로까지 확장했습니다.
- 직전 slice에서 SIGTERM/SIGINT signal stop 경로는 READY로 확인됐으므로, 이번 slice는 `_lane_wrapper()`의 `child.poll() is not None` branch가 같은 `TASK_DONE(reason=stream_eof)`/`READY` 계약을 만족하는지 고정했습니다.

## 핵심 변경
- `tests/test_pipeline_runtime_cli.py`에 `test_lane_wrapper_child_exit_with_real_emitter_emits_task_done`를 추가했습니다.
- 새 replay는 fake selector, fake child, local pipe, fake stdout, active task hint, 실제 `_WrapperEmitter`를 사용합니다.
- fake selector가 text-mode output `Working (synthetic claude verify)`를 한 번 공급한 뒤 writer fd를 닫아 PTY EOF를 만들고, fake child가 `poll() == 0`을 반환해 child-exit branch를 타게 했습니다.
- wrapper event log에 `TASK_DONE(reason=stream_eof)`가 정확히 한 번 기록되고, 바로 다음 event가 `READY`인지 검증합니다.
- selector close와 child `wait()` 호출도 함께 확인했습니다.
- 이번 slice에서는 production code를 추가 수정하지 않았습니다. `pipeline_runtime/cli.py`의 현재 diff와 `.pipeline/config/agent_profile.json` 변경은 기존 미커밋 상태로 남아 있으며 되돌리지 않았습니다.

## 검증
- 통과: `python3 -m py_compile pipeline_runtime/cli.py tests/test_pipeline_runtime_cli.py`
- 통과: `python3 -m unittest tests.test_pipeline_runtime_cli.WrapperEmitterTest.test_lane_wrapper_child_exit_with_real_emitter_emits_task_done -v`
  - 결과: `Ran 1 test`, `OK`
- 통과: `python3 -m unittest tests.test_pipeline_runtime_cli.WrapperEmitterTest.test_lane_wrapper_signal_stop_with_real_emitter_emits_task_done -v`
  - 결과: `Ran 1 test`, `OK`
- 통과: `python3 -m unittest tests.test_pipeline_runtime_cli.WrapperEmitterTest.test_text_stream_finish_emits_task_done_once_after_acceptance -v`
  - 결과: `Ran 1 test`, `OK`
- 통과: `python3 -m unittest tests.test_pipeline_runtime_cli.WrapperEmitterTest.test_claude_jsonl_stream_finish_emits_task_done -v`
  - 결과: `Ran 1 test`, `OK`

## 남은 리스크
- 이번 변경은 local unit replay입니다. live Claude dispatch, tmux, supervisor, browser, web server, networked command는 실행하지 않았습니다.
- 전체 `tests.test_pipeline_runtime_cli` 파일, broad runtime smoke, controller/browser smoke, full smoke는 실행하지 않았습니다. handoff가 focused replay와 focused completion tests로 범위를 제한했습니다.
- 기존 working tree에는 이전 CONTROL_SEQ 2131/2132/2133/2136 관련 미커밋 변경과 여러 untracked `work/`, `verify/`, `report/` 기록이 남아 있으며, 이번 slice에서 되돌리지 않았습니다.
- commit, push, branch/PR publish, merge, release, publication은 실행하지 않았습니다.
