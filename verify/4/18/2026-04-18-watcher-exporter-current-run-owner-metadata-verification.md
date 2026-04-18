# 2026-04-18 watcher exporter current run owner metadata verification

## 변경 파일
- `verify/4/18/2026-04-18-watcher-exporter-current-run-owner-metadata-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest `/work`인 `work/4/18/2026-04-18-watcher-exporter-current-run-owner-metadata.md`가 watcher exporter와 supervisor가 같은 `current_run.json` owner contract(`watcher_pid` + `watcher_fingerprint`)를 공유하도록 맞췄다고 주장하므로, 직전 `/verify`가 재현했던 overwrite drift가 현재 트리에서 실제로 닫혔는지 다시 확인해야 했습니다.
- 같은 날 기존 `/verify`인 `verify/4/18/2026-04-18-supervisor-run-id-inheritance-fingerprint-gate-verification.md`는 “supervisor-only truth는 맞지만 watcher exporter overwrite 때문에 end-to-end restart inheritance는 아직 깨진다”는 상태를 닫은 note였으므로, 이번 라운드는 그 exact boundary가 실제로 복구됐는지 확인하는 새 canonical verify note가 필요했습니다.

## 핵심 변경
- latest `/work`의 핵심 구현 주장은 현재 코드와 일치했습니다.
  - `pipeline_runtime/schema.py`의 `process_starttime_fingerprint(pid)`가 `/proc/<pid>/stat` starttime 추출을 shared helper로 들고 있고, `pipeline_runtime/supervisor.py`와 `watcher_core.py`가 둘 다 그 helper를 사용합니다.
  - `watcher_core._write_current_run_pointer()`는 이제 `run_id`, `status_path`, `events_path`와 함께 `watcher_pid = os.getpid()`와 non-empty `watcher_fingerprint`를 같이 기록합니다.
  - `RuntimeSupervisor`는 watcher exporter가 쓴 pointer 뒤에서도 같은 owner contract를 읽어 prior `run_id`를 이어받을 수 있게 됐고, `.pipeline/README.md`도 그 shared contract를 현재 구현 truth로 적고 있습니다.
- latest `/work`가 적은 focused regression과 broad regression도 현재 트리에서 그대로 통과했습니다.
  - watcher exporter current-run metadata regression 1개와 watcher-written pointer 뒤 supervisor restart inheritance regression 1개가 모두 통과했습니다.
  - `tests.test_watcher_core.TransitionTurnTest`는 현재 `Ran 5 tests`, `OK`입니다.
  - `tests.test_pipeline_runtime_supervisor`는 현재 `Ran 82 tests`, `OK`입니다.
  - `tests.test_watcher_core`는 현재 `Ran 126 tests`, `OK`이고, `tests.test_pipeline_runtime_schema`도 `Ran 17 tests`, `OK`입니다.
  - watcher verify replay boundary 1개도 그대로 통과해 current-run owner metadata 추가가 기존 verify replay surface를 깨지 않음을 다시 확인했습니다.
- latest `/work`의 verification prose 중 한 줄은 현재 raw unittest 출력보다 넓게 적혀 있었습니다.
  - `tests.test_watcher_core.TransitionTurnTest` 항목의 `82+회귀` 문구는 현재 raw command 결과(`Ran 5 tests`)와 일치하지 않습니다.
  - 다만 별도 full watcher rerun line(`tests.test_watcher_core`)이 실제로 `Ran 126 tests`, `OK`라서, broad watcher regression evidence 자체가 거짓이었던 것은 아니고 해당 bullet의 서술이 느슨했던 수준입니다.
- docs/plan 문맥도 이번 라운드와 충돌하지 않았습니다.
  - `docs/NEXT_STEPS.md`, `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md`는 pipeline runtime을 여전히 internal/operator family로 두고 있어, 이번 라운드는 shipped browser contract를 넓히지 않는 same-family current-risk reduction으로 남아 있습니다.

## 검증
- `python3 -m py_compile watcher_core.py pipeline_runtime/supervisor.py pipeline_runtime/schema.py tests/test_watcher_core.py tests/test_pipeline_runtime_supervisor.py tests/test_pipeline_runtime_schema.py`
  - 결과: 통과
- `python3 -m unittest -v tests.test_watcher_core.TransitionTurnTest.test_write_current_run_pointer_records_watcher_pid_and_fingerprint tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_supervisor_restart_inherits_run_id_after_watcher_exporter_writes_pointer`
  - 결과: `Ran 2 tests`, `OK`
- `python3 -m unittest -v tests.test_watcher_core.TransitionTurnTest`
  - 결과: `Ran 5 tests`, `OK`
- `python3 -m unittest -v tests.test_pipeline_runtime_supervisor`
  - 결과: `Ran 82 tests`, `OK`
- `python3 -m unittest -v tests.test_pipeline_runtime_schema`
  - 결과: `Ran 17 tests`, `OK`
- `python3 -m unittest -v tests.test_watcher_core`
  - 결과: `Ran 126 tests`, `OK`
- `python3 -m unittest -v tests.test_watcher_core.VerifyCompletionContractTest.test_poll_replays_current_run_verify_pending_even_when_latest_work_is_already_verified`
  - 결과: `Ran 1 test`, `OK`
- `git diff --check -- watcher_core.py pipeline_runtime/supervisor.py pipeline_runtime/schema.py tests/test_watcher_core.py tests/test_pipeline_runtime_supervisor.py .pipeline/README.md`
  - 결과: 통과
- live tmux restart/replay는 이번 verify 라운드에서 다시 돌리지 않았습니다.
  - 이유: 이번 변경은 shared helper + watcher exporter pointer payload + supervisor inheritance helper에 한정되고, focused 2개 + full watcher/supervisor/schema regression이 현재 트리에서 직접 통과했기 때문입니다.

## 남은 리스크
- `process_starttime_fingerprint(pid)`는 아직 `/proc` 기반 Linux 경계에 의존합니다. `/proc`이 없는 환경에서는 fingerprint가 빈 문자열이 되어 inheritance가 항상 fresh `run_id`로 fall through 하는 safe degradation이 남아 있습니다.
- 다음 same-family current-risk reduction은 `pipeline_runtime/schema.process_starttime_fingerprint`에 `/proc`-missing bounded fallback을 추가해 watcher exporter와 supervisor가 shared owner contract를 유지하도록 만드는 것입니다.
- watcher exporter disabled path와 supervisor cold-start 초기 pointer write의 `watcher_pid: 0` / `watcher_fingerprint: ""` 창은 현재 계약상 의도된 동작으로 남아 있지만, 이번 라운드에서 재현된 overwrite drift처럼 active mismatch는 아니었습니다.
