# 2026-05-21 Pane text fallback telemetry

## 변경 파일

- `pipeline_runtime/supervisor.py`
- `tests/test_pipeline_runtime_supervisor.py`
- `work/5/21/2026-05-21-pane-text-fallback-telemetry.md`

## 사용 skill

- `security-gate`: pane text fallback 사용 사실을 supervisor event log에 남기는 변경이라, raw pane text를 기록하지 않는 audit boundary를 확인했습니다.
- `work-log-closeout`: 변경 파일, 실제 검증, 남은 리스크를 한국어 `/work` 기록으로 남기기 위해 사용했습니다.

## 변경 이유

- wrapper event가 상태를 확정하지 못해 tmux pane text fallback으로 내려간 순간을 운영 중 관측 가능하게 만들기 위함입니다.
- 이 이벤트는 실패가 아니라 telemetry이며, Codex/Gemini 등 구조화 이벤트가 아직 부족한 lane의 fallback 의존도를 증거 기반으로 판단하기 위한 기록입니다.

## 핵심 변경

- `RuntimeSupervisor.__init__`에 lane별 dedupe 상태인 `_last_pane_fallback_key`를 추가했습니다.
- `_build_lane_statuses()`의 pane text fallback 브랜치에서 `pane_text_fallback_used` 이벤트를 기록합니다.
- payload는 `lane`, `model_state`, `active_lane`, `control_status`, `tail_captured`, `surface_reason`만 포함합니다.
- raw `tail_text`와 pane 원문은 payload와 event log에 기록하지 않도록 테스트로 확인했습니다.
- 같은 lane에서 `model_state|control_status|tail_captured` key가 반복되면 중복 기록하지 않고, key가 바뀌면 다시 기록합니다.

## 검증

- focused telemetry 테스트:
  - `python3 -m unittest -v tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_pane_text_fallback_telemetry_is_not_emitted_for_decisive_wrapper_event tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_pane_text_fallback_telemetry_records_without_raw_tail_text tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_pane_text_fallback_telemetry_dedupes_same_lane_key tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_pane_text_fallback_telemetry_reemits_when_key_changes`
  - 결과: `Ran 4 tests in 0.013s` / `OK`.
- 보정 후 focused 확인:
  - `python3 -m unittest -v tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_record_status_events_preserves_local_socket_guard_automation_incident tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_pane_text_fallback_telemetry_records_without_raw_tail_text`
  - 결과: `Ran 2 tests in 0.013s` / `OK`.
- 컴파일:
  - `python3 -m py_compile pipeline_runtime/supervisor.py`
  - 통과했습니다.
- supervisor 전체 테스트:
  - `bash -o pipefail -lc 'python3 -m unittest tests.test_pipeline_runtime_supervisor -v 2>&1 | tail -5'`
  - 최종 결과: `Ran 203 tests in 1.143s` / `OK`.
- whitespace 확인:
  - `git diff --check -- pipeline_runtime/supervisor.py tests/test_pipeline_runtime_supervisor.py`
  - 통과했습니다.

## 남은 리스크

- 이 라운드는 telemetry만 추가했으며 `_build_lane_statuses()`의 `state` / `note` 판정 결과는 의도적으로 바꾸지 않았습니다.
- dedupe key는 요청 범위대로 `model_state|control_status|tail_captured`만 사용합니다. `active_lane`이나 `surface_reason` 변화만으로는 재기록하지 않습니다.
- live runtime/tmux start-stop 검증은 수행하지 않았습니다.
- wrapper event schema, `cli.py`, Codex/Gemini 구조화 출력, Unix socket IPC는 이번 범위 밖이라 건드리지 않았습니다.
- commit, push, PR, merge, publish는 수행하지 않았습니다.
