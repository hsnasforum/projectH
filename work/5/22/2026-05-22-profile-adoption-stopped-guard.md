# 2026-05-22 profile adoption stopped guard

## 변경 파일
- `pipeline_runtime/supervisor.py`
- `work/5/22/2026-05-22-profile-adoption-stopped-guard.md`
- 검증 대상 기존 변경 파일(이번 라운드에서 수정하지 않음):
  - `tests/test_pipeline_runtime_supervisor.py`

## 사용 skill
- `work-log-closeout`: 실제 변경 파일, 실행한 검증, 결과, 남은 리스크를 한국어 `/work` 기록으로 남기기 위해 사용했습니다.

## 변경 이유
- CONTROL_SEQ 2149에 따라 stopped runtime 상태에서 `profile_adoption` mismatch가 `DEGRADED`를 만들던 회귀를 수정했습니다.
- 이전 guard는 `not runtime_inactive`를 조건으로 사용했는데, `_runtime_started=True`이면서 session, watcher, lanes가 모두 꺼진 상태를 active runtime처럼 취급했습니다.
- `tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_status_clears_live_fields_when_runtime_has_stopped`가 `STOPPED` 대신 `DEGRADED`를 받아 실패한 broad regression 결과를 닫기 위한 변경입니다.

## 핵심 변경
- `runtime_component_active`를 추가해 session alive, watcher alive, 또는 lane state가 `OFF`/빈 값이 아닌 경우만 active component로 판단하게 했습니다.
- `profile_adoption_degraded` 조건을 `not runtime_inactive`에서 `runtime_component_active`로 바꿨습니다.
- stopped runtime에서는 stale profile adoption mismatch만으로 `DEGRADED`가 되지 않게 했습니다.
- 새 테스트나 production 범위 밖 파일 수정은 하지 않았습니다.
- commit, push, branch/PR publish, merge, release, publication은 실행하지 않았습니다.

## 검증
- 통과: `python3 -m py_compile pipeline_runtime/supervisor.py`
  - 결과: PASS, 출력 없음
- 통과: `bash -o pipefail -c 'python3 -m unittest tests.test_pipeline_runtime_supervisor -v 2>&1 | tail -20'`
  - 결과: `Ran 224 tests in 1.389s`
  - 결과: `OK`
  - 요구 확인 대상인 `test_write_status_clears_live_fields_when_runtime_has_stopped`, `test_write_status_surfaces_stale_active_profile_runtime_plan`, `test_write_status_activates_claude_task_hint_for_verify_round_when_profile_current`, `test_write_status_activates_codex_task_hint_for_verify_round_without_control_slot`은 같은 full supervisor suite에 포함되어 있으며 suite 전체가 0 FAIL, 0 ERROR로 통과했습니다.
- 통과: `git diff --check -- pipeline_runtime/supervisor.py tests/test_pipeline_runtime_supervisor.py`
  - 결과: PASS, 출력 없음

## 남은 리스크
- CONTROL_SEQ 2149 범위상 `tests.test_pipeline_runtime_supervisor` full suite만 실행했습니다.
- `tests.test_pipeline_runtime_cli`, `tests.test_watcher_core`, Playwright, browser smoke, e2e, `events.jsonl` 확인은 out of scope라 실행하지 않았습니다.
