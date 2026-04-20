# 2026-04-19 operator stop verified-blocker recovery scope

## 변경 파일
- `pipeline_runtime/operator_autonomy.py`
- `watcher_core.py`
- `pipeline_runtime/supervisor.py`
- `tests/test_watcher_core.py`
- `tests/test_pipeline_runtime_supervisor.py`
- `.pipeline/README.md`
- `work/4/19/2026-04-19-operator-stop-verified-blocker-recovery-scope.md`

## 사용 skill
- `doc-sync`: operator stop stale-recovery 계약 변경을 `.pipeline/README.md`와 코드 truth에 맞춰 좁게 동기화하기 위해 사용했습니다.
- `work-log-closeout`: 이번 watcher/supervisor 회귀 방지 라운드의 `/work` closeout을 repo 규약 형식으로 남기기 위해 사용했습니다.

## 변경 이유
- live Codex pane에서 Gemini follow-up 직후 `needs_operator` stop을 쓴 다음, watcher가 그 stop을 stale control로 즉시 무효화해 Codex prompt를 한 번 더 paste하는 흐름이 재현됐습니다.
- 원인은 `BASED_ON_WORK`가 이미 `VERIFY_DONE`인 경우 `needs_operator` 전체를 `verified_blockers_resolved`로 취급하던 공통 가정이었습니다. 이 규칙은 truth-sync blocker에는 맞지만, `slice_ambiguity` 같은 next-slice/operator-selection stop까지 stale로 되돌려 버렸습니다.
- watcher와 supervisor가 같은 stale 기준을 공유하지 않으면 pane dispatch와 status surface가 다시 어긋나므로, 이번 라운드는 stale auto-recovery eligibility를 shared helper로 좁히는 데 집중했습니다.

## 핵심 변경
- `pipeline_runtime/operator_autonomy.py`에 `allows_verified_blocker_auto_recovery(...)` helper를 추가해, `verified_blockers_resolved` self-heal을 명시적 `truth_sync_required` family에만 허용하도록 고정했습니다.
- `watcher_core.py::_stale_operator_control_marker()`는 이제 위 helper가 허용한 operator stop에만 `BASED_ON_WORK -> VERIFY_DONE` stale recovery를 적용합니다. `slice_ambiguity` 같은 next-slice stop은 같은 `BASED_ON_WORK`가 있어도 gated/published contract를 유지합니다.
- `pipeline_runtime/supervisor.py::_stale_operator_control_marker()`도 같은 helper를 사용하도록 맞춰, runtime status/event surface가 watcher와 동일한 stale 기준을 따르게 했습니다.
- `tests/test_watcher_core.py`에 `slice_ambiguity + verified work` 조합이 `control_recovery`가 아니라 gated Codex follow-up으로 남는 회귀 테스트를 추가했습니다.
- `tests/test_pipeline_runtime_supervisor.py`에 같은 조합이 `control_operator_stale_ignored`가 아니라 `control_operator_gated`로 surface되는 테스트를 추가했습니다.
- `.pipeline/README.md`에 "`BASED_ON_WORK`가 VERIFY_DONE이라고 해서 모든 `needs_operator`를 stale stop으로 되돌리면 안 된다"는 계약을 명시했습니다.

## 검증
- `python3 -m py_compile pipeline_runtime/operator_autonomy.py watcher_core.py pipeline_runtime/supervisor.py tests/test_watcher_core.py tests/test_pipeline_runtime_supervisor.py`
  - 결과: 통과
- `python3 -m unittest -v tests.test_watcher_core.TurnResolutionTest.test_slice_ambiguity_operator_request_with_verified_work_stays_gated`
  - 결과: `Ran 1 test`, `OK`
- `python3 -m unittest -v tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_status_keeps_slice_ambiguity_operator_stop_gated_when_based_work_is_verified`
  - 결과: `Ran 1 test`, `OK`
- `python3 -m unittest -v tests.test_watcher_core.TurnResolutionTest.test_stale_operator_request_resolves_to_codex_followup tests.test_watcher_core.RollingSignalTransitionTest.test_stale_operator_request_update_routes_to_codex_control_recovery tests.test_watcher_core.RollingSignalTransitionTest.test_startup_turn_uses_codex_control_recovery_for_stale_operator_request`
  - 결과: `Ran 3 tests`, `OK`
- `python3 -m unittest -v tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_status_gates_slice_ambiguity_operator_stop_for_24h tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_status_keeps_truth_sync_operator_stop_active`
  - 결과: `Ran 2 tests`, `OK`
- `python3 -m unittest tests.test_watcher_core`
  - 결과: `Ran 131 tests`, `OK`
- `git diff --check -- pipeline_runtime/operator_autonomy.py watcher_core.py pipeline_runtime/supervisor.py tests/test_watcher_core.py tests/test_pipeline_runtime_supervisor.py .pipeline/README.md`
  - 결과: 출력 없음

## 남은 리스크
- 현재 live tmux/runtime 프로세스는 이미 떠 있는 코드로 동작 중이라, 이번 patch를 실제 pane behavior에 반영하려면 watcher/supervisor 재시작이 별도로 필요합니다.
- 이번 라운드는 `verified work -> stale operator auto-recovery` 범위를 줄인 것입니다. `needs_operator`를 왜 썼는지의 vocabulary 자체(`REASON_CODE`, `OPERATOR_POLICY`)를 Codex가 항상 canonical 값으로 쓰게 강제한 것은 아닙니다.
- `pipeline_runtime/supervisor.py`, `tests/test_pipeline_runtime_supervisor.py`, `.pipeline/README.md`에는 이번 라운드 이전부터 쌓여 있던 다른 dirty hunk가 같이 존재합니다. 이번 라운드 직접 기여는 stale-recovery scope 축에 한정되므로, 커밋/리뷰 시에는 이 closeout 기준으로 분리해서 보는 편이 안전합니다.
