# 2026-04-18 supervisor run_id inheritance fingerprint gate verification

## 변경 파일
- `verify/4/18/2026-04-18-supervisor-run-id-inheritance-fingerprint-gate-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest `/work`인 `work/4/18/2026-04-18-supervisor-run-id-inheritance-fingerprint-gate.md`가 supervisor `run_id` inheritance를 `watcher_pid` 정수 일치뿐 아니라 watcher process fingerprint(`/proc/<pid>/stat` starttime)까지 같을 때만 허용하도록 좁혔다고 주장하므로, 현재 트리에서 그 구현과 검증 결과가 end-to-end로 실제 맞는지 다시 확인해야 했습니다.
- 같은 날 기존 `/verify`인 `verify/4/18/2026-04-18-supervisor-run-id-inheritance-owner-pid-gate-verification.md`는 직전 owner-pid gate 라운드를 닫은 note라서, fingerprint gate까지 포함한 새 canonical verify note가 필요했습니다.

## 핵심 변경
- latest `/work`가 적은 supervisor 쪽 구현 자체는 현재 코드에 들어가 있습니다.
  - `pipeline_runtime/supervisor.py`의 `_inherited_run_id_from_live_watcher()`는 live `experimental.pid`, `current_run.json.watcher_pid`, 그리고 `current_run.json.watcher_fingerprint`가 모두 일치할 때만 prior `run_id`를 이어받습니다.
  - `_watcher_process_fingerprint(pid)`는 `/proc/<pid>/stat`의 starttime(field 22)을 읽고, `_write_current_run_pointer()`는 `watcher_pid`와 `watcher_fingerprint`를 같이 기록합니다.
  - `tests/test_pipeline_runtime_supervisor.py`와 `.pipeline/README.md`에도 이 fingerprint gate 계약이 반영돼 있습니다.
- 하지만 latest `/work`는 현재 shipped truth를 완전히 닫았다고 보기 어렵습니다.
  - `watcher_core.py`의 별도 `_write_current_run_pointer()`는 여전히 `run_id`, `status_path`, `events_path`, `updated_at`만 기록하고 `watcher_pid`/`watcher_fingerprint`를 쓰지 않습니다.
  - 그래서 watcher exporter가 `current_run.json`을 한 번이라도 다시 쓰면, supervisor가 방금 추가한 owner/fingerprint metadata가 파일에서 사라집니다.
  - focused 재현에서 이 drift가 실제로 확인됐습니다. `WatcherCore._transition_turn(...)` 뒤 생성된 `current_run.json`에는 owner/fingerprint 필드가 없었고, 그 상태에서 live `experimental.pid`를 둔 채 `RuntimeSupervisor`를 다시 띄우면 `inherited_same_run: false`로 fresh `run_id`로 떨어졌습니다.
- 따라서 latest `/work`의 “fingerprint gate로 current-run inheritance risk를 닫았다”는 closeout 주장은 부분적으로만 truthful합니다.
  - supervisor 단독 unit fixture에서는 fingerprint gate가 동작하지만, 실제 runtime family에서 같은 `current_run.json`을 공유하는 watcher exporter overwrite path까지 포함한 end-to-end truth는 아직 닫히지 않았습니다.
  - 현재 테스트 8개 + full supervisor regression 81개가 모두 녹색인 이유도, 이 경로를 아직 `watcher_core` writer와 함께 묶어 고정하지 않았기 때문입니다.
- docs/plan 문맥은 이번 라운드와 충돌하지 않았습니다.
  - `docs/NEXT_STEPS.md`, `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md`는 pipeline runtime을 여전히 internal/operator family로 두고 있어, 이번 mismatch도 같은 runtime ownership family 안의 current-risk drift로 남습니다.

## 검증
- `python3 -m py_compile pipeline_runtime/supervisor.py tests/test_pipeline_runtime_supervisor.py`
  - 결과: 통과
- `python3 -m unittest -v tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_supervisor_inherits_run_id_when_watcher_is_alive_so_status_follows_verify_replay tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_supervisor_skips_run_id_inheritance_when_watcher_pid_is_dead tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_supervisor_skips_run_id_inheritance_when_current_run_owner_pid_is_missing tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_supervisor_skips_run_id_inheritance_when_current_run_owner_pid_mismatches_live_watcher tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_supervisor_skips_run_id_inheritance_when_pointer_fingerprint_is_missing tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_supervisor_skips_run_id_inheritance_when_pointer_fingerprint_mismatches_live_watcher tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_supervisor_write_current_run_pointer_records_live_watcher_pid tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_supervisor_write_current_run_pointer_records_live_watcher_fingerprint`
  - 결과: `Ran 8 tests`, `OK`
- `python3 -m unittest -v tests.test_pipeline_runtime_supervisor`
  - 결과: `Ran 81 tests`, `OK`
- `python3 -m unittest -v tests.test_watcher_core.VerifyCompletionContractTest.test_poll_replays_current_run_verify_pending_even_when_latest_work_is_already_verified`
  - 결과: `Ran 1 test`, `OK`
- `python3 - <<'PY'` (watcher exporter current-run payload 재현)
  - 결과: `WatcherCore._transition_turn(...)` 뒤 생성된 `current_run.json` 출력에는 `events_path`, `run_id`, `status_path`, `updated_at`만 있었고 `watcher_pid`/`watcher_fingerprint`가 없었습니다.
- `python3 - <<'PY'` (watcher-written `current_run.json` + live `experimental.pid` 뒤 supervisor restart 재현)
  - 결과: `inherited_same_run: false`; watcher exporter가 bare pointer를 쓴 뒤에는 supervisor가 prior `run_id`를 이어받지 못하고 fresh `run_id`로 떨어졌습니다.
- `git diff --check -- pipeline_runtime/supervisor.py tests/test_pipeline_runtime_supervisor.py .pipeline/README.md`
  - 결과: 통과
- live tmux restart/replay는 이번 verify 라운드에서 다시 돌리지 않았습니다.
  - 이유: current mismatch는 unit fixture 부족이 아니라 `watcher_core.py`의 별도 pointer writer가 owner metadata를 지우는 코드 경로에서 바로 재현됐기 때문입니다.

## 남은 리스크
- active gap은 아직 남아 있습니다. `watcher_core._write_current_run_pointer()`가 bare payload로 `current_run.json`을 덮어쓰는 한, latest `/work`의 fingerprint gate는 supervisor-only truth에 머물고 실제 restart inheritance path는 다시 깨질 수 있습니다.
- 다음 same-family current-risk reduction은 watcher exporter와 supervisor가 같은 `current_run.json` owner contract(`watcher_pid` + `watcher_fingerprint`)를 공유하게 맞추고, watcher-written pointer 뒤 supervisor restart inheritance가 유지되는 cross-boundary regression을 추가하는 것입니다.
- `/proc` 미지원 환경 fallback이나 watcher/self-owned pointer로의 더 큰 ownership 이동은 그 다음 단계에서 검토해도 되지만, 우선은 현재 Linux runtime path에서 방금 재현된 overwrite drift를 먼저 닫는 편이 맞습니다.
