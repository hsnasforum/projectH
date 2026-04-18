# 2026-04-18 watcher supervisor owner death lease release

## 변경 파일
- `watcher_core.py`
- `tests/test_watcher_core.py`
- `.pipeline/README.md`

## 사용 skill
- `work-log-closeout`: `/work` closeout 형식과 필수 사실 항목을 repo 규칙에 맞춰 정리하기 위해 사용했습니다.
- `release-check`: 마무리 단계에서 실제 실행한 검증과 남은 리스크를 과장 없이 정리하기 위해 사용했습니다.

## 변경 이유
- evidence-ranked open-risk 중 가장 강한 family는 "supervisor 비정상 종료 뒤 `slot_verify` lease가 TTL까지 남아 pending handoff/recovery turn을 가리는 문제"였습니다.
- 기존 `PaneLease`는 lock 파일의 started_at/ttl만 보고 active 여부를 판단했고, lease owner인 supervisor가 이미 죽었는지 여부는 보지 않았습니다. 그래서 watcher가 살아남아도 stale lease를 즉시 정리하지 못하고 10~15분 동안 막힐 수 있었습니다.

## 핵심 변경
- `watcher_core.py`의 `PaneLease`에 optional `owner_pid_path`를 추가하고, configured owner pid가 사라졌거나 비어 있거나 `os.kill(pid, 0)` 기준으로 더 이상 살아 있지 않으면 해당 lease lock을 stale로 보고 즉시 삭제하도록 바꿨습니다.
- `WatcherCore`는 startup 시 `.pipeline/supervisor.pid`가 존재하면 그 경로를 `PaneLease` owner로 넘기도록 맞췄습니다. unit/dry-run 테스트처럼 supervisor pid가 없는 환경은 기존 동작을 유지합니다.
- handoff dispatch 경계에서 stale lease가 남아 있으면 TTL 만료를 기다리지 않고 바로 `CLAUDE_ACTIVE` 전환이 열리는 회귀를 `tests/test_watcher_core.py`에 추가했습니다.
- `.pipeline/README.md`에 supervisor pid가 사라진 경우 watcher가 `slot_verify` lease를 stale lock으로 즉시 정리해야 한다는 cleanup 계약을 명시했습니다.

## 검증
- `python3 -m py_compile watcher_core.py tests/test_watcher_core.py`
  - 결과: 통과
- `python3 -m unittest -v tests.test_watcher_core.ClaudeHandoffDispatchTest.test_verify_lease_is_reclaimed_when_supervisor_pid_is_dead tests.test_watcher_core.ClaudeHandoffDispatchTest.test_handoff_update_releases_when_supervisor_pid_is_dead tests.test_watcher_core.ClaudeHandoffDispatchTest.test_handoff_update_waits_until_verify_lease_released`
  - 결과: `Ran 3 tests`, `OK`
- `python3 -m unittest -v tests.test_watcher_core`
  - 결과: `Ran 114 tests`, `OK`
- `git diff --check -- watcher_core.py tests/test_watcher_core.py .pipeline/README.md`
  - 결과: 통과

## 남은 리스크
- 이번 라운드는 stale lease release만 닫았습니다. supervisor 비정상 종료 자체를 watcher/runtime surface에서 어떻게 degrade/stop으로 올릴지까지는 범위를 넓히지 않았습니다.
- owner pid 경계는 startup 시 `.pipeline/supervisor.pid`가 존재하는 supervisor-managed runtime을 전제로 합니다. 다른 수동 watcher 실행 경로에서 같은 cleanup contract를 강제하려면 별도 owner wiring이 더 필요할 수 있습니다.
- screenshot에 있던 나머지 open-risk들(`control_seq` drift, Claude idle timeout 오판, verify 중 artifact hash aliasing, generic `control_mismatch` observability 부족)은 이번 라운드 범위 밖이라 그대로 남아 있습니다.
