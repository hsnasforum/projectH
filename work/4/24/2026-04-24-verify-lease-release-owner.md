# 2026-04-24 verify lease release owner 정리

## 변경 파일
- `verify_fsm.py`
- `watcher_core.py`
- `tests/test_verify_fsm.py`
- `tests/test_watcher_core.py`
- `work/4/24/2026-04-24-verify-lease-release-owner.md`

## 사용 skill
- `finalize-lite`: handoff 범위, 실행 검증, doc-sync 필요 여부, `/work` closeout 준비 상태를 확인했습니다.
- `work-log-closeout`: 실제 변경 파일, 실행 검증, 남은 리스크를 한국어 `/work` 기록으로 남겼습니다.

## 변경 이유
- M28 Axis 2 handoff는 archive-matching `VERIFY_PENDING` 처리 중 `watcher_core.py`가 `slot_verify` lease release를 직접 수행하는 bypass를 제거하라고 지시했습니다.
- lease release write/transition 경로를 `StateMachine` 쪽으로 모아, watcher는 archive 판단과 라우팅만 맡고 release owner는 FSM으로 유지하도록 했습니다.

## 핵심 변경
- `StateMachine.release_verify_lease_for_archive(job)`를 추가해 archive-matching pending 경로의 `slot_verify` release를 FSM 위임 메서드로 노출했습니다.
- `WatcherCore._archive_matching_verified_pending_jobs()`에서 `self.lease.release("slot_verify")` 직접 호출을 제거하고 `self.sm.release_verify_lease_for_archive(job)`로 교체했습니다.
- `tests/test_verify_fsm.py`에 archive release 위임이 `archive_matching_verified_pending` reason으로 lease release event를 남기는 검증을 추가했습니다.
- `tests/test_watcher_core.py`에 archive-matching `VERIFY_PENDING` replay를 추가해 FSM 위임 메서드 호출을 확인하고, watcher direct `lease.release()`는 `AssertionError`로 차단되도록 고정했습니다.
- handoff가 제외한 `watcher_core.py:4082`의 `lease.is_active("slot_verify")` read-only query와 Axis 3 영역은 건드리지 않았습니다.

## 검증
- `rg -n 'self\\.lease\\.release\\("slot_verify"\\)' watcher_core.py || true`
  - 통과: 출력 없음
- `python3 -m py_compile verify_fsm.py watcher_core.py`
  - 통과: 출력 없음
- `python3 -m unittest tests.test_verify_fsm tests.test_watcher_core`
  - 통과: `Ran 210 tests in 9.117s`, `OK`
- `git diff --check`
  - 통과: 출력 없음

## 남은 리스크
- 전체 unittest suite는 이번 handoff acceptance에 포함되지 않아 재실행하지 않았습니다. 직전 Axis 1 closeout 기준으로 sandbox의 localhost socket 제한과 order-dependent GUI 단일 실패가 남아 있었습니다.
- 작업트리에는 이번 handoff 범위 밖의 기존 dirty files가 계속 남아 있습니다: `pipeline_runtime/cli.py`, `pipeline_runtime/operator_autonomy.py`, `pipeline_runtime/supervisor.py`, `pipeline_runtime/turn_arbitration.py`, `scripts/pipeline_runtime_gate.py`, 관련 테스트 및 report/verify/work 파일들입니다. 이번 round에서는 해당 파일들을 수정하거나 되돌리지 않았습니다.
- `.pipeline/advisory_request.md`, `.pipeline/operator_request.md`, commit/push/PR은 건드리지 않았습니다.
