# 2026-04-18 watcher startup pending verify replay verification

## 변경 파일
- `verify/4/18/2026-04-18-watcher-startup-pending-verify-replay-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest `/work`인 `work/4/18/2026-04-18-watcher-startup-pending-verify-replay.md`가 watcher startup 복원 경로에서 current-run `VERIFY_PENDING` replay와 stale `slot_verify` lease 정리를 함께 닫았다고 주장하므로, 현재 트리 기준으로 그 closeout이 실제 코드/테스트/문서와 맞는지 다시 확인해야 했습니다.
- same-day `/verify`로 이미 있던 `verify/4/18/2026-04-18-watcher-dispatch-control-mismatch-requery-verification-restored.md`는 더 이른 round를 복구한 artifact라 latest `/work`를 직접 닫는 canonical verify note가 아니었습니다. 따라서 fresh `/verify`를 먼저 남긴 뒤에만 next control을 여는 편이 맞았습니다.

## 핵심 변경
- latest `/work`의 핵심 구현 주장은 현재 코드와 일치했습니다.
  - `watcher_core.py`의 `_poll()`은 current-run `VERIFY_RUNNING` 다음에 current-run `VERIFY_PENDING`를 별도 우선 처리해, 최신 `/work` candidate 스캔 결과와 무관하게 복원된 pending verify round를 다시 `sm.step(...)`으로 재개합니다.
  - `PaneLease`는 lock payload에 `owner_pid`를 저장하고, legacy lock처럼 `owner_pid`가 없을 때도 `supervisor.pid` mtime이 lock `started_at`보다 새로우면 restart 이후 stale lease로 정리합니다.
  - `.pipeline/README.md`도 위 두 경계를 현재 구현 truth로 적고 있습니다.
- latest `/work`가 함께 적은 restored verify artifact도 현재 트리에서 유효했습니다.
  - `verify/4/18/2026-04-18-watcher-dispatch-control-mismatch-requery-verification-restored.md`는 `work/4/18/2026-04-18-watcher-dispatch-control-mismatch-requery.md`를 explicit하게 참조합니다.
  - same-day verify lookup focused regression 2개를 다시 돌렸고, direct day-dir verify note와 matching verify skip 경계가 그대로 통과했습니다.
- latest `/work`의 focused watcher 회귀 주장은 재현됐고, 추가로 full `tests.test_watcher_core`도 현재 트리에서 다시 통과했습니다.
  - 따라서 closeout의 `tests.test_watcher_core` `Ran 125 tests`, `OK` 주장은 current-tree truth로 재확인됐습니다.
- 다만 latest `/work`가 남긴 live risk, 즉 "watcher 로그는 `lease acquired`/`VERIFY_RUNNING`까지 진행했는데 canonical `status.json`은 stale `STOPPED`로 남는다"는 경계는 이번 verify에서 unit/live 재현까지 다시 닫지 않았습니다.
  - 다음 슬라이스는 same-family current-risk reduction으로 이 runtime surface mismatch를 직접 고정하는 편이 맞다고 판단했습니다.

## 검증
- `python3 -m py_compile watcher_core.py tests/test_watcher_core.py`
  - 결과: 통과
- `python3 -m unittest -v tests.test_watcher_core.VerifyCompletionContractTest.test_poll_replays_current_run_verify_pending_even_when_latest_work_is_already_verified tests.test_watcher_core.PaneLeaseOwnerPidWiringTest`
  - 결과: `Ran 8 tests`, `OK`
- `python3 -m unittest -v tests.test_watcher_core.WorkNoteFilteringTest.test_same_day_verify_lookup_accepts_direct_day_dir_note tests.test_watcher_core.WorkNoteFilteringTest.test_latest_verify_candidate_skips_work_with_same_day_matching_verify`
  - 결과: `Ran 2 tests`, `OK`
- `python3 -m unittest -v tests.test_watcher_core 2>&1 | tail -n 5`
  - 결과: `Ran 125 tests`, `OK`
- `git diff --check -- watcher_core.py tests/test_watcher_core.py .pipeline/README.md`
  - 결과: 통과
- live tmux restart/replay와 실제 `status.json` stale snapshot 재현은 이번 verify 라운드에서 다시 실행하지 않았습니다.
  - 이유: latest `/work`의 코드 변화는 watcher unit 범위에서 이미 직접 고정돼 있고, 남은 리스크는 supervisor/runtime surface family의 follow-up slice로 더 좁게 다루는 편이 맞기 때문입니다.

## 남은 리스크
- watcher startup replay와 stale lease 정리는 unit으로 다시 확인됐지만, canonical runtime surface(`.pipeline/runs/<run_id>/status.json`)가 live restart 뒤 current-run verify truth를 즉시 따라오는지는 이번 verify에서 다시 증명하지 않았습니다.
- docs는 이미 supervisor-owned runtime surface를 current truth로 선언하고 있는데, latest `/work`의 live note는 watcher log truth와 status surface truth가 어긋날 수 있음을 보여 줍니다. 이 ownership/runtime sync 경계가 다음 same-family current-risk reduction입니다.
- restored verify artifact는 automation matching을 복구했지만, 사람이 읽는 slug 정렬은 여전히 완전히 예쁘지는 않습니다. 다만 현재 blocker는 human naming보다 runtime truth mismatch 쪽이 더 우선입니다.
