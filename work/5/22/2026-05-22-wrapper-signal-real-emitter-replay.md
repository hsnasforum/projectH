# 2026-05-22 wrapper signal real emitter replay

## 변경 파일
- `tests/test_pipeline_runtime_cli.py`
- `work/5/22/2026-05-22-wrapper-signal-real-emitter-replay.md`

## 사용 skill
- `security-gate`: lane wrapper의 SIGTERM forwarding, shell execution wrapper, wrapper event logging을 로컬 replay로 검증하는 변경이라 사용했습니다.
- `work-log-closeout`: 실제 변경 파일, 실행한 검증, 남은 리스크를 한국어 `/work` 기록으로 남기기 위해 사용했습니다.
- `finalize-lite`: 구현 마무리 단계에서 검증 정직성, 문서 동기화 필요 여부, `/work` closeout 준비 상태를 좁게 확인하기 위해 사용했습니다.

## 변경 이유
- CONTROL_SEQ 2133 handoff에 따라 lane-wrapper SIGTERM/SIGINT stop path, real `_WrapperEmitter`, active task hint, text-mode stream finish가 결합될 때 wrapper `TASK_DONE`/`READY`가 실제 event log에 남는지 고정했습니다.
- 직전 두 slice는 signal stop path의 `finish_stream()` 호출과 text-mode `finish_stream()`의 `TASK_DONE` 의미를 분리해 검증했으므로, 이번 slice는 그 두 계약을 하나의 로컬 replay로 연결했습니다.

## 핵심 변경
- `tests/test_pipeline_runtime_cli.py`에 `test_lane_wrapper_signal_stop_with_real_emitter_emits_task_done`를 추가했습니다.
- 새 테스트는 fake selector와 pipe로 text-mode output `Working (synthetic claude verify)`를 주입해 실제 `_WrapperEmitter`가 `DISPATCH_SEEN`/`TASK_ACCEPTED`를 기록하게 합니다.
- 이어서 captured SIGTERM handler를 호출해 `_lane_wrapper()`의 `stop_requested` 경로를 타게 하고, wrapper event log에 `TASK_DONE(reason=stream_eof)`가 정확히 한 번 기록되는지 확인합니다.
- 같은 replay에서 `TASK_DONE` 직후 `READY`가 기록되는지, `os.killpg()`가 SIGTERM으로 호출되는지, selector가 닫히는지도 확인했습니다.
- 이번 slice에서는 `pipeline_runtime/cli.py` production code를 추가 수정하지 않았습니다. 해당 파일의 현재 diff는 이전 CONTROL_SEQ 2131/2132 slice에서 남은 미커밋 변경입니다.
- 보안 경계: 테스트는 로컬 pipe, fake selector, fake child process만 사용하며 tmux, supervisor, browser, web server, networked command를 시작하지 않습니다.

## 검증
- 통과: `python3 -m unittest tests.test_pipeline_runtime_cli.WrapperEmitterTest.test_lane_wrapper_signal_stop_with_real_emitter_emits_task_done -v`
  - 결과: `Ran 1 test`, `OK`
- 통과: `python3 -m py_compile pipeline_runtime/cli.py tests/test_pipeline_runtime_cli.py`
- 통과: `python3 -m unittest tests.test_pipeline_runtime_cli.WrapperEmitterTest.test_text_stream_finish_emits_task_done_once_after_acceptance -v`
  - 결과: `Ran 1 test`, `OK`
- 통과: `python3 -m unittest tests.test_pipeline_runtime_cli.WrapperEmitterTest.test_claude_jsonl_stream_finish_emits_task_done -v`
  - 결과: `Ran 1 test`, `OK`
- 통과: `python3 -m unittest tests.test_pipeline_runtime_cli.WrapperEmitterTest.test_lane_wrapper_finishes_stream_once_when_signal_requests_stop -v`
  - 결과: `Ran 1 test`, `OK`
- 통과: `git diff --check -- pipeline_runtime/cli.py tests/test_pipeline_runtime_cli.py work/5/22/2026-05-22-wrapper-signal-real-emitter-replay.md`
  - 결과: PASS, 출력 없음.

## 남은 리스크
- 이번 변경은 local unit replay입니다. Claude lane이 실제 enabled/active 상태에서 trigger work를 수신하는지는 live로 재관찰하지 않았습니다.
- 전체 `tests.test_pipeline_runtime_cli` 파일과 broad runtime smoke는 실행하지 않았습니다. handoff 범위가 focused replay와 기존 focused completion tests에 한정되어 좁은 검증만 수행했습니다.
- 기존 working tree에는 CONTROL_SEQ 2129/2131/2132 관련 미커밋 변경과 여러 untracked `work/`, `verify/` 기록이 남아 있으며, 이번 slice에서 되돌리지 않았습니다.
- commit, push, branch/PR publish, merge, release, publication은 실행하지 않았습니다.
