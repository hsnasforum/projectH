# 2026-04-18 watcher dispatch control mismatch requery

## 변경 파일
### 이번 라운드 직접 편집 파일
- `watcher_dispatch.py`
- `tests/test_watcher_core.py`
- `.pipeline/README.md`
- `pipeline_runtime/supervisor.py`

### 현재 `git diff HEAD`에 함께 보이는 별도 라운드/기존 dirty worktree
- `watcher_core.py`, `pipeline_runtime/schema.py`, `verify_fsm.py`, `tests/test_pipeline_runtime_schema.py`, `tests/test_pipeline_runtime_supervisor.py` 등은 오늘 다른 watcher/supervisor 라운드 산출물이거나 세션 시작 전부터 있던 dirty worktree입니다.
- 이번 closeout은 위 "직접 편집 파일"만 이번 라운드 범위로 기록합니다.

## 사용 skill
- `doc-sync`: owner-death cleanup 책임 경계와 `flush_pending` observability 계약을 `.pipeline/README.md`와 `pipeline_runtime/supervisor.py` 주석에 현재 구현 truth로 맞추기 위해 사용했습니다.
- `work-log-closeout`: `/work` closeout 형식과 사실 항목을 repo 규칙에 맞춰 남기기 위해 사용했습니다.

## 변경 이유
- owner-death / start-up race 보강 자체는 이미 들어와 있었지만, `watcher_dispatch.py::flush_pending()`은 active control을 루프 시작에서 한 번만 읽고 모든 pending에 재사용하고 있었습니다.
- 이 상태에서는 같은 control family 안에서 `CONTROL_SEQ`만 바뀌어도 뒤쪽 pending이 stale snapshot 기준으로 drop되거나, 반대로 이미 stale인 pending이 늦게 paste될 수 있었습니다.
- 또한 drop 관측성이 raw `"control_mismatch"` 한 덩어리뿐이라 seq drift / file drift / active control 부재를 재현 로그만으로 구분하기 어려웠습니다.

## 핵심 변경
- `watcher_dispatch.py`에서 `flush_pending()`이 pending 항목마다 active control을 다시 읽도록 바꿨습니다. 이제 루프 전체에서 stale control snapshot을 재사용하지 않습니다.
- control mismatch 판정을 `pending_notification_control_mismatch_reason(...)`으로 분리해 `active_control_missing`, `control_file_drift`, `control_status_drift`, `control_seq_drift`를 구분하게 했습니다.
- mismatch drop 시 raw log뿐 아니라 runtime event(`lane_input_deferred_dropped`)에도 structured payload를 남기도록 맞췄습니다. payload에는 `reason_code`, `expected_control_seq`, `active_control_seq`, `expected_prompt_path`, `active_prompt_path`, `expected_status`, `active_status`, `notify_kind`가 들어갑니다.
- `tests/test_watcher_core.py`에 queue 단위 테스트 2개를 추가했습니다.
  - pending 두 개 처리 중 active control이 바뀌면 두 번째 pending은 새 control 기준으로 재판정되는지
  - prompt path는 같고 `CONTROL_SEQ`만 달라진 경우 `control_seq_drift`가 structured payload로 남는지
- 기존 `BusyLaneNotificationDeferTest.test_stale_codex_pending_notification_is_dropped_before_claude_handoff_dispatch`도 강화해서, stale operator pending이 새 Claude handoff 앞에서 `control_file_drift`로 drop되고 structured path/seq 정보가 raw log에 남는지 확인했습니다.
- `.pipeline/README.md`는 owner-death 계약을 현재 코드와 맞췄습니다. `SIGKILL`에서는 supervisor `finally` unlink를 기대하지 않고, stale pid cleanup responsibility는 watcher owner-death 경계가 맡는다고 명시했습니다.
- `pipeline_runtime/supervisor.py`에는 위 책임 분리를 짧은 주석으로 고정했습니다. 정상 종료(SIGTERM/SIGINT)에서만 `finally` unlink를 기대하고, `SIGKILL` stale pid는 watcher cleanup contract 밖에서 해결하지 않는다는 뜻입니다.

## 검증
- `python3 -m py_compile watcher_dispatch.py watcher_core.py pipeline_runtime/supervisor.py tests/test_watcher_core.py`
  - 결과: 통과
- `python3 -m unittest -v tests.test_watcher_core.WatcherDispatchQueueControlMismatchTest`
  - 결과: `Ran 2 tests`, `OK`
- `python3 -m unittest -v tests.test_watcher_core.BusyLaneNotificationDeferTest.test_stale_codex_pending_notification_is_dropped_before_claude_handoff_dispatch`
  - 결과: `Ran 1 test`, `OK`
- `python3 -m unittest -v tests.test_watcher_core`
  - 결과: `Ran 121 tests`, `OK`
- `git diff --check -- watcher_dispatch.py watcher_core.py pipeline_runtime/supervisor.py tests/test_watcher_core.py .pipeline/README.md`
  - 결과: 통과
- launcher live stability gate / tmux replay는 이번 라운드에 실행하지 않았습니다.
  - 이유: 이번 슬라이스는 dispatch queue owner 경계와 structured observability를 코드/단위 회귀로 먼저 닫는 범위였고, 현재 repo에는 같은 라운드에서 바로 재현 가능한 scripted live gate 명령이 고정돼 있지 않았습니다.

## 남은 리스크
- **live tmux gate 미실행**: start-up race와 stale lease release는 unit으로 닫혔지만, 실제 launcher/supervisor/watcher bring-up 순서에서 `handoff_dispatch -> TASK_ACCEPTED -> TASK_DONE -> receipt_close` 체인이 유지되는지는 다음 stability gate에서 다시 확인해야 합니다.
- **stale `supervisor.pid` 파일 자체 정리**: 이번 라운드는 cleanup authority를 watcher owner-death 판정으로 고정했지, `SIGKILL` 뒤 남은 pid 파일을 별도 startup migration으로 치우지는 않았습니다.
- **family #3~#5 잔여**: Claude idle timeout 오판, verify 중 artifact hash rebaseline, generic lane defer 분석 부족은 그대로 남아 있습니다.
- **queue drop observability는 좋아졌지만 root cause는 여전히 family별로 다릅니다**. 재발 시 다음 우선 확인 지점은 새 `reason_code`가 `control_seq_drift`인지 `control_file_drift`인지부터 보는 편이 맞습니다.
