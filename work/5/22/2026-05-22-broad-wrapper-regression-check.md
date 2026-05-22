# 2026-05-22 broad wrapper regression check

## 변경 파일
- `work/5/22/2026-05-22-broad-wrapper-regression-check.md`
- 검증 대상 기존 변경 파일(이번 라운드에서 수정하지 않음):
  - `pipeline_runtime/cli.py`
  - `pipeline_runtime/supervisor.py`
  - `watcher_core.py`
  - `tests/test_pipeline_runtime_cli.py`
  - `tests/test_pipeline_runtime_supervisor.py`
  - `tests/test_watcher_core.py`

## 사용 skill
- `work-log-closeout`: 실행한 검증, 실패 결과, 미수정 범위, 남은 리스크를 한국어 `/work` 기록으로 남기기 위해 사용했습니다.

## 변경 이유
- CONTROL_SEQ 2148에 따라 wrapper-completion 관련 이전 verify note들에 남아 있던 "전체 suite 실행하지 않음" 잔여 리스크를 한 번의 회귀 확인으로 닫으려 했습니다.
- 이번 slice는 검증 전용이며 production code, 테스트, `.pipeline/` control slot을 수정하지 않는 범위였습니다.

## 핵심 변경
- 지정된 세 source 파일에 대해 `py_compile`을 실행했습니다.
- 지정된 세 test module의 full unittest suite를 실행했습니다.
- 지정된 여섯 파일에 대해 `git diff --check`를 실행했습니다.
- full unittest suite에서 1개 실패가 확인되어 production code 수정은 시도하지 않았습니다.
- commit, push, branch/PR publish, merge, release, publication은 실행하지 않았습니다.

## 검증
- 통과: `python3 -m py_compile pipeline_runtime/cli.py pipeline_runtime/supervisor.py watcher_core.py`
  - 결과: PASS, 출력 없음
- 실패: `bash -o pipefail -c 'python3 -m unittest tests.test_pipeline_runtime_cli tests.test_pipeline_runtime_supervisor tests.test_watcher_core -v 2>&1 | tail -30'`
  - 결과: `Ran 548 tests in 11.154s`
  - 결과: `FAILED (failures=1)`
  - 실패 테스트: `tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_status_clears_live_fields_when_runtime_has_stopped`
  - 실패 메시지: `AssertionError: 'DEGRADED' != 'STOPPED'`
  - 실패 위치: `tests/test_pipeline_runtime_supervisor.py`, line 1578
- 통과: `git diff --check -- pipeline_runtime/cli.py pipeline_runtime/supervisor.py watcher_core.py tests/test_pipeline_runtime_cli.py tests/test_pipeline_runtime_supervisor.py tests/test_watcher_core.py`
  - 결과: PASS, 출력 없음

## 남은 리스크
- `tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_status_clears_live_fields_when_runtime_has_stopped`가 실패해 broad wrapper regression gap은 닫히지 않았습니다.
- handoff failure criteria에 따라 production code 수정은 이번 slice에서 수행하지 않았습니다.
- Playwright, browser smoke, e2e, `events.jsonl` 확인은 out of scope라 실행하지 않았습니다.
