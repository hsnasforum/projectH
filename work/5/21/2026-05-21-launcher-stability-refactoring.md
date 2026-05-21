# 2026-05-21 Launcher stability refactoring

## 변경 파일

- `pipeline-launcher.py`
- `tests/test_pipeline_launcher.py`
- `work/5/21/2026-05-21-launcher-stability-refactoring.md`

## 사용 skill

- `security-gate`: launcher가 subprocess 실행, background cancel, curses terminal 복구를 다루므로 로컬 실행 경계와 누수 위험을 점검했습니다.
- `work-log-closeout`: 변경 파일, 실제 검증, 남은 리스크를 한국어 `/work` 기록으로 남기기 위해 사용했습니다.

## 변경 이유

- WSL/Windows 환경에서 runtime CLI spawn 시 working directory가 불안정할 수 있는 경로를 줄였습니다.
- stop/restart background action이 오래 걸리거나 launcher 종료가 들어와도 하위 subprocess를 종료할 수 있도록 했습니다.
- runtime attach 중 예외나 `KeyboardInterrupt`가 발생해도 curses terminal 상태를 복구하도록 방어했습니다.
- polling loop에서 반복되는 active profile / runtime adapter 해석 I/O를 캐시해 불필요한 파일 읽기를 줄였습니다.

## 핵심 변경

- `_spawn_runtime_cli()`가 `subprocess.Popen` handle을 반환하게 하고, Windows/WSL 경로에서는 `cwd=str(project)`를 명시했습니다.
- `_run_runtime_cli()`를 `subprocess.run()` 기반에서 `Popen` 기반으로 바꿔 timeout, cancel event, process registration을 처리하게 했습니다.
- `BackgroundAction`에 subprocess registry와 `cancel()`을 추가했고, launcher `q` 입력 시 진행 중인 background action을 취소하도록 연결했습니다.
- `pipeline_stop()` / `pipeline_restart()`의 background 경로가 실행 중인 runtime CLI process를 `BackgroundAction`에 등록합니다.
- `configure_curses_screen()` helper를 추가하고, `a` attach 경로를 `try/finally`로 감싸 curses mode, cursor, timeout, color, resize 상태를 복구합니다.
- `resolve_project_active_profile()` / `resolve_project_runtime_adapter()` 결과를 active profile 파일의 `mtime_ns + size` 기준으로 캐시했습니다.
- launcher 단위 테스트에 Windows cwd, background cancel, runtime adapter cache, timeout 처리 검증을 추가했습니다.

## 검증

- `python3 -m py_compile pipeline-launcher.py`
  - 통과했습니다.
- `python3 -m unittest tests.test_pipeline_launcher -v`
  - 통과했습니다. `Ran 40 tests in 0.203s`
- `git diff --check -- pipeline-launcher.py tests/test_pipeline_launcher.py`
  - 통과했습니다.

## 남은 리스크

- 실제 TUI 수동 검증(`python3 pipeline-launcher.py .` 후 `s/t/r/a/q`)은 실행하지 않았습니다.
- `q` 입력은 등록된 subprocess에 terminate/kill을 보내지만, launcher 종료 전 background thread join까지 기다리지는 않습니다.
- profile cache는 active profile 파일의 `mtime_ns + size` 기준입니다. 같은 메타데이터로 파일 내용만 바뀌는 비정상 케이스는 즉시 감지하지 못할 수 있습니다.
- commit, push, PR, merge, publish는 수행하지 않았습니다.
