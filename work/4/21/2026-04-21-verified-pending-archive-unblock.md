# 2026-04-21 verified pending archive unblock

## 변경 파일
- `watcher_core.py`
- `tests/test_watcher_core.py`
- `.pipeline/README.md`
- `docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md`
- `work/4/21/2026-04-21-verified-pending-archive-unblock.md`

## 사용 skill
- `security-gate`: watcher runtime control/state 보강이 destructive write나 operator gate 침범으로 이어지지 않는지 확인했습니다.
- `doc-sync`: current-run `VERIFY_PENDING` replay 계약이 구현과 문서에서 같은 의미가 되도록 좁게 동기화했습니다.
- `finalize-lite`: 변경 파일, 실제 검증, 남은 리스크, closeout 필요성을 점검했습니다.
- `work-log-closeout`: 실행한 사실과 남은 리스크 기준으로 이 `/work` 기록을 남겼습니다.

## 변경 이유
- 최신 work `work/4/21/2026-04-21-stale-advisory-operator-guard.md`는 검증 후보로 떠 있었지만, 예전 current-run `VERIFY_PENDING` job이 이미 matching `/verify`가 있는 상태로 남아 최신 work scan을 계속 가로막고 있었습니다.
- stale pending job을 `VERIFY_DONE`으로 위장하면 manifest 없는 receipt-pending surface가 생길 수 있으므로, 기존 state-archive 경계로 치우는 방식이 더 안전했습니다.

## 핵심 변경
- `watcher_core.py`에 `_archive_matching_verified_pending_jobs(...)`를 추가해 current-run `VERIFY_PENDING` job의 artifact가 이미 matching `/verify`로 닫힌 경우 replay 전에 same-run `state-archive/`로 옮기도록 했습니다.
- `_poll()`의 pending verify replay 직전에 위 helper를 적용해, verified stale pending job이 최신 unverified `/work` 후보 처리를 막지 못하게 했습니다.
- archive 시 stabilizer, verify lease, dedupe state를 함께 정리하고 `stale_verify_pending_archived` raw/runtime event를 남기도록 했습니다.
- `tests/test_watcher_core.py`에 stale pending job archive 후 최신 unverified work job이 step되는 회귀 테스트를 추가했습니다.
- `.pipeline/README.md`와 runtime 기술설계 문서에 current-run pending replay의 예외 조건을 명시했습니다.
- live runtime에서는 watcher source 변경을 supervisor가 감지해 `watcher_self_restart_started/completed` 이벤트를 남기고 PID `654458`로 재시작했으며, 기존 stale job state가 `.pipeline/runs/20260421T114022Z-p577587/state-archive/`로 이동된 것을 확인했습니다.
- 이후 최신 verify job은 wrapper `DISPATCH_SEEN` / `TASK_ACCEPTED`를 받아 `VERIFY_RUNNING`으로 올라갔고, 최종적으로 `VERIFY_DONE`까지 닫힌 것을 확인했습니다.
- verify/handoff owner가 후속으로 `.pipeline/operator_request.md` `CONTROL_SEQ: 712`를 작성했습니다. 이는 이 Codex 라운드가 직접 작성한 control slot이 아니라 live verify/handoff round의 산출물입니다.

## 검증
- `python3 -m py_compile watcher_core.py verify_fsm.py` -> 통과
- `python3 -m unittest tests.test_watcher_core.CurrentRunPendingVerifyTest.test_poll_archives_verified_pending_job_before_latest_unverified_work_scan` -> ERROR. 존재하지 않는 테스트 클래스명으로 호출한 명령 실수입니다.
- `python3 -m unittest tests.test_watcher_core.VerifyCompletionContractTest.test_poll_archives_verified_pending_job_before_latest_unverified_work_scan` -> 통과
- `python3 -m unittest tests.test_watcher_core` -> 176 tests OK
- `python3 -m py_compile watcher_core.py` -> 통과
- `git diff --check -- watcher_core.py tests/test_watcher_core.py .pipeline/README.md docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md` -> 통과
- `git diff --check -- watcher_core.py tests/test_watcher_core.py .pipeline/README.md docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md work/4/21/2026-04-21-verified-pending-archive-unblock.md` -> 통과

## 남은 리스크
- live runtime은 stale pending job starvation에서는 벗어났고 최신 work verify도 `VERIFY_DONE`으로 닫혔습니다.
- 남은 런타임 경계는 verify/handoff owner가 새로 띄운 `commit_push_bundle_authorization` operator stop입니다. 이번 Codex 라운드는 commit, push, operator slot 작성까지 수행하지 않았습니다.
- commit, push, branch/PR publish, 6시간 soak, `/verify` 작성, `.pipeline` control slot 수정은 수행하지 않았습니다.
