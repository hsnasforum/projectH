# 2026-05-22 watcher runtime status wrapper removal

## 변경 파일
- `watcher_core.py`
- `tests/test_watcher_core.py`
- `work/5/22/2026-05-22-watcher-runtime-status-wrapper-removal.md`

## 사용 skill
- `finalize-lite`: 구현 종료 전 검증 범위, 문서 동기화 필요 여부, `/work` closeout 준비 상태를 점검했습니다.
- `work-log-closeout`: 실제 변경 파일, 실행 검증, 남은 리스크를 한국어 `/work` 기록으로 남기기 위해 사용했습니다.

## 변경 이유
- trigger-9 live 관찰에서 `TASK_DONE source=wrapper lane=Claude`가 900초 deadline 안에 정상 수렴해 A3 Step 6 진입 조건이 충족됐습니다.
- `watcher_status_writer.py`와 `watcher_lane_status.py`는 이미 존재했으므로, 실제 잔여 범위는 `watcher_core.py`에 남아 있던 `_write_runtime_status()` 얇은 래퍼 제거였습니다.
- 현재 `.pipeline/implement_handoff.md`는 이미 CONTROL_SEQ 2153으로 넘어가 있었지만, 이번 라운드는 사용자의 최신 지시에 따라 CONTROL_SEQ 2152 잔여 범위만 처리했고 control slot은 수정하지 않았습니다.

## 핵심 변경
- `WatcherCore._write_runtime_status()` 메서드를 제거했습니다.
- 기존 3개 호출 지점에서 `write_runtime_status()`를 직접 호출하도록 변경했습니다.
  - runtime 시작 직후 status export
  - `_transition_turn()` 이후 control/status export
  - `_poll()` 루프의 주기적 status export
- 각 호출 지점에서 `now_iso`, active control, fallback control, lane statuses, heartbeat, current-run pointer writer를 직접 조립하도록 했습니다.
- `tests/test_watcher_core.py`의 래퍼 의존 테스트를 module-level `watcher_core.write_runtime_status` 경로로 바꿨습니다.
- `_poll()`이 startup grace 전에도 추출된 writer를 직접 호출하는 focused test를 추가했습니다.
- `watcher_core.py` 기준 `_write_runtime_status` 문자열은 0개, `write_runtime_status(` 직접 호출은 3개입니다.

## 검증
- 통과: `python3 -m py_compile watcher_core.py watcher_status_writer.py watcher_lane_status.py`
- 통과: `python3 -m unittest tests.test_watcher_status_writer tests.test_watcher_lane_status -v`
  - 결과: 7 tests OK
- 통과: `python3 -m unittest tests.test_watcher_core.WatcherPromptAssemblyTest.test_verify_prompt_context_includes_runtime_dispatch_surface -v`
  - 결과: 1 test OK
- 통과: `python3 -m unittest tests.test_watcher_core.CodexDispatchConfirmationTest.test_watcher_poll_calls_extracted_runtime_status_writer_before_startup_grace tests.test_watcher_core.CodexDispatchConfirmationTest.test_watcher_poll_answers_gemini_git_permission_prompt_before_startup_grace -v`
  - 결과: 2 tests OK
- 통과: `python3 -m unittest tests.test_watcher_core -v`
  - 결과: 266 tests OK
- 통과: `python3 -m unittest tests.test_pipeline_runtime_cli tests.test_pipeline_runtime_supervisor tests.test_watcher_core -v`
  - 결과: 549 tests OK
  - 기존 handoff 표기는 548개였지만, 이번 라운드에서 focused test 1개가 추가되어 549개로 집계됐습니다.
- 통과: `git diff --check -- watcher_core.py watcher_status_writer.py watcher_lane_status.py tests/test_watcher_core.py tests/test_watcher_status_writer.py tests/test_watcher_lane_status.py`
  - 결과: PASS, 출력 없음
- 명령 지정 오류 후 재실행: 처음에 존재하지 않는 unittest class 경로(`RuntimeStatusPromptTest`, `WatcherDispatchTest`)로 2개 selector를 실행해 실패했고, 실제 class명으로 다시 실행해 위와 같이 통과시켰습니다.

## 남은 리스크
- 브라우저/E2E는 실행하지 않았습니다. 이번 변경은 watcher runtime status writer 호출 경로의 내부 리팩터링이며, 검증 범위는 Python compile/unit/runtime suite로 충분하다고 판단했습니다.
- 직접 호출 방식은 `write_runtime_status()` 인자 묶음이 3곳에 드러납니다. 이는 사용자가 지정한 Step 6 잔여 범위를 따른 것이며, 더 줄이려면 별도 helper 재도입 여부를 다음 구조화 라운드에서 판단해야 합니다.
- 작업 시작 전부터 `.pipeline/config/agent_profile.json`, `.pipeline/config/runtime_policy.json`, `pipeline_runtime/cli.py`, `pipeline_runtime/supervisor.py`, `watcher_status_writer.py`, `watcher_lane_status.py`, 관련 테스트와 다수의 `work/`, `verify/`, `report/gemini/` 파일에 기존 dirty state가 있었습니다. 이번 라운드에서는 기존 변경을 되돌리거나 control slot을 수정하지 않았습니다.
- commit, push, branch/PR publish, merge, release, publication은 실행하지 않았습니다.
