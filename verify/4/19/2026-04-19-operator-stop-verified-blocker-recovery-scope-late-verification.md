# 2026-04-19 operator stop verified-blocker recovery scope late verification

## 변경 파일
- `verify/4/19/2026-04-19-operator-stop-verified-blocker-recovery-scope-late-verification.md`

## 사용 skill
- `round-handoff`: dispatcher가 4/19 `/work`(`work/4/19/2026-04-19-operator-stop-verified-blocker-recovery-scope.md`)를 오늘(2026-04-20) 다시 re-dispatch했으나 matching `/verify` 노트가 존재하지 않던 상태를 감지했습니다. 4/19 verify 폴더에는 해당 scope의 verification 노트가 없고, dispatcher가 가리킨 `verify/4/19/2026-04-19-response-body-conflict-header-verification.md`는 seq 408 CONFLICT response-body 라운드 전용이라 family mismatch였습니다. 이번 라운드에서 4/19 scope 전용 late-verify 노트를 신규로 추가해 shipped truth를 캡처하고, 현재 in-flight 축(Milestone 4 E2b retriage seq 434 gemini_request)과 축 분리를 명시합니다.

## 변경 이유
- 4/19 `/work`는 `verified_blockers_resolved` self-heal 범위를 `truth_sync_required` family에만 허용하도록 좁히는 watcher/supervisor 공유 helper(`allows_verified_blocker_auto_recovery`)와 관련 회귀를 shipped 했다고 주장합니다. dispatcher가 이 `/work`를 today 재-dispatch하면서 matching verify 노트가 비어 있어, late-verify를 채워야 future dispatcher가 같은 SHA를 stale로 오인하거나 중복 구현을 시도하지 않습니다.
- 동시에, 오늘(2026-04-20) 실제 활성 축은 Milestone 4 E2b arbitration(`.pipeline/gemini_request.md` seq 434, `advice_truth_sync_gap` retriage 결과)입니다. seq 424 `dispatcher_state_truth_sync` 선례에 따라 older `/work` re-dispatch는 in-flight newer 축을 overwrite하지 않고, 이 late-verify는 informational로 남겨 둡니다.

## 핵심 변경
- 4/19 `/work`의 구현 주장은 현재 tree와 일치합니다.
  - `pipeline_runtime/operator_autonomy.py:168` `allows_verified_blocker_auto_recovery(control_meta: Mapping[str, Any] | None = None) -> bool` 존재 확인.
  - `watcher_core.py:62` 에서 import, `:2041` 에서 `if not allows_verified_blocker_auto_recovery(control_meta): ...` 사용 확인. stale operator control marker가 해당 helper가 허용한 경우에만 `BASED_ON_WORK -> VERIFY_DONE` stale recovery를 적용합니다.
  - `pipeline_runtime/supervisor.py:22` 에서 import, `:434` 에서 같은 guard 사용 확인. runtime status/event surface가 watcher와 동일한 stale 기준을 공유합니다.
  - `tests/test_watcher_core.py:3035` `test_slice_ambiguity_operator_request_with_verified_work_stays_gated` 존재 및 통과 확인.
  - `tests/test_pipeline_runtime_supervisor.py:2611` `test_write_status_keeps_slice_ambiguity_operator_stop_gated_when_based_work_is_verified` 존재 및 통과 확인.
  - `.pipeline/README.md:172` 에 "`BASED_ON_WORK`가 이미 `VERIFY_DONE`라고 해서 모든 `needs_operator`를 stale stop으로 되돌리면 안 됩니다. `verified_blockers_resolved` self-heal은 … `truth_sync_required`처럼 … family에만 적용하고, `slice_ambiguity`나 다른 next-slice/operator-selection stop은 같은 `BASED_ON_WORK`를 갖더라도 gate/publish 계약을 그대로 유지하는 편이 맞습니다." 문장 존재 확인.
- `.pipeline` rolling slot snapshot
  - `.pipeline/claude_handoff.md`: STATUS `implement`, CONTROL_SEQ `430` — seq 430 Milestone 4 E3 wording polish shipped 후 새 handoff 미발행. 다음 implement 축은 seq 434 gemini_request 응답 후 결정될 예정.
  - `.pipeline/gemini_request.md`: STATUS `request_open`, CONTROL_SEQ `434` — Milestone 4 E2b refined arbitration(α/β/γ/G) 요청. Gemini advice 432의 label-set widening / trusted-role 정의 / multi-source metric 세 gap을 refine. in-flight.
  - `.pipeline/gemini_advice.md`: STATUS `advice_ready`, CONTROL_SEQ `432` — seq 434 gemini_request에 의해 refine 대기.
  - `.pipeline/operator_request.md`: STATUS `needs_operator`, CONTROL_SEQ `433` — `advice_truth_sync_gap`로 올렸다가 retriage로 seq 434 gemini_request로 변환. 이번 라운드에서 dispatcher_state_truth_sync 신규 operator_request(seq 435)로 대체 예정.

