# 2026-04-18 watcher startup pending verify replay

## 변경 파일
- `watcher_core.py`
- `tests/test_watcher_core.py`
- `.pipeline/README.md`
- `verify/4/18/2026-04-18-watcher-dispatch-control-mismatch-requery-verification-restored.md`

## 사용 skill
- `doc-sync`: startup 복원된 `VERIFY_PENDING` round 재개 계약을 `.pipeline/README.md`에 현재 구현 truth로 맞추기 위해 사용했습니다.
- `work-log-closeout`: 이번 round closeout을 repo 규칙 형식으로 남기기 위해 사용했습니다.

## 변경 이유
- restart 뒤에도 watcher가 멈춘 것처럼 보인 직접 원인은 두 겹이었습니다.
- 첫째, same-day `/verify` note 하나가 다른 `/work` 내용을 담도록 재사용되면서 `work/4/18/2026-04-18-watcher-dispatch-control-mismatch-requery.md`가 matching verify를 잃었고, startup이 이 round를 다시 `VERIFY_PENDING`으로 복원했습니다.
- 둘째, `watcher_core._poll()`은 startup에서 state로 복원된 current-run `VERIFY_PENDING` job을 다시 step하지 않고 최신 `/work` candidate 한 개만 스캔하고 있어서, 최신 work가 이미 verify된 경우 older pending round가 `active_round=VERIFY_PENDING`으로만 남고 dispatch starvation에 빠질 수 있었습니다.
- live restart를 다시 확인해 보니 여기서 끝이 아니었습니다. `slot_verify.lock`에는 lease를 잡은 당시 supervisor pid가 남지 않아, supervisor가 재시작된 뒤에도 예전 lease를 current owner의 live lock처럼 착각해 `lease_busy`를 계속 반환하고 있었습니다.

## 핵심 변경
- `watcher_core.py`
  - current-run `VERIFY_RUNNING` 우선 처리 다음에 current-run `VERIFY_PENDING`도 별도로 읽어, 가장 최근 pending round를 먼저 `sm.step(...)`으로 재개하도록 보강했습니다.
  - 이 경로는 최신 `/work` candidate 스캔과 분리되어, startup에서 state로 복원된 pending verify round가 더 최신 verified work 때문에 영구히 굶는 상황을 막습니다.
  - `PaneLease`가 lease를 잡을 때 `owner_pid`를 함께 lock 파일에 기록하도록 바꿨습니다.
  - legacy lock처럼 `owner_pid`가 없는 기존 lock도 current `supervisor.pid`의 mtime이 lock `started_at`보다 더 새로우면 restart 이후 stale lease로 보고 정리하게 했습니다. 이 경로가 없으면 supervisor restart 뒤에도 old lease가 TTL 동안 `lease_busy`로 남습니다.
- `tests/test_watcher_core.py`
  - `test_poll_replays_current_run_verify_pending_even_when_latest_work_is_already_verified`를 추가했습니다.
  - 더 최신 `/work`가 이미 matching `/verify`로 닫혀 있어 candidate가 없어도, state에 남아 있는 current-run pending round는 `_poll()`이 다시 step하는지 고정합니다.
  - `PaneLeaseOwnerPidWiringTest`에 두 케이스를 추가했습니다.
    - lock이 `owner_pid`를 저장하고, 해당 owner가 죽은 뒤 supervisor가 다른 pid로 재시작해도 stale lease가 지워지는지
    - legacy lock처럼 `owner_pid`가 없더라도 supervisor restart(mtime 증가)만으로 stale lease가 정리되는지
- `.pipeline/README.md`
  - watcher startup이 current-run `VERIFY_PENDING` job을 state에서 복원했을 때는 최신 `/work` candidate 유무와 무관하게 그 round를 먼저 재개해야 한다는 계약을 추가했습니다.
  - `slot_verify.lock`이 `owner_pid`를 저장해야 하고, legacy lock도 supervisor restart 후 stale lease로 정리해야 한다는 lease ownership 계약을 추가했습니다.
- `verify/4/18/2026-04-18-watcher-dispatch-control-mismatch-requery-verification-restored.md`
  - explicit `work/...md` 참조가 들어간 restored verify artifact를 추가해, same-day matching `/verify`가 끊겨 old round가 다시 resurrect되는 상태를 복구했습니다.

## 검증
- `python3 -m py_compile watcher_core.py tests/test_watcher_core.py`
  - 결과: 통과
- `python3 -m unittest -v tests.test_watcher_core.VerifyCompletionContractTest.test_poll_replays_current_run_verify_pending_even_when_latest_work_is_already_verified`
  - 결과: `Ran 1 test`, `OK`
- `python3 -m unittest -v tests.test_watcher_core.PaneLeaseOwnerPidWiringTest`
  - 결과: `Ran 7 tests`, `OK`
- `python3 -m py_compile watcher_dispatch.py watcher_core.py pipeline_runtime/supervisor.py tests/test_watcher_core.py`
  - 결과: 통과
- `python3 -m unittest -v tests.test_watcher_core`
  - 결과: `Ran 125 tests`, `OK`

## 남은 리스크
- live tmux watcher 로그에서는 stale `lease_busy`가 사라지고 실제 `lease acquired`/`VERIFY_RUNNING`까지 진행되는 것을 확인했지만, `status.json` surface는 여전히 `STOPPED` stale snapshot으로 남아 있어 supervisor/status writer truth와 watcher log truth가 엇갈리는 follow-up이 남아 있습니다.
- same-day verify 파일명 정리까지 이번 round에서 강제로 하지는 않았습니다. automation은 explicit `work/...md` 참조 기준으로는 복구됐지만, 사람이 볼 때 slug mismatch는 남아 있습니다.
- current-run pending replay를 먼저 재개하도록 한 만큼, 같은 run 안에 여러 pending round가 비정상적으로 쌓였을 때 어떤 round를 우선할지는 여전히 "가장 최근 pending" 기준입니다. 다중 pending backlog 정책을 별도로 정교화한 것은 아닙니다.
