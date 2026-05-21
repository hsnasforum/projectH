# 2026-05-20 cli runtime reload automation health source guard

## 변경 파일

- `pipeline_runtime/cli.py`
- `tests/test_pipeline_runtime_cli.py`
- `work/5/20/2026-05-20-cli-runtime-reload-automation-health-source-guard.md`

## 사용 skill

- `work-log-closeout`: handoff 실행 결과, 실제 변경 파일, 실행한 검증, 남은 리스크를 한국어 `/work` closeout으로 남기기 위해 사용했습니다.

## 변경 이유

- `.pipeline/implement_handoff.md#2006`이 CLI/runtime reload source list에서 `pipeline_runtime/automation_health.py`가 빠진 freshness gap을 닫도록 요구했습니다.
- watcher self-restart source set은 이미 automation health helper를 감시하지만, CLI start/reconcile 경로의 `_runtime_source_newer_than_supervisor_pidfile()`는 `_RUNTIME_RELOAD_SOURCE_NAMES`만 보기 때문에 같은 helper 변경을 supervisor reload 필요 조건으로 보지 못할 수 있었습니다.
- 이번 라운드는 live watcher/runtime 재시작이나 status resample이 아니라, CLI reload source list와 unit-level regression만 보강하는 범위였습니다.

## 핵심 변경

- `_RUNTIME_RELOAD_SOURCE_NAMES`에 `pipeline_runtime/automation_health.py`를 추가했습니다.
- `test_automation_health_source_newer_than_supervisor_pidfile_requests_reload`를 추가했습니다.
- 새 regression은 임시 프로젝트에서 `pipeline_runtime/automation_health.py` mtime을 `.pipeline/supervisor.pid`보다 최신으로 만들고, `_runtime_source_newer_than_supervisor_pidfile(project_root)`가 `True`를 반환하는지 확인합니다.
- 기존 `watcher_core.py` 기반 reload regression은 유지했습니다.
- `.pipeline/advisory_request.md`, `.pipeline/operator_request.md`는 작성하지 않았고, commit, push, branch/PR publication, merge, release, live watcher/runtime restart도 수행하지 않았습니다.

## 검증

- `sha256sum .pipeline/implement_handoff.md`
  - 결과: PASS. 요청 SHA `99a62db7e01d2888495692b623d2df485576846394e42c722d4b553385ab2e4e`와 일치했습니다.
- `python3 -m py_compile pipeline_runtime/cli.py tests/test_pipeline_runtime_cli.py`
  - 결과: PASS.
- `python3 -m unittest -v tests.test_pipeline_runtime_cli.SupervisorCliTest.test_runtime_source_newer_than_supervisor_pidfile_requests_reload tests.test_pipeline_runtime_cli.SupervisorCliTest.test_automation_health_source_newer_than_supervisor_pidfile_requests_reload`
  - 결과: PASS. `Ran 2 tests in 0.004s`, `OK`.
- `git diff --check -- pipeline_runtime/cli.py tests/test_pipeline_runtime_cli.py`
  - 결과: PASS. 출력 없음.
- `git diff --check -- pipeline_runtime/cli.py tests/test_pipeline_runtime_cli.py work/5/20/2026-05-20-cli-runtime-reload-automation-health-source-guard.md`
  - 결과: PASS. 출력 없음.
- `git diff --check --no-index -- /dev/null work/5/20/2026-05-20-cli-runtime-reload-automation-health-source-guard.md`
  - 결과: PASS. diff 존재로 exit code는 1이지만 whitespace error 출력은 없었습니다.

## 남은 리스크

- 이번 라운드는 CLI/runtime reload source list의 automation health helper 누락만 다뤘습니다. watcher self-restart source set, supervisor self-file guard, active verify round status provenance 자체는 이전 라운드 범위였습니다.
- live watcher/runtime은 재시작하지 않았습니다. 실제 running runtime이 새 reload source list를 반영하는지는 verify/handoff lane의 다음 runtime surface 확인 대상입니다.
- 작업트리는 handoff 시작 전부터 여러 파일이 dirty 상태였습니다. 이번 #2006 라운드에서 직접 편집한 source/test 파일은 `pipeline_runtime/cli.py`와 `tests/test_pipeline_runtime_cli.py`뿐입니다.
- controller Playwright/webServer/full-smoke, broad unit, long soak는 실행하지 않았습니다. 이번 변경이 browser-visible contract나 controller webServer를 바꾸지 않았기 때문입니다.
