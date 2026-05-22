# 2026-05-22 verify done deadline runtime policy

## 변경 파일
- `.pipeline/config/runtime_policy.json`
- `pipeline_runtime/supervisor.py`
- `watcher_core.py`
- `tests/test_pipeline_runtime_supervisor.py`
- `tests/test_watcher_core.py`
- `work/5/22/2026-05-22-verify-done-deadline-runtime-policy.md`

## 사용 skill
- `work-log-closeout`: 실제 변경 파일, 실행한 검증, 남은 리스크를 한국어 `/work` 기록으로 남기기 위해 사용했습니다.

## 변경 이유
- live run `20260522T040034Z-p31147`에서 Claude verify lane은 wrapper `TASK_ACCEPTED`까지 정상 도달했지만, `TASK_DONE`이 45초 deadline 안에 기록되지 않아 completion stall로 판정됐습니다.
- 같은 run에서 Codex도 약 40초가 걸려 기존 45초 deadline은 정상 verify 작업에도 너무 좁은 경계로 확인됐습니다.
- 이번 slice의 목표는 verify `TASK_DONE` 대기 deadline을 runtime policy로 명시하고, watcher 실행 인자까지 전달해 기본값을 300초로 올리는 것입니다.

## 핵심 변경
- `watcher_core.py`에 `DEFAULT_VERIFY_DONE_DEADLINE_SEC = 300.0`을 추가하고, `WatcherCore`의 `verify_done_deadline_sec` 기본값을 45초에서 300초로 변경했습니다.
- `watcher_core.py` CLI에 `--verify-done-deadline` 플래그를 추가해 watcher 프로세스 실행 시 deadline을 명시적으로 받을 수 있게 했습니다.
- `pipeline_runtime/supervisor.py`가 `.pipeline/config/runtime_policy.json`의 `verify_done_deadline_sec` 값을 읽고 watcher 실행 명령에 `--verify-done-deadline`으로 전달하도록 했습니다.
- `.pipeline/config/runtime_policy.json`에 `"verify_done_deadline_sec": 300`을 추가했습니다.
- watcher 기본값과 supervisor policy 전달 경로를 각각 단위 테스트로 고정했습니다.

## 검증
- 통과: `python3 -m py_compile watcher_core.py pipeline_runtime/supervisor.py tests/test_watcher_core.py tests/test_pipeline_runtime_supervisor.py`
- 통과: `python3 -m unittest tests.test_watcher_core.VerifyCompletionContractTest.test_default_verify_done_deadline_is_300_seconds tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_watcher_shell_command_passes_verify_done_deadline_from_runtime_policy -v`
  - 결과: `Ran 2 tests`, `OK`
- 통과: `python3 -m unittest tests.test_watcher_core -v 2>&1 | tail -5`
  - 결과: `Ran 265 tests in 9.661s`, `OK`
- 통과: `python3 -m unittest tests.test_pipeline_runtime_supervisor -v 2>&1 | tail -5`
  - 결과: `Ran 222 tests in 1.775s`, `OK`
- 통과: `git diff --check -- watcher_core.py pipeline_runtime/supervisor.py .pipeline/config/runtime_policy.json tests/test_watcher_core.py tests/test_pipeline_runtime_supervisor.py`
- 통과: `python3 -m json.tool .pipeline/config/runtime_policy.json >/dev/null`

## 남은 리스크
- 이번 slice는 `TASK_DONE` deadline을 300초로 늘리는 정책 연결입니다. Claude verify lane이 실제로 `TASK_DONE source=wrapper lane=Claude`까지 end-to-end 완료하는지는 다음 자연 verify round에서 확인해야 합니다.
- SIGTERM 시 `finish_stream()` 호출 보장, lane kill 중 `TASK_DONE` 손실 방지는 별도 slice로 남겼습니다.
- dispatch 전 `pane_text_fallback_used lane=Claude` 노이즈는 이번 변경 대상이 아닙니다.
- 기존 untracked `verify/5/22/2026-05-22-live-claude-verify-trigger-3.md`는 이번 slice 범위 밖이라 그대로 두었습니다.
- commit, push, PR 생성, merge는 실행하지 않았습니다.
