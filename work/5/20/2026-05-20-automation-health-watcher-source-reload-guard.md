# 2026-05-20 automation health watcher source reload guard

## 변경 파일

- `pipeline_runtime/supervisor.py`
- `tests/test_pipeline_runtime_supervisor.py`
- `work/5/20/2026-05-20-automation-health-watcher-source-reload-guard.md`

## 사용 skill

- `work-log-closeout`: handoff 실행 결과, 실제 변경 파일, 실행한 검증, 남은 리스크를 한국어 `/work` closeout으로 남기기 위해 사용했습니다.

## 변경 이유

- `.pipeline/implement_handoff.md#2004`가 `pipeline_runtime/automation_health.py` 변경 후 running watcher가 stale helper code를 계속 사용할 수 있는 source reload freshness gap을 닫도록 요구했습니다.
- 직전 검증은 current source가 active verify round mismatch를 `recovering/dispatch_stall/retrying`과 `automation_health_source`로 계산하지만, file-backed watcher status에는 여전히 stale `ok/continue`와 provenance 누락이 남을 수 있음을 확인했습니다.
- 이번 라운드는 live watcher 재시작이나 status resample이 아니라, automation health helper 변경이 기존 watcher self-restart source guard에 포함되도록 하는 단위 수준 guard 보강입니다.

## 핵심 변경

- `_WATCHER_SELF_RESTART_SOURCE_NAMES`에 `pipeline_runtime/automation_health.py`를 추가했습니다.
- watcher source reload marker가 `experimental.pid`보다 최신인 automation health helper를 감지할 수 있게 했습니다.
- `test_automation_health_source_change_marks_watcher_restart_source`를 추가해, helper mtime이 pidfile보다 최신이면 marker의 `source_path`가 `pipeline_runtime/automation_health.py`를 가리키는지 확인했습니다.
- 기존 watcher source restart regression은 유지했고, 새 regression은 실제 watcher/runtime을 재시작하지 않는 marker 단위 검증으로 제한했습니다.
- `.pipeline/advisory_request.md`, `.pipeline/operator_request.md`는 작성하지 않았고, commit, push, branch/PR publication, merge, release, live watcher/runtime restart도 수행하지 않았습니다.

## 검증

- `sha256sum .pipeline/implement_handoff.md`
  - 결과: PASS. 요청 SHA `f5333b5f3920bcb5d3e4e1c66abbb0a389272d27302b52430d3f405c3f6ba1f2`와 일치했습니다.
- `python3 -m py_compile pipeline_runtime/supervisor.py pipeline_runtime/automation_health.py tests/test_pipeline_runtime_supervisor.py tests/test_pipeline_runtime_automation_health.py`
  - 결과: PASS.
- `python3 -m unittest -v tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_watcher_source_change_restarts_watcher_without_operator_decision tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_automation_health_source_change_marks_watcher_restart_source`
  - 결과: PASS. `Ran 2 tests in 0.010s`, `OK`.
- `git diff --check -- pipeline_runtime/supervisor.py tests/test_pipeline_runtime_supervisor.py pipeline_runtime/automation_health.py tests/test_pipeline_runtime_automation_health.py`
  - 결과: PASS. 출력 없음.
- `git diff --check -- pipeline_runtime/supervisor.py tests/test_pipeline_runtime_supervisor.py pipeline_runtime/automation_health.py tests/test_pipeline_runtime_automation_health.py work/5/20/2026-05-20-automation-health-watcher-source-reload-guard.md`
  - 결과: PASS. 출력 없음.
- `git diff --check --no-index -- /dev/null work/5/20/2026-05-20-automation-health-watcher-source-reload-guard.md`
  - 결과: PASS. diff 존재로 exit code는 1이지만 whitespace error 출력은 없었습니다.

## 남은 리스크

- 이번 라운드는 watcher self-restart source guard만 다뤘습니다. controller Playwright/webServer/full-smoke, broad unit, long soak는 실행하지 않았습니다.
- live watcher/runtime은 재시작하지 않았습니다. 실제 running watcher가 새 source list로 reload되는지는 verify/handoff lane의 다음 runtime surface 확인 대상입니다.
- 작업트리는 handoff 시작 전부터 여러 파일이 dirty 상태였습니다. 이번 라운드에서 직접 편집한 source/test 파일은 `pipeline_runtime/supervisor.py`와 `tests/test_pipeline_runtime_supervisor.py`뿐입니다.
