# 2026-04-22 verify lease release consolidation

## 변경 파일
- `verify_fsm.py`
- `watcher_core.py`
- `tests/test_verify_fsm.py`
- `work/4/22/2026-04-22-verify-lease-release-consolidation.md`

## 사용 skill
- `security-gate`: verify FSM lease release와 runtime log JSONL 기록 경로를 바꾸는 작업이라 local-first runtime control, audit/log, stop-slot 경계를 확인했습니다.
- `finalize-lite`: 구현 종료 전 요구 검증 통과 여부, 문서 동기화 필요 여부, `/work` closeout 준비 상태를 좁게 점검했습니다.
- `work-log-closeout`: 실제 변경 파일, 실행 명령, 남은 리스크를 기준으로 이 closeout을 작성했습니다.

## 변경 이유
- `.pipeline/implement_handoff.md` CONTROL_SEQ 750의 `lease_release_consolidation` handoff를 완료하기 위해서입니다.
- `verify_fsm.py`의 여러 `self.lease.release(...)` 호출을 하나의 `_release_verify_lease()` 경계로 모아 release 이유를 JSONL로 관찰 가능하게 만들기 위해서입니다.

## 핵심 변경
- `verify_fsm.py`의 `StateMachine`에 `_release_verify_lease(slot, job=None, reason="")` helper를 추가했습니다.
- `verify_fsm.py` 안의 direct `self.lease.release(...)` 8개 호출을 모두 `_release_verify_lease(...)`로 교체하고, 각 호출에 `dispatch_dry_run`, `dispatch_failed`, `startup_recovery`, `feedback_verify_complete` 등 전환 이유를 부여했습니다.
- `_release_verify_lease()`는 기존 lease interface를 그대로 호출하고, reason이 있을 때만 `append_jsonl()`로 `lease_released` event를 `error_log`에 기록합니다.
- `watcher_core.py`의 `_archive_matching_verified_pending_jobs()`에 남는 예외적인 direct release 앞에는 `archive_matching_verified_pending` 이유가 보이도록 명시 로그를 추가했습니다.
- `tests/test_verify_fsm.py`에 helper가 lease release를 호출하는지와 reason 포함 JSONL event를 쓰는지 검증하는 테스트 2개를 추가했습니다.

## 검증
- `python3 -m py_compile verify_fsm.py watcher_core.py` 통과
- `python3 -m unittest tests.test_verify_fsm` 통과 (`5 tests`)
- `python3 -m unittest tests.test_watcher_core` 통과 (`191 tests`)
- `git diff --check` 통과

## 남은 리스크
- 이번 slice는 handoff 제약에 따라 `pipeline_runtime/schema.py`, `pipeline_runtime/supervisor.py`, `lane_surface.py`, `pipeline_gui/`, `app/`, `core/`, `storage/`를 건드리지 않았습니다.
- `watcher_core.py`의 release는 handoff 지시대로 새 helper 계층을 만들지 않고 local log만 추가했습니다.
- `verify_fsm.py`, `watcher_core.py`, `tests/test_verify_fsm.py`는 이전 CONTROL_SEQ 747/742 구현 변경이 이미 dirty 상태인 파일 위에 이번 변경을 더했습니다. 이전 dirty 항목은 되돌리지 않았습니다.
- 최종 status에는 이번 라운드 이전부터 존재하던 `pipeline_gui/backend.py`, `pipeline_runtime/schema.py`, `pipeline_runtime/supervisor.py`, `tests/test_pipeline_runtime_schema.py`, `verify/4/22/2026-04-22-role-harness-pipeline-automation-handoff-verification.md`, `report/gemini/2026-04-22-axis2-or-resume.md`, `report/gemini/2026-04-22-axis3-scoping.md`, `report/gemini/2026-04-22-post-cleanup-next-slice.md`, `verify/4/22/2026-04-22-post-cleanup-launcher-automation-realignment.md`, `work/4/22/2026-04-22-active-control-snapshot.md`, `work/4/22/2026-04-22-pipeline-control-shared-snapshot.md`, `work/4/22/2026-04-22-runtime-legacy-control-cleanup-closeout.md`, `work/4/22/2026-04-22-verify-close-chain-snapshot.md`가 별도 dirty 또는 untracked 항목으로 남아 있습니다. 이번 handoff에서는 해당 파일들을 정리하지 않았습니다.
