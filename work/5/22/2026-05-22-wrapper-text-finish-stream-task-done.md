# 2026-05-22 wrapper text finish stream TASK_DONE

## 변경 파일
- `pipeline_runtime/cli.py`
- `tests/test_pipeline_runtime_cli.py`
- `work/5/22/2026-05-22-wrapper-text-finish-stream-task-done.md`

## 사용 skill
- `security-gate`: lane wrapper의 runtime control, shell execution 종료 경로, wrapper event logging 영향을 확인하기 위해 사용했습니다.
- `work-log-closeout`: 실제 변경 파일, 실행한 검증, 남은 리스크를 한국어 `/work` 기록으로 남기기 위해 사용했습니다.
- `finalize-lite`: 구현 마무리 단계에서 검증 정직성, 문서 동기화 필요 여부, `/work` closeout 준비 상태를 좁게 확인하기 위해 사용했습니다.

## 변경 이유
- CONTROL_SEQ 2132 handoff에 따라 `_WrapperEmitter.finish_stream()` 호출이 accepted text-mode task에서도 wrapper `TASK_DONE`/`READY` 의미를 갖도록 보정했습니다.
- 직전 slice는 `_lane_wrapper()`가 SIGTERM/SIGINT 경로에서 `finish_stream()`을 호출하도록 만들었지만, text-mode `finish_stream()` 자체가 `TASK_DONE`을 내지 않는 잔여 리스크가 남아 있었습니다.

## 핵심 변경
- `pipeline_runtime/cli.py`에서 `_WrapperEmitter.finish_stream()`이 `jsonl_mode` 여부와 무관하게 기존 `_on_claude_completion("stream_eof")` helper를 호출하도록 변경했습니다.
- accepted task가 없는 상태에서는 기존 helper guard로 `TASK_DONE`을 내지 않으며, accepted task 완료 뒤 반복 호출해도 `accepted_key`가 비워져 중복 `TASK_DONE`이 나지 않는 기존 completion path를 재사용했습니다.
- `tests/test_pipeline_runtime_cli.py`에 `test_text_stream_finish_emits_task_done_once_after_acceptance`를 추가해 text-mode accepted task가 `stream_eof` reason의 `TASK_DONE`을 정확히 한 번 내는지 고정했습니다.
- 기존 JSONL stream EOF completion test와 직전 signal stop path test를 함께 재실행해 JSONL 동작과 wrapper signal path가 유지되는지 확인했습니다.
- 보안 경계: 새 셸 명령 실행 경로, 외부 네트워크, 파일 삭제/덮어쓰기, 승인 우회는 추가하지 않았고 기존 wrapper event 기록 경로만 사용했습니다.
- 문서 동기화: 제품/UI/승인 정책/운영자 규칙 변경이 아니라 runtime wrapper completion 내부 보정이므로 별도 제품 문서는 수정하지 않았습니다.

## 검증
- 통과: `python3 -m py_compile pipeline_runtime/cli.py tests/test_pipeline_runtime_cli.py`
- 통과: `python3 -m unittest tests.test_pipeline_runtime_cli.WrapperEmitterTest.test_text_stream_finish_emits_task_done_once_after_acceptance -v`
  - 결과: `Ran 1 test`, `OK`
- 통과: `python3 -m unittest tests.test_pipeline_runtime_cli.WrapperEmitterTest.test_claude_jsonl_stream_finish_emits_task_done -v`
  - 결과: `Ran 1 test`, `OK`
- 통과: `python3 -m unittest tests.test_pipeline_runtime_cli.WrapperEmitterTest.test_lane_wrapper_finishes_stream_once_when_signal_requests_stop -v`
  - 결과: `Ran 1 test`, `OK`
- 통과: `git diff --check -- pipeline_runtime/cli.py tests/test_pipeline_runtime_cli.py work/5/22/2026-05-22-wrapper-text-finish-stream-task-done.md`
  - 결과: PASS, 출력 없음.

## 남은 리스크
- 이번 변경은 wrapper completion semantics에 한정됩니다. Claude lane이 실제 enabled/active 상태에서 trigger work를 수신하는지 여부는 이번 implement slice에서 live로 재관찰하지 않았습니다.
- 전체 `tests.test_pipeline_runtime_cli` 파일과 broad runtime smoke는 실행하지 않았습니다. 변경 범위가 `_WrapperEmitter.finish_stream()`와 focused unit coverage에 한정되어 요청된 좁은 검증만 수행했습니다.
- 기존 working tree에는 CONTROL_SEQ 2129/2131 관련 미커밋 변경과 여러 untracked `work/`, `verify/` 기록이 남아 있으며, 이번 slice에서 되돌리지 않았습니다.
- commit, push, branch/PR publish, merge, release, publication은 실행하지 않았습니다.
