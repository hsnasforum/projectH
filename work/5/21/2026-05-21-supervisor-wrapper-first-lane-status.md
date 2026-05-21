# 2026-05-21 Supervisor wrapper-first lane status

## 변경 파일

- `pipeline_runtime/supervisor.py`
- `tests/test_pipeline_runtime_supervisor.py`
- `work/5/21/2026-05-21-supervisor-wrapper-first-lane-status.md`

## 사용 skill

- `security-gate`: lane 상태 truth 우선순위가 tmux pane 텍스트에서 wrapper event 로그 쪽으로 이동하므로, 로컬 런타임 감사 표면과 주입 방어 관점에서 범위를 확인했습니다.
- `work-log-closeout`: 변경 파일, 실제 검증, 남은 리스크를 한국어 `/work` 기록으로 남기기 위해 사용했습니다.

## 변경 이유

- wrapper event schema formalization 다음 단계로, `RuntimeSupervisor._build_lane_statuses()`가 wrapper event를 lane 상태의 우선 truth channel로 사용해야 했습니다.
- tmux pane text는 사람이 보는 보조 표면이므로, wrapper event가 TASK_ACCEPTED/TASK_DONE/BROKEN을 확정한 경우에는 tail capture 자체를 건너뛰도록 했습니다.

## 핵심 변경

- `_build_lane_statuses()`에 `wrapper_status_decisive` 계층을 추가했습니다.
  - `accepted_task`가 있으면 wrapper event만으로 `WORKING`을 확정합니다.
  - `done_task`가 있고 wrapper model이 `READY`이면 `READY`를 확정합니다.
  - wrapper model이 `BROKEN`이면 `BROKEN`을 확정합니다.
- wrapper event로 상태가 확정된 lane은 `_detect_active_lane_failure_reason()`와 `capture_tail()`을 호출하지 않습니다.
- wrapper event가 미확정인 lane은 기존 pane text fallback을 유지합니다. 이 경우에만 tail text 기반 `WORKING`/`READY` 추론으로 내려갑니다.
- 회귀 테스트를 추가했습니다.
  - TASK_ACCEPTED wrapper event가 있으면 tail capture 없이 `WORKING`.
  - TASK_DONE wrapper event가 있으면 tail capture 없이 `READY`.
  - 확정 wrapper event가 없으면 기존 pane text fallback으로 `WORKING` 추론.

## 검증

- focused 신규 테스트:
  - `python3 -m unittest -v tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_wrapper_accepted_task_skips_tail_capture_and_marks_working tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_wrapper_done_task_skips_tail_capture_and_marks_ready tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_lane_statuses_use_pane_text_fallback_without_decisive_wrapper_event`
  - 결과: `Ran 3 tests in 0.006s` / `OK`.
- 컴파일:
  - `python3 -m py_compile pipeline_runtime/supervisor.py`
  - 통과했습니다.
- supervisor 전체 테스트:
  - `bash -o pipefail -lc 'python3 -m unittest tests.test_pipeline_runtime_supervisor -v 2>&1 | tail -5'`
  - 결과: `Ran 199 tests in 1.097s` / `OK`.
- whitespace 확인:
  - `git diff --check -- pipeline_runtime/supervisor.py tests/test_pipeline_runtime_supervisor.py`
  - 통과했습니다.

## 남은 리스크

- Claude `--output-format stream-json` 연결은 이번 라운드 범위 밖이라 구현하지 않았습니다.
- `pipeline_runtime/wrapper_events.py`는 이번 라운드에서 추가 수정하지 않았습니다.
- wrapper event가 없는 lane은 여전히 tmux pane text fallback을 사용합니다. 다만 wrapper event가 확정한 상태보다 우선하지 않습니다.
- live runtime/tmux start-stop 검증은 수행하지 않았습니다.
- commit, push, PR, merge, publish는 수행하지 않았습니다.
