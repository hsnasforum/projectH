# 2026-05-20 stale operator retriage dispatch guard

## 변경 파일

- `watcher_dispatch.py`
- `tests/test_watcher_core.py`
- `.pipeline/README.md`
- `docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md`
- `work/5/20/2026-05-20-stale-operator-retriage-dispatch-guard.md`
- `verify/5/20/2026-05-20-stale-operator-retriage-dispatch-guard.md`

## 사용 skill

- `security-gate`: operator stop, pane dispatch, stale prompt 재주입 경계를 다루는 변경이라 승인/중지 안전 경계를 확인했습니다.
- `doc-sync`: 런타임 dispatch 계약이 바뀌었으므로 `.pipeline/README.md`와 운영 runbook의 pending/control-resolution 설명을 맞췄습니다.
- `release-check`: handoff 전 실제 실행한 테스트, 문서 동기화, 남은 리스크를 분리해 확인했습니다.
- `work-log-closeout`: 이번 구현 라운드의 변경 파일, 검증, 남은 리스크를 한국어 `/work` 기록으로 남기기 위해 사용했습니다.

## 변경 이유

- 사용자가 확인한 반복 동작은 `.pipeline/operator_request.md#2031 safety_stop`이 active가 된 뒤에도, 직전 `#2030 verify_operator_retriage` prompt가 Codex pane에 다시 붙여넣기될 수 있는 경로 때문에 발생할 수 있었습니다.
- `verify_operator_retriage` 같은 control-resolution prompt는 `require_active_control=false`라서, dispatch 직전 active control mismatch guard가 적용되지 않았습니다.
- 같은 `.pipeline/operator_request.md` 경로를 가리키더라도 `expected_control_seq=2030`보다 높은 `CONTROL_SEQ: 2031` safety stop이 들어오면 오래된 prompt는 폐기되어야 합니다.

## 핵심 변경

- `WatcherDispatchQueue.dispatch()`에서 pending flush가 아닌 즉시 dispatch도 active control mismatch를 먼저 검사하도록 했습니다.
- `_drop_dispatch_if_active_control_mismatch()`를 추가해 `expected_control_path`, `expected_control_slot`, `expected_control_seq`가 있는 prompt를 현재 active control과 대조하고, drift가 있으면 `lane_input_deferred_dropped` 이벤트와 함께 폐기합니다.
- `active_control_missing`은 기존 strict active-control prompt와 relaxed control-resolution prompt를 구분해, relaxed prompt가 불필요하게 drop되지 않도록 처리했습니다.
- `#2030 verify_operator_retriage`가 `#2031 safety_stop + immediate_publish` 이후 drop되는 단위 테스트와 rolling signal 테스트를 추가했습니다.
- runtime 문서에 `require_active_control=false`인 control-resolution prompt도 dispatch 직전 `expected_control_seq`를 재검사해야 한다는 계약을 남겼습니다.

## 검증

- `python3 -m unittest -v tests.test_watcher_core.WatcherDispatchQueueControlMismatchTest.test_stale_operator_retriage_dispatch_drops_after_new_safety_stop tests.test_watcher_core.RollingSignalTransitionTest.test_safety_stop_drops_pending_operator_retriage_and_blocks_dispatch`
  - 결과: PASS. 2 tests OK.
- `python3 -m py_compile watcher_dispatch.py tests/test_watcher_core.py`
  - 결과: PASS. 출력 없음.
- `git diff --check -- watcher_dispatch.py tests/test_watcher_core.py .pipeline/README.md docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md`
  - 결과: PASS. 출력 없음.
- `python3 -m pipeline_runtime.cli status . --json`
  - 결과: active control은 `.pipeline/operator_request.md#2031`입니다.
  - 결과: `turn_state=OPERATOR_WAIT`, `automation_health=needs_operator`, `automation_reason_code=safety_stop`, `automation_next_action=operator_required`입니다.

## 남은 리스크

- watcher는 현재 status 기준 `alive=false`라서, 이번 source guard는 watcher가 다음에 같은 코드로 실행될 때 적용됩니다.
- Codex pane에는 이전 prompt text가 화면에 남아 있을 수 있지만, active control truth는 #2031 operator wait입니다.
- 전체 `tests/test_watcher_core.py`, broad unit, Playwright/e2e, long soak는 실행하지 않았습니다. 이번 변경은 watcher dispatch guard와 runtime 문서에 한정했기 때문입니다.
- 작업 트리는 기존 자동화 라운드의 많은 변경과 untracked `/work`/`/verify` 기록을 포함하고 있어 clean 상태가 아닙니다.
