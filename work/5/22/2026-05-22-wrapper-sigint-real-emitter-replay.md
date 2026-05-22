# 2026-05-22 wrapper SIGINT real emitter replay

## 변경 파일
- `tests/test_pipeline_runtime_cli.py`
- `work/5/22/2026-05-22-wrapper-sigint-real-emitter-replay.md`

## 사용 skill
- `security-gate`: lane wrapper의 signal forwarding, shell wrapper, wrapper event log 검증을 건드리는 테스트 변경이라 로컬/승인/로그 경계를 확인했습니다.
- `finalize-lite`: 구현 마무리에서 실행한 검사, 문서 동기화 필요 여부, 남은 리스크를 좁게 점검했습니다.
- `work-log-closeout`: 실제 변경 파일과 실행한 검증만 한국어 `/work` 기록으로 남기기 위해 사용했습니다.

## 변경 이유
- CONTROL_SEQ 2136 handoff에 따라 real `_WrapperEmitter` lane-wrapper stop replay가 SIGTERM뿐 아니라 SIGINT에서도 같은 completion 계약을 만족하는지 고정했습니다.
- 직전 slice는 SIGTERM replay까지 READY였으므로, 이번 slice는 같은 local replay를 확장해 SIGINT half를 닫는 범위로 제한했습니다.

## 핵심 변경
- `test_lane_wrapper_signal_stop_with_real_emitter_emits_task_done`를 helper + `subTest` 구조로 정리해 SIGTERM과 SIGINT를 같은 deterministic replay로 실행하게 했습니다.
- SIGINT replay는 fake selector, fake child, local pipe, active task hint, 실제 `_WrapperEmitter`를 사용합니다.
- SIGINT 경로에서 wrapper event log에 `TASK_DONE(reason=stream_eof)`가 정확히 한 번 기록되고, 바로 다음 event가 `READY`인지 검증합니다.
- SIGINT replay에서 `os.killpg(child.pid, signal.SIGINT)`가 호출되는지도 검증합니다.
- 이번 slice에서는 production code를 추가 수정하지 않았습니다. `pipeline_runtime/cli.py`의 현재 diff는 이전 wrapper completion slice에서 남은 미커밋 변경입니다.

## 검증
- 통과: `python3 -m py_compile pipeline_runtime/cli.py tests/test_pipeline_runtime_cli.py`
- 통과: `python3 -m unittest tests.test_pipeline_runtime_cli.WrapperEmitterTest.test_lane_wrapper_signal_stop_with_real_emitter_emits_task_done -v`
  - 결과: `Ran 1 test`, `OK`
  - 의미: 같은 exact-name 테스트 안에서 `signal=SIGTERM`, `signal=SIGINT` subcase를 모두 실행했습니다.
- 통과: `python3 -m unittest tests.test_pipeline_runtime_cli.WrapperEmitterTest.test_text_stream_finish_emits_task_done_once_after_acceptance -v`
  - 결과: `Ran 1 test`, `OK`
- 통과: `python3 -m unittest tests.test_pipeline_runtime_cli.WrapperEmitterTest.test_claude_jsonl_stream_finish_emits_task_done -v`
  - 결과: `Ran 1 test`, `OK`

## 남은 리스크
- 이번 변경은 local unit replay입니다. live Claude dispatch나 tmux/supervisor/browser/web server는 실행하지 않았습니다.
- 전체 `tests.test_pipeline_runtime_cli` 파일과 broad runtime smoke는 실행하지 않았습니다. handoff가 focused replay와 focused completion tests로 범위를 제한했습니다.
- 기존 working tree에는 이전 CONTROL_SEQ 2131/2132/2133 관련 미커밋 변경과 여러 untracked `work/`, `verify/` 기록이 남아 있으며, 이번 slice에서 되돌리지 않았습니다.
- commit, push, branch/PR publish, merge, release, publication은 실행하지 않았습니다.