## 검증
- 직접 코드/테스트 대조
  - `pipeline_runtime/operator_autonomy.py:168`, `watcher_core.py:62`/`:2041`, `pipeline_runtime/supervisor.py:22`/`:434`, `tests/test_watcher_core.py:3035`, `tests/test_pipeline_runtime_supervisor.py:2611`, `.pipeline/README.md:172` 실제 위치 확인.
- `python3 -m py_compile pipeline_runtime/operator_autonomy.py watcher_core.py pipeline_runtime/supervisor.py tests/test_watcher_core.py tests/test_pipeline_runtime_supervisor.py`
  - 결과: `PYCOMPILE_OK`
- `python3 -m unittest -v tests.test_watcher_core.TurnResolutionTest.test_slice_ambiguity_operator_request_with_verified_work_stays_gated tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_status_keeps_slice_ambiguity_operator_stop_gated_when_based_work_is_verified`
  - 결과: `Ran 2 tests in 0.029s`, `OK`. 두 신규 회귀 모두 green.
- `python3 -m unittest tests.test_watcher_core`
  - 결과: `Ran 138 tests in 8.120s`, `OK`. `/work` 기록의 131건에서 7건 추가(이후 라운드에서 watcher 테스트가 더 늘어난 것으로 추정), 실패 없음.
- `git diff --check -- pipeline_runtime/operator_autonomy.py watcher_core.py pipeline_runtime/supervisor.py tests/test_watcher_core.py tests/test_pipeline_runtime_supervisor.py .pipeline/README.md`
  - 결과: 출력 없음, `DIFFCHECK_OK`.
- 이번 late verify에서 재실행하지 않은 것과 그 이유
  - `tests.test_pipeline_runtime_supervisor` 전체 스위트: dirty-state 기반 실패 family(`TestRuntimeStatusRead`)가 이 slice 밖으로 분리되어 있고, `/work`가 pin한 두 신규 회귀는 좁게 직접 재실행해 green을 확인했습니다.
  - Playwright, `make e2e-test`: 4/19 scope은 watcher/supervisor 런타임 경계 변경이라 browser-visible contract를 건드리지 않았습니다.

## 남은 리스크
- **Dispatcher 재-dispatch 드리프트**: today(2026-04-20) dispatcher가 4/19 `/work` + mismatched 4/19 verify를 가리키며 verify 라운드를 요청했습니다. 4/19 scope은 이미 shipped이고 새 implementation이 필요 없으므로, 이번 late verify는 informational입니다. in-flight 활성 축은 `.pipeline/gemini_request.md` seq 434 Milestone 4 E2b refined arbitration이며, 같은 사이클에 `operator_request` seq 435를 `dispatcher_state_truth_sync`로 올려 operator가 축 continuity를 선택하도록 합니다. seq 424의 `dispatcher_state_truth_sync` 선례와 동일한 패턴입니다.
- **Live tmux/runtime 반영**: `/work`가 지적했듯 live watcher/supervisor 프로세스는 이번 patch를 자동으로 pick up하지 않습니다. operator가 필요 시점에 수동으로 재시작해야 합니다. 이번 verify는 shipped code 정합성만 확인했을 뿐 live process behavior를 확인하지는 않았습니다.
- **REASON_CODE vocabulary canonicalization 미강제**: Codex가 `needs_operator`를 작성할 때 canonical `REASON_CODE`/`OPERATOR_POLICY` 사용이 항상 강제되는 것은 아닙니다. 이번 helper는 canonical 값을 가정하는 classification에만 관여하므로, vocabulary drift가 발생하면 `allows_verified_blocker_auto_recovery`의 분류도 추적 가능성을 잃을 수 있습니다. 별도 슬라이스 후보.
- **Milestone 4 축 상태**: E1(seq 427), E3(seq 430) shipped. E2 refined arbitration(α/β/γ/G)은 seq 434 gemini_request에서 Gemini 응답 대기 중. 오늘(2026-04-20) docs-only round count는 계속 0이며 same-day same-family docs-only 3+ guard에 걸리지 않았습니다.
- unrelated 전체 `python3 -m unittest tests.test_web_app` 실패 family, `tests.test_pipeline_gui_backend::TestRuntimeStatusRead` dirty-state 실패는 이번 slice와 축이 달라 그대로 남아 있습니다.
