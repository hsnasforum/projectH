STATUS: verified
WORK: work/5/20/2026-05-20-stale-operator-retriage-dispatch-guard.md
CONTROL_SEQ: 2031

# 검증 기록

## 요약

`watcher_dispatch.py`의 새 guard는 더 높은 `CONTROL_SEQ`의
`safety_stop + immediate_publish` operator stop이 active가 된 뒤, 같은
`.pipeline/operator_request.md` 경로를 가리키는 오래된
`verify_operator_retriage` prompt를 `control_seq_drift`로 drop하도록
검증됐습니다.

## 변경 파일

- `watcher_dispatch.py`
- `tests/test_watcher_core.py`
- `.pipeline/README.md`
- `docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md`
- `work/5/20/2026-05-20-stale-operator-retriage-dispatch-guard.md`
- `verify/5/20/2026-05-20-stale-operator-retriage-dispatch-guard.md`

## 확인한 대상

- `WatcherDispatchQueue.dispatch()`
- `WatcherDispatchQueue._drop_dispatch_if_active_control_mismatch()`
- `WatcherDispatchQueueControlMismatchTest.test_stale_operator_retriage_dispatch_drops_after_new_safety_stop`
- `RollingSignalTransitionTest.test_safety_stop_drops_pending_operator_retriage_and_blocks_dispatch`
- `.pipeline/README.md`
- `docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md`
- `python3 -m pipeline_runtime.cli status . --json` output

## 실행한 검증

- `python3 -m unittest -v tests.test_watcher_core.WatcherDispatchQueueControlMismatchTest.test_stale_operator_retriage_dispatch_drops_after_new_safety_stop tests.test_watcher_core.RollingSignalTransitionTest.test_safety_stop_drops_pending_operator_retriage_and_blocks_dispatch`
  - 결과: PASS. 2 tests OK.
- `python3 -m py_compile watcher_dispatch.py tests/test_watcher_core.py`
  - 결과: PASS. 출력 없음.
- `git diff --check -- watcher_dispatch.py tests/test_watcher_core.py .pipeline/README.md docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md`
  - 결과: PASS. 출력 없음.
- `python3 -m pipeline_runtime.cli status . --json`
  - 결과: active control은 `.pipeline/operator_request.md#2031`입니다.
  - 결과: `turn_state=OPERATOR_WAIT`, `automation_health=needs_operator`,
    `automation_reason_code=safety_stop`, `automation_next_action=operator_required`입니다.
  - 결과: watcher는 `alive=false`, Codex lane은 `READY` / `prompt_visible`입니다.

## 실행하지 않은 검증

- 전체 `tests/test_watcher_core.py`
  - 이유: 현재 파일에는 이전 자동화 라운드의 광범위한 변경이 섞여 있어, 이번 문제 재현 경로에 직접 닿는 두 테스트를 우선했습니다.
- Playwright/e2e
  - 이유: browser-visible product behavior를 바꾸지 않았습니다.
- long soak 또는 runtime restart
  - 이유: 현재 목표는 #2031 operator stop 유지와 stale dispatch guard의 단위/rolling 재현 검증입니다.

## 판정

- 이번 문제의 코드 경로는 재현 테스트로 닫혔습니다.
- active runtime truth는 여전히 `#2031 safety_stop` operator wait입니다.
- watcher process는 현재 살아 있지 않으므로, source 변경은 다음 watcher 실행부터 적용됩니다.

## 남은 리스크

- 작업 트리는 기존 dirty bundle과 untracked work/verify 기록을 포함합니다.
- 이미 화면에 붙은 과거 prompt text는 source guard가 지우지 않습니다. 다만 새 dispatch 시점에는 `expected_control_seq` drift가 있는 prompt를 drop해야 합니다.
