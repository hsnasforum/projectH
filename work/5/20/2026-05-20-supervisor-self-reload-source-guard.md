# 2026-05-20 supervisor self-reload source guard

## 변경 파일

- `pipeline_runtime/supervisor.py`
- `tests/test_pipeline_runtime_supervisor.py`
- `work/5/20/2026-05-20-supervisor-self-reload-source-guard.md`

## 사용 skill

- `work-log-closeout`: handoff 실행 결과, 실제 변경 파일, 실행한 검증, 남은 리스크를 한국어 `/work` closeout으로 남기기 위해 사용했습니다.

## 변경 이유

- `.pipeline/implement_handoff.md#2005`가 `pipeline_runtime/supervisor.py` 자체 변경이 watcher self-restart source marker에 잡히지 않는 freshness gap을 닫도록 요구했습니다.
- 직전 라운드는 `pipeline_runtime/automation_health.py`를 self-restart source set에 추가했지만, 그 source set 자체가 `pipeline_runtime/supervisor.py` 안에 있어 running watcher가 supervisor 변경을 reload 대상으로 보지 못할 수 있었습니다.
- 이번 라운드는 live watcher/runtime 재시작이나 status resample이 아니라, supervisor self-file omission을 unit-level guard로 보강하는 범위입니다.

## 핵심 변경

- `_WATCHER_SELF_RESTART_SOURCE_NAMES`에 `pipeline_runtime/supervisor.py`를 추가했습니다.
- `test_supervisor_source_change_marks_watcher_restart_source`를 추가했습니다.
- 새 regression은 임시 프로젝트에서 `pipeline_runtime/supervisor.py` mtime을 `experimental.pid`보다 최신으로 만들고, `_watcher_source_restart_marker()`의 `source_path`가 supervisor source를 가리키는지 확인합니다.
- 기존 watcher source restart regression과 인접 automation health marker regression은 유지했습니다.
- `.pipeline/advisory_request.md`, `.pipeline/operator_request.md`는 작성하지 않았고, commit, push, branch/PR publication, merge, release, live watcher/runtime restart도 수행하지 않았습니다.

## 검증

- `sha256sum .pipeline/implement_handoff.md`
  - 결과: PASS. 요청 SHA `fa3e3eabb1b658b5c6d0ff9e3b73dec255206637e1a42d788f479d029c7dd58c`와 일치했습니다.
- `python3 -m py_compile pipeline_runtime/supervisor.py tests/test_pipeline_runtime_supervisor.py`
  - 결과: PASS.
- `python3 -m unittest -v tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_watcher_source_change_restarts_watcher_without_operator_decision tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_supervisor_source_change_marks_watcher_restart_source`
  - 결과: PASS. `Ran 2 tests in 0.009s`, `OK`.
- `python3 -m unittest -v tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_automation_health_source_change_marks_watcher_restart_source`
  - 결과: PASS. `Ran 1 test in 0.003s`, `OK`.
- `git diff --check -- pipeline_runtime/supervisor.py tests/test_pipeline_runtime_supervisor.py`
  - 결과: PASS. 출력 없음.
- `git diff --check -- pipeline_runtime/supervisor.py tests/test_pipeline_runtime_supervisor.py work/5/20/2026-05-20-supervisor-self-reload-source-guard.md`
  - 결과: PASS. 출력 없음.
- `git diff --check --no-index -- /dev/null work/5/20/2026-05-20-supervisor-self-reload-source-guard.md`
  - 결과: PASS. diff 존재로 exit code는 1이지만 whitespace error 출력은 없었습니다.

## 남은 리스크

- 이번 라운드는 watcher self-restart source set의 supervisor self-file omission만 다뤘습니다. CLI/runtime reload source list의 `pipeline_runtime/automation_health.py` 누락 가능성은 직전 `/verify`에 남은 별도 리스크로 기록돼 있지만 이번 handoff 범위 밖이었습니다.
- live watcher/runtime은 재시작하지 않았습니다. 실제 running watcher가 새 source list로 reload되는지는 verify/handoff lane의 다음 runtime surface 확인 대상입니다.
- 작업트리는 handoff 시작 전부터 여러 파일이 dirty 상태였습니다. 이번 #2005 라운드에서 직접 추가한 동작은 `pipeline_runtime/supervisor.py`의 supervisor source entry와 `tests/test_pipeline_runtime_supervisor.py`의 supervisor marker regression입니다.
- controller Playwright/webServer/full-smoke, broad unit, long soak는 실행하지 않았습니다. 이번 변경이 browser-visible contract나 controller webServer를 바꾸지 않았기 때문입니다.
