# 2026-05-08 M121 watcher lease reclamation

## 변경 파일

- `watcher_state.py`
- `pipeline_runtime/supervisor.py`
- `tests/test_watcher_core.py`
- `work/5/8/2026-05-08-m121-watcher-lease-reclamation.md`

## 사용 skill

- `security-gate`: watcher self-restart 중 lock 파일을 archive로 이동하는 write-capable runtime control 변경의 경계와 로그/복구 성격을 점검했다.
- `work-log-closeout`: 구현 라운드 종료 기록 형식과 실제 검증 사실 정리에 사용했다.

## 변경 이유

- watcher self-restart 시 이전 watcher가 남긴 supervisor-owned active lease가 supervisor PID 생존 때문에 owner-dead로 정리되지 않고 TTL 만료까지 새 watcher dispatch를 막는 구조적 문제를 줄이기 위해 변경했다.
- TTL 값이나 `_terminate_pid_file()` 동작은 바꾸지 않고, self-restart 직전에 기존 lock을 보존 이동해 새 watcher가 즉시 acquire할 수 있게 했다.

## 핵심 변경

- `PaneLease.archive_for_restart()`를 추가해 slot lock이 있으면 `locks/archive/<slot>.lock.stale-<timestamp>`로 보존 이동하고, lock이 없으면 no-op `True`를 반환하게 했다.
- archive 디렉터리 생성 또는 rename 실패 시 `False`를 반환하고 경고 로그를 남기게 했다.
- `RuntimeSupervisor._maybe_restart_watcher_for_source_change()`에서 `experimental.pid` 종료 전에 `slot_verify`, `slot_implement`, `slot_advisory`, `slot_followup` lock을 archive하도록 연결했다.
- `PaneLeaseOwnerPidWiringTest`에 active lease 보존 이동, lock 없음 no-op, archive 후 TTL 이전 acquire 성공 회귀 테스트를 추가했다.
- security-gate 관점: 변경은 로컬 `.pipeline/locks` 내부 파일 이동만 수행하며 외부 네트워크, 승인 payload, 사용자 문서 저장 흐름을 건드리지 않는다. 기존 lock은 삭제가 아니라 archive에 보존되므로 감사/복구 단서가 남는다.

## 검증

- `python3 -m py_compile watcher_state.py pipeline_runtime/supervisor.py`
  - PASS.
- `python3 -m unittest -v tests.test_watcher_core.PaneLeaseOwnerPidWiringTest`
  - PASS: 10개 테스트 통과.
- `python3 -m unittest -v tests.test_watcher_core.PaneLeaseOwnerPidWiringTest.test_archive_for_restart_moves_active_lease_to_archive tests.test_watcher_core.PaneLeaseOwnerPidWiringTest.test_archive_for_restart_returns_true_when_no_lease_exists tests.test_watcher_core.PaneLeaseOwnerPidWiringTest.test_watcher_acquire_succeeds_after_archive_for_restart`
  - PASS: 신규 3개 테스트 직접 실행.
- `git diff --check -- watcher_state.py pipeline_runtime/supervisor.py tests/test_watcher_core.py`
  - PASS.

## 남은 리스크

- archive 실패 시 supervisor self-restart 자체는 계속 진행되며, 실패 원인은 warning log로 남는다. 이 경우 해당 lock은 TTL 만료까지 남을 수 있다.
- live watcher self-restart 시나리오는 직접 실행하지 않았고, 회귀 테스트는 `PaneLease` 단위 동작과 acquire 재시도 경로에 집중했다.
- `watcher_dispatch.py`, `watcher_core.py`, TTL 값, product UI / preference 파일은 handoff 금지 범위라 수정하지 않았다.
