STATUS: verified
CONTROL_SEQ: 118
BASED_ON_WORK: work/4/24/2026-04-24-verify-lease-release-owner.md
VERIFIED_BY: Claude
NEXT_CONTROL: .pipeline/advisory_request.md CONTROL_SEQ 119 (M28 Axis 3 scoping)

---

## M28 Axis 2 — Lease Release Single-Owner

### Verdict

PASS. `verify_fsm.py` + `watcher_core.py` 변경이 `/work` 기술과 일치하고, 재검증 통과.

### Checks Rerun

- `rg -n 'self\.lease\.release\("slot_verify"\)' watcher_core.py` → 출력 없음 (직접 호출 제거 확인)
- `python3 -m py_compile verify_fsm.py watcher_core.py` → OK
- `python3 -m unittest tests.test_verify_fsm tests.test_watcher_core` → `Ran 210 tests in 9.285s`, OK
- `git diff --check` → OK (출력 없음)

### Implementation Confirmed

- `verify_fsm.StateMachine.release_verify_lease_for_archive()` 신규 메서드 확인 (verify_fsm.py:291)
- `watcher_core.WatcherCore._archive_matching_verified_pending_jobs()`: `self.lease.release("slot_verify")` 직접 호출 제거 + `self.sm.release_verify_lease_for_archive(job)` 위임 확인 (watcher_core.py:3514)
- `tests/test_verify_fsm.py:145`: `release_verify_lease_for_archive`가 `archive_matching_verified_pending` reason으로 lease release event를 남기는 검증 확인
- `tests/test_watcher_core.py:7995`: `core.lease.release` 직접 호출 AssertionError 차단 + `sm.release_verify_lease_for_archive` 단독 경로 검증 확인 (line 8044: `fsm_release_mock.assert_called_once()`, line 8047: `direct_release_mock.assert_not_called()`)

### What Was Checked

- 직접 `lease.release("slot_verify")` bypass 완전 제거 grep 확인
- py_compile, 210-test suite (test_verify_fsm + test_watcher_core), git diff --check 재실행
- verify_fsm.py / watcher_core.py / test_watcher_core.py 코드 직접 확인

### What Was Not Checked

- 전체 `python3 -m unittest discover -s tests` 미실행: Axis 1 closeout 기준 pre-existing sandbox socket 오류(36개) + GUI order-dependent 실패(1개)가 Axis 2 변경과 무관함. Axis 2 변경 파일(verify_fsm.py, watcher_core.py)은 해당 계열과 연결 없음.
- browser/e2e 미실행: runtime-only 변경, browser contract 미변경.

### Out-of-Scope Dirty Worktree

이번 Axis 2 검증 범위 밖의 pending files는 선행 `/work` + `/verify` 노트로 이미 커버됨:
- `pipeline_runtime/cli.py`, `scripts/pipeline_runtime_gate.py` → `work/4/24/2026-04-24-large-automation-verification.md`
- `pipeline_runtime/supervisor.py`, `pipeline_runtime/turn_arbitration.py` → `work/4/24/2026-04-24-hibernate-stale-working-surface.md`
- `pipeline_runtime/operator_autonomy.py` → 위 라운드들의 연관 파일

### Residual Risk

- `watcher_core.py:4082`의 `self.lease.is_active("slot_verify")` read-only query는 Axis 2 범위 밖(write/transition owner 원칙 대상 아님). 현 상태 유지.
- M28 Axis 3 (active_round selection) 스코프는 advisory에서 결정 예정. `_build_active_round()`는 dict 상태를 읽어 display struct를 만드는 read surface로, Axes 1-2의 write/transition bypass 패턴과 다른 아키텍처적 판단이 필요.
